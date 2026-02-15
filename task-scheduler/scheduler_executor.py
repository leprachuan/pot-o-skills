"""
Simplified task scheduler executor daemon.

Runs as a systemd service, checking jobs.json every 1 second.
For each job that's ready to run:
- Executes via agent_manager.py
- Captures results
- Sends to Telegram if notification is enabled
"""

import json
import os
import subprocess
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/opt/.task-scheduler/executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import TelegramNotifier for sending results
sys.path.insert(0, '/opt/skills/telegram-notify')
try:
    from shared_infrastructure import TelegramNotifier
except ImportError:
    TelegramNotifier = None


class TaskSchedulerExecutor:
    """Execute scheduled jobs from jobs.json."""

    def __init__(self):
        self.jobs_file = Path("/opt/.task-scheduler/jobs.json")
        self.logs_dir = Path("/opt/.task-scheduler/logs/")
        self.results_dir = Path("/opt/.task-scheduler/results/")
        self.config_file = Path("/opt/agents.json")

        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def _load_jobs(self) -> Dict:
        """Load jobs from JSON."""
        if not self.jobs_file.exists():
            return {"jobs": []}
        try:
            return json.loads(self.jobs_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            logger.error(f"Failed to load jobs from {self.jobs_file}")
            return {"jobs": []}

    def _save_jobs(self, data: Dict):
        """Save jobs to JSON."""
        try:
            self.jobs_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")

    def _log_job(self, job_id: str, message: str):
        """Log job execution to job-specific log file."""
        log_file = self.logs_dir / f"{job_id}.log"
        timestamp = datetime.utcnow().isoformat() + "Z"
        try:
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            logger.error(f"Failed to log job {job_id}: {e}")

    def _save_result(self, job_id: str, job_name: str, success: bool, output: str = "", error: str = ""):
        """Save full execution result to results database.

        Creates a JSON file with complete execution details for auditing and analysis.
        """
        result_file = self.results_dir / f"{job_id}.jsonl"
        timestamp = datetime.utcnow().isoformat() + "Z"

        result = {
            "timestamp": timestamp,
            "job_id": job_id,
            "job_name": job_name,
            "success": success,
            "output": output[:5000] if output else "",  # Keep first 5000 chars
            "error": error[:5000] if error else "",     # Keep first 5000 chars
        }

        try:
            # Append to JSONL file (one JSON object per line)
            with open(result_file, "a") as f:
                f.write(json.dumps(result) + "\n")
        except Exception as e:
            logger.error(f"Failed to save result for job {job_id}: {e}")

    def _send_telegram(self, message: str, job_id: str) -> bool:
        """Send result via Telegram notification."""
        try:
            if not TelegramNotifier:
                logger.warning("TelegramNotifier not available, skipping notification")
                return False

            notifier = TelegramNotifier()
            result = notifier.send_notification(message)

            if result.get("success"):
                self._log_job(job_id, f"Notification sent to Telegram")
                return True
            else:
                error = result.get("message", "Unknown error")
                logger.error(f"Failed to send Telegram notification: {error}")
                self._log_job(job_id, f"Notification failed: {error}")
                return False
        except Exception as e:
            logger.error(f"Exception sending Telegram: {e}")
            self._log_job(job_id, f"Exception sending notification: {str(e)}")
            return False

    def _execute_task(self, job: Dict) -> Optional[str]:
        """
        Execute a job via agent_manager.py.
        Returns the execution result/output, or None if failed.
        """
        try:
            job_id = job["id"]
            agent = job.get("agent", os.getenv("SCHEDULER_DEFAULT_AGENT", "orchestrator"))
            runtime = job.get("runtime", os.getenv("SCHEDULER_DEFAULT_RUNTIME", "claude"))
            task = job.get("task", "")
            notify = job.get("notify", False)  # Whether to send Telegram notification

            # Create session ID
            session_id = f"scheduled-{job_id}-{int(time.time())}"

            # Build command for agent_manager.py
            cmd = [
                "python3",
                "/opt/n8n-copilot-shim/agent_manager.py",  # Use prod (now has --mode support)
                "--config", str(self.config_file),
                "--agent", agent,
                "--runtime", runtime,
                "--model", "sonnet" if runtime == "claude" else "gemini-1.5-pro",
                "--mode", "yolo",  # Bypass permissions for all scheduled tasks
                task,
                session_id
            ]

            logger.info(f"Executing job {job_id}: {task[:60]}...")
            self._log_job(job_id, f"Starting execution via agent_manager.py")

            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                self._log_job(job_id, f"Execution succeeded")
                self._save_result(job_id, job["name"], success=True, output=output)
                logger.info(f"Job {job_id} completed successfully")

                # Send notification if enabled
                if notify:
                    notification_text = f"✅ *Job Completed*\n\n*Task:* {task[:100]}\n\n*Result:*\n{output[:500]}"
                    self._send_telegram(notification_text, job_id)

                return output
            else:
                error_msg = result.stderr or result.stdout
                self._log_job(job_id, f"Execution failed: {error_msg[:200]}")
                self._save_result(job_id, job["name"], success=False, error=error_msg)
                logger.error(f"Job {job_id} failed with code {result.returncode}")

                # Send error notification if enabled
                if notify:
                    notification_text = f"❌ *Job Failed*\n\n*Task:* {task[:100]}\n\n*Error:*\n{error_msg[:500]}"
                    self._send_telegram(notification_text, job_id)

                return None

        except subprocess.TimeoutExpired:
            self._log_job(job_id, "Execution timed out (5 minutes)")
            self._save_result(job_id, job["name"], success=False, error="Execution timed out (5 minutes)")
            logger.error(f"Job {job_id} execution timed out")

            if job.get("notify"):
                self._send_telegram(
                    f"⏱️ *Job Timeout*\n\n*Task:* {task[:100]}\n\nExecution exceeded 5 minute limit",
                    job_id
                )
            return None

        except Exception as e:
            error_str = str(e)
            self._log_job(job_id, f"Exception: {error_str}")
            self._save_result(job_id, job["name"], success=False, error=error_str)
            logger.error(f"Failed to execute job {job_id}: {e}")

            if job.get("notify"):
                self._send_telegram(
                    f"⚠️ *Job Exception*\n\n*Task:* {task[:100]}\n\n*Error:*\n{error_str[:200]}",
                    job_id
                )
            return None

    def _is_job_ready(self, job: Dict) -> bool:
        """Check if a job is ready to execute (enabled and time has passed)."""
        if not job.get("enabled", True):
            return False

        next_run_str = job.get("next_run")
        if not next_run_str:
            return False

        try:
            next_run = datetime.fromisoformat(next_run_str.replace("Z", "+00:00")).replace(tzinfo=None)
            now = datetime.utcnow()
            return next_run <= now
        except (ValueError, TypeError):
            logger.warning(f"Invalid next_run format: {next_run_str}")
            return False

    def _calculate_next_run(self, schedule: str) -> Optional[str]:
        """Calculate next run time from schedule string."""
        from datetime import timedelta

        schedule = schedule.lower().strip()
        now = datetime.utcnow()

        # Handle "in X minutes/hours/days" format
        if schedule.startswith("in "):
            parts = schedule[3:].split()
            if len(parts) >= 2:
                try:
                    amount = int(parts[0])
                    unit = parts[1].rstrip('s')

                    if unit == "minute":
                        next_run = now + timedelta(minutes=amount)
                    elif unit == "hour":
                        next_run = now + timedelta(hours=amount)
                    elif unit == "second":
                        next_run = now + timedelta(seconds=amount)
                    elif unit == "day":
                        next_run = now + timedelta(days=amount)
                    else:
                        return None

                    return next_run.isoformat() + "Z"
                except ValueError:
                    return None

        # Handle "every X minutes/hours/days" format
        if schedule.startswith("every "):
            parts = schedule[6:].split()
            if len(parts) >= 2:
                try:
                    amount = int(parts[0])
                    unit = parts[1].rstrip('s')

                    if unit == "minute":
                        next_run = now + timedelta(minutes=amount)
                    elif unit == "hour":
                        next_run = now + timedelta(hours=amount)
                    elif unit == "day":
                        next_run = now + timedelta(days=amount)
                    else:
                        return None

                    return next_run.isoformat() + "Z"
                except ValueError:
                    return None

        logger.warning(f"Could not parse schedule: {schedule}")
        return None

    def check_and_execute(self):
        """Check for ready jobs and execute them."""
        data = self._load_jobs()

        for job in data.get("jobs", []):
            if not self._is_job_ready(job):
                continue

            job_id = job["id"]
            logger.info(f"Job ready: {job_id}")

            # Execute the job
            result = self._execute_task(job)

            # Update job record
            now = datetime.utcnow()
            job["last_run"] = now.isoformat() + "Z"

            # Handle recurring vs one-time jobs
            recurring = job.get("recurring", True)  # Default: recurring

            if recurring:
                # Recurring job - calculate next run
                next_run = self._calculate_next_run(job.get("schedule", ""))
                if next_run:
                    job["next_run"] = next_run
                else:
                    # If we can't calculate next run, disable the job
                    job["enabled"] = False
                    self._log_job(job_id, "Could not calculate next run, disabling job")
            else:
                # One-time job - disable after running
                job["enabled"] = False
                self._log_job(job_id, "One-time job completed, disabling")

        self._save_jobs(data)

    def run(self):
        """Main executor loop - runs forever, checking every 1 second."""
        logger.info("Task scheduler executor started")

        try:
            while True:
                try:
                    self.check_and_execute()
                    time.sleep(1)  # Check every 1 second
                except Exception as e:
                    logger.error(f"Error in execution loop: {e}")
                    time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Task scheduler executor stopped")
            sys.exit(0)


def main():
    """Entry point."""
    executor = TaskSchedulerExecutor()
    executor.run()


if __name__ == "__main__":
    main()
