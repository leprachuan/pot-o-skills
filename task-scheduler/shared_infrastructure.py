"""Shared task scheduler infrastructure."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


def parse_schedule_to_next_run(schedule: str) -> Optional[str]:
    """Parse schedule string and return ISO datetime string for next run."""
    schedule = schedule.lower().strip()
    now = datetime.utcnow()

    # Handle "in X minutes/hours/seconds" format
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
                pass

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
                pass

        # Handle "every day at HH:MM" or "every day at HHam/pm"
        if "at" in schedule:
            time_part = schedule.split("at")[1].strip()
            try:
                # Parse "9am" or "14:30" format
                if "am" in time_part or "pm" in time_part:
                    time_obj = datetime.strptime(
                        time_part.replace("am", "").replace("pm", "").strip(), "%I"
                    ).time()
                    if "pm" in time_part and time_obj.hour != 12:
                        time_obj = time_obj.replace(hour=time_obj.hour + 12)
                    elif "am" in time_part and time_obj.hour == 12:
                        time_obj = time_obj.replace(hour=0)
                else:
                    # Try HH:MM format
                    time_obj = datetime.strptime(time_part, "%H:%M").time()

                next_run = now.replace(
                    hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0
                )
                if next_run <= now:
                    next_run += timedelta(days=1)

                return next_run.isoformat() + "Z"
            except (ValueError, AttributeError):
                pass

    return None


class TaskScheduler:
    def __init__(self, config: Optional[Dict] = None):
        self.jobs_file = Path(os.getenv("SCHEDULER_JOBS_FILE", "/opt/.task-scheduler/jobs.json"))
        self.logs_dir = Path(os.getenv("SCHEDULER_LOGS_DIR", "/opt/.task-scheduler/logs/"))
        self.max_retries = int(os.getenv("SCHEDULER_RETRY_MAX", 3))
        
        self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._init_jobs_file()
    
    def _init_jobs_file(self):
        """Initialize jobs.json if it doesn't exist."""
        if not self.jobs_file.exists():
            self.jobs_file.write_text(json.dumps({"jobs": []}, indent=2))
    
    def _load_jobs(self) -> Dict:
        """Load jobs from JSON."""
        return json.loads(self.jobs_file.read_text())
    
    def _save_jobs(self, data: Dict):
        """Save jobs to JSON."""
        self.jobs_file.write_text(json.dumps(data, indent=2))
    
    def schedule_task(self, name: str, schedule: str, agent: str = None, runtime: str = None, task: str = "", notify: bool = False, recurring: bool = True) -> Dict:
        """Create a scheduled task.

        Args:
            name: Task name
            schedule: Schedule string (e.g., "in 2 minutes", "every day at 9am")
            agent: Agent to run (default: from SCHEDULER_DEFAULT_AGENT env var, or "orchestrator")
            runtime: Runtime (default: from SCHEDULER_DEFAULT_RUNTIME env var, or "claude")
            task: Task description/prompt
            notify: Whether to send Telegram notification of results (default: False)
            recurring: Whether job recurs after running (default: True). False = one-time job.
        """
        # Use provided values or fall back to environment variables or hardcoded defaults
        if agent is None:
            agent = os.getenv("SCHEDULER_DEFAULT_AGENT", "orchestrator")
        if runtime is None:
            runtime = os.getenv("SCHEDULER_DEFAULT_RUNTIME", "claude")
        jobs = self._load_jobs()
        job_id = name.lower().replace(" ", "-")

        # Calculate next run time
        next_run = parse_schedule_to_next_run(schedule)

        job = {
            "id": job_id,
            "name": name,
            "agent": agent,
            "runtime": runtime,
            "task": task,
            "schedule": schedule,
            "notify": notify,
            "recurring": recurring,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "next_run": next_run,
            "last_run": None,
            "enabled": True,
            "retries": 0
        }

        jobs["jobs"].append(job)
        self._save_jobs(jobs)
        self._log(job_id, f"Scheduled task: {name} (next run: {next_run}, notify: {notify}, recurring: {recurring})")

        return {"success": True, "result": job, "message": f"Task '{name}' scheduled for {next_run}"}
    
    def list_jobs(self) -> Dict:
        """List all scheduled jobs."""
        jobs = self._load_jobs()
        return {"success": True, "result": jobs["jobs"], "message": f"Found {len(jobs['jobs'])} jobs"}
    
    def pause_job(self, job_id: str) -> Dict:
        """Pause a job."""
        jobs = self._load_jobs()
        for job in jobs["jobs"]:
            if job["id"] == job_id:
                job["enabled"] = False
                self._save_jobs(jobs)
                self._log(job_id, "Job paused")
                return {"success": True, "message": f"Job '{job_id}' paused"}
        return {"success": False, "message": f"Job '{job_id}' not found"}
    
    def resume_job(self, job_id: str) -> Dict:
        """Resume a job."""
        jobs = self._load_jobs()
        for job in jobs["jobs"]:
            if job["id"] == job_id:
                job["enabled"] = True
                self._save_jobs(jobs)
                self._log(job_id, "Job resumed")
                return {"success": True, "message": f"Job '{job_id}' resumed"}
        return {"success": False, "message": f"Job '{job_id}' not found"}
    
    def delete_job(self, job_id: str) -> Dict:
        """Delete a job."""
        jobs = self._load_jobs()
        original_count = len(jobs["jobs"])
        jobs["jobs"] = [j for j in jobs["jobs"] if j["id"] != job_id]
        
        if len(jobs["jobs"]) < original_count:
            self._save_jobs(jobs)
            self._log(job_id, "Job deleted")
            return {"success": True, "message": f"Job '{job_id}' deleted"}
        return {"success": False, "message": f"Job '{job_id}' not found"}
    
    def get_logs(self, job_id: str) -> Dict:
        """Get logs for a job."""
        log_file = self.logs_dir / f"{job_id}.log"
        if log_file.exists():
            return {"success": True, "result": log_file.read_text(), "message": "Logs retrieved"}
        return {"success": False, "message": f"No logs found for job '{job_id}'"}
    
    def _log(self, job_id: str, message: str):
        """Log to job-specific log file."""
        log_file = self.logs_dir / f"{job_id}.log"
        timestamp = datetime.utcnow().isoformat() + "Z"
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def doctor(self) -> Dict:
        """Diagnostic tool."""
        issues = []
        fixes = []
        
        # Check jobs file
        if not self.jobs_file.exists():
            issues.append("Jobs file not found")
            fixes.append(f"Create: {self.jobs_file}")
        
        # Check logs directory
        if not self.logs_dir.exists():
            issues.append("Logs directory not found")
            fixes.append(f"Create: {self.logs_dir}")
        
        # Check permissions
        try:
            test_file = self.logs_dir / ".test"
            test_file.write_text("test")
            test_file.unlink()
        except PermissionError:
            issues.append(f"Cannot write to logs directory: {self.logs_dir}")
            fixes.append(f"Fix permissions: chmod 755 {self.logs_dir}")
        
        # Load and validate jobs
        try:
            jobs = self._load_jobs()
            job_count = len(jobs.get("jobs", []))
        except json.JSONDecodeError:
            issues.append("jobs.json is corrupted")
            fixes.append("Restore from backup or recreate jobs.json")
            job_count = 0
        
        return {
            "success": len(issues) == 0,
            "result": {
                "issues": issues,
                "fixes": fixes,
                "jobs_count": job_count,
                "logs_dir": str(self.logs_dir),
                "jobs_file": str(self.jobs_file)
            },
            "message": "Diagnostics complete"
        }
