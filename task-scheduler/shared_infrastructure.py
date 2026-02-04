"""Shared task scheduler infrastructure."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

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
    
    def schedule_task(self, name: str, schedule: str, agent: str, runtime: str, task: str) -> Dict:
        """Create a scheduled task."""
        jobs = self._load_jobs()
        job_id = name.lower().replace(" ", "-")
        
        job = {
            "id": job_id,
            "name": name,
            "agent": agent,
            "runtime": runtime,
            "task": task,
            "schedule": schedule,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "next_run": None,
            "last_run": None,
            "enabled": True,
            "retries": 0
        }
        
        jobs["jobs"].append(job)
        self._save_jobs(jobs)
        self._log(job_id, f"Scheduled task: {name}")
        
        return {"success": True, "result": job, "message": f"Task '{name}' scheduled"}
    
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
        log_file.write_text(f"[{timestamp}] {message}\n", "a")
    
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
