# Task Scheduler - Results Logging & History

## Overview

The task scheduler now keeps a **complete audit log of every job execution** with full results, errors, and metadata.

## How Results Are Stored

Results are stored in **JSONL format** (one JSON object per line) for each job:

- **Location**: `/opt/.task-scheduler/results/{job_id}.jsonl`
- **Format**: JSONL (newline-delimited JSON)
- **Data retained**: 5000 characters per result (sufficient for most cases)

## Result Schema

Each result contains:

```json
{
  "timestamp": "2026-02-15T01:44:15.821425Z",
  "job_id": "results-test-job",
  "job_name": "Results Test Job",
  "success": true,
  "output": "stdout from job execution (up to 5000 chars)",
  "error": "stderr if failed (up to 5000 chars)"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | ISO8601 | When the job executed (UTC) |
| `job_id` | string | Unique job identifier |
| `job_name` | string | Human-readable job name |
| `success` | boolean | true = success, false = error/timeout/exception |
| `output` | string | stdout from agent_manager execution (success only) |
| `error` | string | stderr or error message (failure only) |

## Viewing Results

### Using the view_results.py utility

```bash
# Show all results for a job
python3 /opt/skills/task-scheduler/view_results.py job-id

# Show only the most recent result
python3 /opt/skills/task-scheduler/view_results.py job-id --latest

# Show last 5 results
python3 /opt/skills/task-scheduler/view_results.py job-id --limit 5

# Show only successful runs
python3 /opt/skills/task-scheduler/view_results.py job-id --success

# Show only failed runs
python3 /opt/skills/task-scheduler/view_results.py job-id --errors
```

### Manual inspection

```bash
# View raw JSONL for a job
cat /opt/.task-scheduler/results/job-id.jsonl

# Pretty-print with jq
cat /opt/.task-scheduler/results/job-id.jsonl | jq .

# Count executions
wc -l /opt/.task-scheduler/results/job-id.jsonl

# Get success rate
grep '"success":true' /opt/.task-scheduler/results/job-id.jsonl | wc -l
```

## Example Workflows

### Check if a recurring job is working

```bash
python3 /opt/skills/task-scheduler/view_results.py my-monitor --latest
```

Output:
```
2026-02-15T01:44:34.042399Z | My Monitor | ✅ SUCCESS
  Output: CPU: 45%, Memory: 62%, Disk: 78% - All OK
```

### Find why a job keeps failing

```bash
python3 /opt/skills/task-scheduler/view_results.py my-backup --errors
```

Output:
```
2026-02-15T01:30:00.123456Z | My Backup | ❌ FAILED
  Error: Connection timeout to backup server

2026-02-15T01:31:00.234567Z | My Backup | ❌ FAILED
  Error: Connection timeout to backup server
```

### Get execution statistics

```bash
# Count total runs
wc -l /opt/.task-scheduler/results/my-job.jsonl

# Count successes
grep '"success":true' /opt/.task-scheduler/results/my-job.jsonl | wc -l

# Count failures
grep '"success":false' /opt/.task-scheduler/results/my-job.jsonl | wc -l
```

### Export results for analysis

```bash
# Export to CSV
cat /opt/.task-scheduler/results/my-job.jsonl | \
  jq -r '[.timestamp, .success, (.output // "")[0:50]] | @csv' \
  > results.csv

# Get last 10 as CSV
tail -10 /opt/.task-scheduler/results/my-job.jsonl | \
  jq -r '[.timestamp, .success, (.output // "")[0:50]] | @csv'
```

## Data Retention

- Results are stored **indefinitely** (no automatic cleanup)
- Each job has its own JSONL file (can grow over time)
- For long-running recurring jobs, consider periodic cleanup:

```bash
# Remove old results (keep last 1000 lines)
tail -1000 /opt/.task-scheduler/results/job-id.jsonl > /tmp/recent.jsonl
mv /tmp/recent.jsonl /opt/.task-scheduler/results/job-id.jsonl
```

## What Gets Logged

✅ **Always logged**:
- Execution timestamp
- Job ID and name
- Success/failure status
- Full output or error message
- Timeout errors
- Exceptions

✅ **Separate from results**:
- Execution timestamps in job-specific logs
- Notification sent/failed status
- Job enablement changes

## Use Cases

### Auditing
View complete history of all job runs for compliance/debugging

### Monitoring
Track job success rates and identify patterns

### Troubleshooting
Quickly find when/why jobs failed

### Analytics
Export results for performance analysis or dashboards

### Alerts
Parse results to trigger alerts on repeated failures

### SLA Tracking
Calculate uptime/success metrics for service level agreements

## Integration

Add results logging to any automation:

```python
import json
from pathlib import Path

results_dir = Path("/opt/.task-scheduler/results/")

# Query results
results_file = results_dir / "my-job.jsonl"
with open(results_file) as f:
    results = [json.loads(line) for line in f]
    successful = [r for r in results if r['success']]
    print(f"Success rate: {len(successful)}/{len(results)}")
```

## Files

- **Executor**: `/opt/skills/task-scheduler/scheduler_executor.py`
- **Results storage**: `/opt/.task-scheduler/results/{job_id}.jsonl`
- **View utility**: `/opt/skills/task-scheduler/view_results.py`
- **Job logs**: `/opt/.task-scheduler/logs/{job_id}.log` (metadata only)
