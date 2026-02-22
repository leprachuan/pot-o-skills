#!/usr/bin/env python3
"""Task scheduler CLI for Copilot."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_infrastructure import TaskScheduler

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "message": "Action required"}))
        return
    
    action = sys.argv[1]
    scheduler = TaskScheduler()
    
    try:
        if action == "schedule_task":
            name = sys.argv[2]
            schedule = sys.argv[3]
            agent = sys.argv[4]
            runtime = sys.argv[5]
            task = sys.argv[6]
            result = scheduler.schedule_task(name, schedule, agent, runtime, task)
        
        elif action == "list_jobs":
            result = scheduler.list_jobs()
        
        elif action == "pause_job":
            job_id = sys.argv[2]
            result = scheduler.pause_job(job_id)
        
        elif action == "resume_job":
            job_id = sys.argv[2]
            result = scheduler.resume_job(job_id)
        
        elif action == "delete_job":
            job_id = sys.argv[2]
            result = scheduler.delete_job(job_id)
        
        elif action == "get_logs":
            job_id = sys.argv[2]
            result = scheduler.get_logs(job_id)
        
        elif action == "doctor":
            result = scheduler.doctor()
        
        else:
            result = {"success": False, "message": f"Unknown action: {action}"}
        
        print(json.dumps(result))
    
    except Exception as e:
        print(json.dumps({"success": False, "message": str(e)}))

if __name__ == "__main__":
    main()
