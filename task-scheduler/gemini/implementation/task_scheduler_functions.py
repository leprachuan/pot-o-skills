"""Task scheduler functions for Gemini."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared_infrastructure import TaskScheduler

scheduler = TaskScheduler()

def schedule_task(name: str, schedule: str, agent: str, runtime: str, task: str):
    return scheduler.schedule_task(name, schedule, agent, runtime, task)

def list_jobs():
    return scheduler.list_jobs()

def pause_job(job_id: str):
    return scheduler.pause_job(job_id)

def resume_job(job_id: str):
    return scheduler.resume_job(job_id)

def delete_job(job_id: str):
    return scheduler.delete_job(job_id)

def get_logs(job_id: str):
    return scheduler.get_logs(job_id)

def doctor():
    return scheduler.doctor()
