"""Background executor daemon for scheduled tasks."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Import TelegramNotifier for direct Telegram notifications (avoid agent_manager overhead)
sys.path.insert(0, '/opt/skills/telegram-notify')
try:
    from shared_infrastructure import TelegramNotifier
except ImportError:
    TelegramNotifier = None

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


class ScheduleParser:
    """Parse natural language schedules into datetime objects."""

    @staticmethod
    def parse_next_run(schedule: str) -> Optional[datetime]:
        """
        Parse schedule string and return next run datetime.

        Supports:
        - "in 5 minutes"
        - "in 1 hour"
        - "every day at 9am"
        - "every day at 14:30"
        - "every hour"
        - "every 30 minutes"
        """
        schedule = schedule.lower().strip()
        now = datetime.utcnow()

        # Handle "in X minutes/hours/seconds" format
        if schedule.startswith("in "):
            parts = schedule[3:].split()
            if len(parts) >= 2:
                try:
                    amount = int(parts[0])
                    unit = parts[1].rstrip('s')  # Remove trailing 's'

                    if unit == "minute":
                        return now + timedelta(minutes=amount)
                    elif unit == "hour":
                        return now + timedelta(hours=amount)
                    elif unit == "second":
                        return now + timedelta(seconds=amount)
                    elif unit == "day":
                        return now + timedelta(days=amount)
                except ValueError:
                    pass

        # Handle "every X minutes/hours/days" format
        if schedule.startswith("every "):
            parts = schedule[6:].split()
            if len(parts) >= 2:
                try:
                    amount = int(parts[0])
                    unit = parts[1].rstrip('s')

                    if unit == "minute":
                        return now + timedelta(minutes=amount)
                    elif unit == "hour":
                        return now + timedelta(hours=amount)
                    elif unit == "day":
                        return now + timedelta(days=amount)
                except ValueError:
                    pass

            # Handle "every day at HH:MM" or "every day at HHam/pm"
            if "at" in schedule:
                time_part = schedule.split("at")[1].strip()
                try:
                    # Parse "9am" or "14:30" format
                    if "am" in time_part or "pm" in time_part:
                        # Simple am/pm parsing
                        time_obj = datetime.strptime(time_part.replace("am", "").replace("pm", "").strip(), "%I").time()
                        if "pm" in time_part and time_obj.hour != 12:
                            time_obj = time_obj.replace(hour=time_obj.hour + 12)
                        elif "am" in time_part and time_obj.hour == 12:
                            time_obj = time_obj.replace(hour=0)
                    else:
                        # Try HH:MM format
                        time_obj = datetime.strptime(time_part, "%H:%M").time()

                    next_run = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    return next_run
                except (ValueError, AttributeError):
                    pass

        logger.warning(f"Could not parse schedule: {schedule}")
        return None


class JobExecutor:
    """Execute scheduled jobs."""

    def __init__(self):
        self.jobs_file = Path("/opt/.task-scheduler/jobs.json")
        self.logs_dir = Path("/opt/.task-scheduler/logs/")
        self.config_file = Path("/opt/agents.json")

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
        """Log job execution."""
        log_file = self.logs_dir / f"{job_id}.log"
        timestamp = datetime.utcnow().isoformat() + "Z"
        try:
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            logger.error(f"Failed to log job {job_id}: {e}")

    def _execute_task(self, job: Dict) -> bool:
        """Execute a single task via agent_manager.py."""
        try:
            job_id = job["id"]
            agent = job.get("agent", "orchestrator")
            runtime = job.get("runtime", "claude")
            task = job.get("task", "")

            # Special handling for send_telegram tasks
            if task.startswith("send_telegram:"):
                message = task.replace("send_telegram:", "").strip()
                return self._send_telegram(message, job_id)

            # For other tasks, delegate to agent_manager.py
            session_id = f"scheduled-{job_id}-{int(time.time())}"
            cmd = [
                "python3",
                "/opt/n8n-copilot-shim/agent_manager.py",
                "--agent", agent,
                "--runtime", runtime,
                "--model", "sonnet" if runtime == "claude" else "gemini-1.5-pro",
                "--config", str(self.config_file),
                task,
                session_id
            ]

            logger.info(f"Executing job {job_id}: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                self._log_job(job_id, f"Task executed successfully. Session: {session_id}")
                return True
            else:
                error_msg = result.stderr or result.stdout
                self._log_job(job_id, f"Task failed with code {result.returncode}: {error_msg}")
                return False

        except subprocess.TimeoutExpired:
            self._log_job(job_id, "Task execution timed out")
            logger.error(f"Job {job_id} execution timed out")
            return False
        except Exception as e:
            self._log_job(job_id, f"Execution error: {str(e)}")
            logger.error(f"Failed to execute job {job_id}: {e}")
            return False

    def _send_telegram(self, message: str, job_id: str) -> bool:
        """Send Telegram notification directly via TelegramNotifier.

        This avoids the overhead of delegating to agent_manager, which was causing
        30-second timeouts. Direct API calls are much faster (typically <1s).
        Resolves: https://github.com/leprachuan/Wee-Orchestrator/issues/10
        """
        try:
            # Use direct TelegramNotifier if available
            if TelegramNotifier:
                logger.info(f"Sending telegram for job {job_id} (direct): {message[:50]}...")
                notifier = TelegramNotifier()
                result = notifier.send_notification(message)

                if result.get("success"):
                    self._log_job(job_id, f"Telegram sent: {message}")
                    return True
                else:
                    error = result.get("message", "Unknown error")
                    self._log_job(job_id, f"Telegram failed: {error}")
                    return False
            else:
                # Fallback: delegate to agent_manager if TelegramNotifier not available
                logger.warning(f"TelegramNotifier not available, falling back to agent_manager")
                cmd = [
                    "python3",
                    "/opt/n8n-copilot-shim/agent_manager.py",
                    "--agent", "orchestrator",
                    "--runtime", "claude",
                    "--model", "sonnet",
                    "--config", str(self.config_file),
                    f"Send a telegram notification with message: {message}",
                    f"telegram-{job_id}-{int(time.time())}"
                ]

                logger.info(f"Sending telegram for job {job_id} (via agent_manager): {message}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    self._log_job(job_id, f"Telegram sent: {message}")
                    return True
                else:
                    error = result.stderr or result.stdout
                    self._log_job(job_id, f"Telegram failed: {error}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send telegram for {job_id}: {e}")
            self._log_job(job_id, f"Telegram error: {str(e)}")
            return False

    def check_and_execute(self):
        """Check for jobs that should run and execute them."""
        data = self._load_jobs()
        now = datetime.utcnow()

        for job in data.get("jobs", []):
            if not job.get("enabled", True):
                continue

            job_id = job["id"]
            next_run_str = job.get("next_run")

            # If next_run is not set, parse schedule to determine it
            if not next_run_str:
                next_run = ScheduleParser.parse_next_run(job.get("schedule", ""))
                if next_run:
                    job["next_run"] = next_run.isoformat() + "Z"
                else:
                    self._log_job(job_id, f"Could not parse schedule: {job.get('schedule')}")
                    continue
            else:
                next_run = datetime.fromisoformat(next_run_str.replace("Z", "+00:00")).replace(tzinfo=None)

            # Check if it's time to execute
            if next_run <= now:
                logger.info(f"Executing job {job_id}")
                success = self._execute_task(job)

                # Update job status
                job["last_run"] = now.isoformat() + "Z"
                job["retries"] = 0

                # Calculate next run
                next_run = ScheduleParser.parse_next_run(job.get("schedule", ""))
                if next_run:
                    job["next_run"] = next_run.isoformat() + "Z"
                    self._log_job(job_id, f"Execution {'succeeded' if success else 'failed'}. Next run: {job['next_run']}")
                else:
                    job["enabled"] = False
                    self._log_job(job_id, "Could not calculate next run, disabling job")

        self._save_jobs(data)


def main():
    """Main executor loop."""
    logger.info("Task scheduler executor started")
    executor = JobExecutor()

    try:
        while True:
            try:
                executor.check_and_execute()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Task scheduler executor stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
