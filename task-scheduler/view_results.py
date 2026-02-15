#!/usr/bin/env python3
"""
Utility to view and query job execution results.

Usage:
    python3 view_results.py                              # Show all recent results
    python3 view_results.py job-id                       # Show all results for a job
    python3 view_results.py job-id --limit 5             # Show last 5 results for a job
    python3 view_results.py job-id --success             # Show only successful runs
    python3 view_results.py job-id --errors              # Show only failed runs
    python3 view_results.py job-id --latest              # Show most recent result
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def load_results(job_id):
    """Load all results for a job from JSONL file."""
    results_file = Path(f"/opt/.task-scheduler/results/{job_id}.jsonl")
    if not results_file.exists():
        return []

    results = []
    try:
        with open(results_file) as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
    except Exception as e:
        print(f"Error reading results: {e}")
        return []

    return results


def format_result(result, show_output=True):
    """Format a result for display."""
    timestamp = result.get("timestamp", "")
    job_name = result.get("job_name", "")
    success = result.get("success", False)
    output = result.get("output", "")
    error = result.get("error", "")

    status = "✅ SUCCESS" if success else "❌ FAILED"

    output_str = ""
    if show_output:
        if success and output:
            output_str = f"\n  Output: {output[:200]}{'...' if len(output) > 200 else ''}"
        elif error:
            output_str = f"\n  Error: {error[:200]}{'...' if len(error) > 200 else ''}"

    return f"{timestamp} | {job_name} | {status}{output_str}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 view_results.py <job-id> [--latest|--success|--errors|--limit N]")
        print("\nExample:")
        print("  python3 view_results.py my-job                    # Show all results")
        print("  python3 view_results.py my-job --latest           # Show last result")
        print("  python3 view_results.py my-job --success          # Show successful runs")
        print("  python3 view_results.py my-job --errors           # Show failed runs")
        print("  python3 view_results.py my-job --limit 5          # Show last 5 results")
        return

    job_id = sys.argv[1]
    filters = sys.argv[2:] if len(sys.argv) > 2 else []

    # Load results
    results = load_results(job_id)

    if not results:
        print(f"No results found for job: {job_id}")
        return

    # Apply filters
    if "--success" in filters:
        results = [r for r in results if r.get("success")]
    elif "--errors" in filters:
        results = [r for r in results if not r.get("success")]

    if "--latest" in filters:
        results = results[-1:]

    # Apply limit
    limit_idx = next((i for i, f in enumerate(filters) if f == "--limit"), None)
    if limit_idx is not None and limit_idx + 1 < len(filters):
        try:
            limit = int(filters[limit_idx + 1])
            results = results[-limit:]
        except ValueError:
            pass

    # Display results
    print(f"\n📋 Results for job: {job_id} (showing {len(results)} of {len(load_results(job_id))} total)")
    print("=" * 100)

    for result in results:
        print(format_result(result, show_output=True))

    # Summary stats
    print("\n" + "=" * 100)
    all_results = load_results(job_id)
    successful = sum(1 for r in all_results if r.get("success"))
    failed = len(all_results) - successful
    print(f"Summary: {successful} successful, {failed} failed (total: {len(all_results)})")

    if all_results:
        first_run = all_results[0].get("timestamp", "")
        last_run = all_results[-1].get("timestamp", "")
        print(f"First run: {first_run}")
        print(f"Last run: {last_run}")


if __name__ == "__main__":
    main()
