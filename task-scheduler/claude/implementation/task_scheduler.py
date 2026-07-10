"""Task scheduler implementation for Claude."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared_infrastructure import TaskScheduler

class TaskSchedulerSkill:
    def __init__(self):
        self.scheduler = TaskScheduler()
    
    def schedule_task(self, name: str, schedule: str, agent: str, runtime: str, task: str):
        return self.scheduler.schedule_task(name, schedule, agent, runtime, task)
    
    def list_jobs(self):
        return self.scheduler.list_jobs()
    
    def pause_job(self, job_id: str):
        return self.scheduler.pause_job(job_id)
    
    def resume_job(self, job_id: str):
        return self.scheduler.resume_job(job_id)
    
    def delete_job(self, job_id: str):
        return self.scheduler.delete_job(job_id)
    
    def get_logs(self, job_id: str):
        return self.scheduler.get_logs(job_id)
    
    def doctor(self):
        return self.scheduler.doctor()
