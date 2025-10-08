import argparse
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from smartcron.config.parser import JobConfigParser, JobConfig
from smartcron.utils.logger import SmartCronLogger
from smartcron.monitor.system_metrics import SystemMonitor


def format_bytes(bytes_val):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def cmd_list_jobs(args):
    parser = JobConfigParser(config_dir=args.config_dir)
    jobs = parser.load_all_jobs()
    
    if not jobs:
        print("No jobs configured.")
        return
    
    print(f"\n{'Job Name':<30} {'Enabled':<10} {'AI Aware':<10} {'Last Run':<12}")
    print("-" * 80)
    
    for job in jobs:
        enabled = "Yes" if job.enabled else "No"
        ai_aware = "Yes" if job.ai_aware else "No"
        
        if job.last_run_time:
            import time
            from datetime import datetime
            last_run = datetime.fromtimestamp(job.last_run_time).strftime("%Y-%m-%d %H:%M")
        else:
            last_run = "Never"
        
        print(f"{job.job_name:<30} {enabled:<10} {ai_aware:<10} {last_run:<12}")
    
    print()


def cmd_show_job(args):
    parser = JobConfigParser(config_dir=args.config_dir)
    
    job_file = os.path.join(args.config_dir, f"{args.job_name}.yaml")
    if not os.path.exists(job_file):
        job_file = os.path.join(args.config_dir, f"{args.job_name}.yml")
    if not os.path.exists(job_file):
        job_file = os.path.join(args.config_dir, f"{args.job_name}.json")
    
    if not os.path.exists(job_file):
        print(f"Job '{args.job_name}' not found.")
        return
    
    try:
        job = parser.load_job(job_file)
        
        print(f"\nJob: {job.job_name}")
        print("=" * 60)
        print(f"Command: {job.command}")
        print(f"Enabled: {job.enabled}")
        print(f"AI Aware: {job.ai_aware}")
        print(f"Retry on Fail: {job.retry_on_fail}")
        
        if job.preferred_time:
            print(f"Preferred Times: {', '.join(job.preferred_time)}")
        
        constraints = job.get_constraints()
        if constraints:
            print("\nConstraints:")
            for key, value in constraints.items():
                print(f"  - {key}: {value}")
        
        if job.last_run_time:
            from datetime import datetime
            last_run = datetime.fromtimestamp(job.last_run_time).strftime("%Y-%m-%d %H:%M:%S")
            status = "SUCCESS" if job.last_run_success else "FAILED"
            print(f"\nLast Run: {last_run} ({status})")
        
        print()
        
    except Exception as e:
        print(f"Error loading job: {e}")


def cmd_system_status(args):
    monitor = SystemMonitor()
    metrics = monitor.get_all_metrics()
    
    print("\nSystem Status")
    print("=" * 60)
    
    cpu = metrics["cpu"]
    print(f"\nCPU:")
    print(f"  Load Average: {cpu['load_1m']:.2f}, {cpu['load_5m']:.2f}, {cpu['load_15m']:.2f}")
    print(f"  CPU Usage: {cpu['cpu_percent']:.1f}%")
    
    mem = metrics["memory"]
    print(f"\nMemory:")
    print(f"  Total: {mem['total_mb']:.0f} MB")
    print(f"  Used: {mem['used_mb']:.0f} MB ({mem['percent']:.1f}%)")
    print(f"  Available: {mem['available_mb']:.0f} MB")
    
    if metrics["battery"]:
        battery = metrics["battery"]
        charging = "Charging" if battery["is_charging"] else "Not Charging"
        print(f"\nBattery:")
        print(f"  Level: {battery['percent']:.1f}%")
        print(f"  Status: {charging}")
        if battery["seconds_left"] > 0:
            hours = battery["seconds_left"] // 3600
            minutes = (battery["seconds_left"] % 3600) // 60
            print(f"  Time Left: {hours}h {minutes}m")
    
    disk = metrics["disk"]
    print(f"\nDisk (/):")
    print(f"  Total: {disk['total_gb']:.1f} GB")
    print(f"  Used: {disk['used_gb']:.1f} GB ({disk['percent']:.1f}%)")
    print(f"  Free: {disk['free_gb']:.1f} GB")
    
    if metrics["idle_time_sec"] is not None:
        idle_minutes = metrics["idle_time_sec"] // 60
        print(f"\nUser Idle Time: {idle_minutes} minutes")
    
    print()


def cmd_job_history(args):
    logger = SmartCronLogger(db_path=args.db)
    history = logger.get_job_history(args.job_name, limit=args.limit)
    
    if not history:
        print(f"No execution history found for job '{args.job_name}'.")
        return
    
    print(f"\nExecution History for: {args.job_name}")
    print("=" * 80)
    
    for entry in history:
        from datetime import datetime
        start_time = datetime.fromtimestamp(entry['start_time']).strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if entry['success'] else "FAILED"
        duration = entry['execution_time_sec']
        
        print(f"\n[{start_time}] {status} (Exit Code: {entry['exit_code']}, Duration: {duration:.2f}s)")
        
        if args.verbose:
            if entry['stdout']:
                print(f"  STDOUT: {entry['stdout'][:200]}")
            if entry['stderr']:
                print(f"  STDERR: {entry['stderr'][:200]}")
    
    print()
    
    success_rate = logger.get_job_success_rate(args.job_name, last_n=args.limit)
    avg_time = logger.get_average_execution_time(args.job_name, last_n=args.limit)
    
    print(f"Success Rate (last {args.limit}): {success_rate:.1%}")
    print(f"Average Execution Time: {avg_time:.2f}s")
    print()


def cmd_enable_job(args):
    parser = JobConfigParser(config_dir=args.config_dir)
    
    job_file = os.path.join(args.config_dir, f"{args.job_name}.yaml")
    if not os.path.exists(job_file):
        job_file = os.path.join(args.config_dir, f"{args.job_name}.yml")
    if not os.path.exists(job_file):
        job_file = os.path.join(args.config_dir, f"{args.job_name}.json")
    
    if not os.path.exists(job_file):
        print(f"Job '{args.job_name}' not found.")
        return
    
    try:
        job = parser.load_job(job_file)
        job.enabled = True
        parser.save_job(job, job_file)
        print(f"Job '{args.job_name}' enabled.")
    except Exception as e:
        print(f"Error enabling job: {e}")


def cmd_disable_job(args):
    parser = JobConfigParser(config_dir=args.config_dir)
    
    job_file = os.path.join(args.config_dir, f"{args.job_name}.yaml")
    if not os.path.exists(job_file):
        job_file = os.path.join(args.config_dir, f"{args.job_name}.yml")
    if not os.path.exists(job_file):
        job_file = os.path.join(args.config_dir, f"{args.job_name}.json")
    
    if not os.path.exists(job_file):
        print(f"Job '{args.job_name}' not found.")
        return
    
    try:
        job = parser.load_job(job_file)
        job.enabled = False
        parser.save_job(job, job_file)
        print(f"Job '{args.job_name}' disabled.")
    except Exception as e:
        print(f"Error disabling job: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="SmartCron Control CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--config-dir", default="/etc/smartcron/jobs", help="Job configuration directory")
    parser.add_argument("--db", default="/var/lib/smartcron/logs.db", help="Database path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("list", help="List all configured jobs")
    
    show_parser = subparsers.add_parser("show", help="Show details of a specific job")
    show_parser.add_argument("job_name", help="Name of the job")
    
    subparsers.add_parser("status", help="Show system status")
    
    history_parser = subparsers.add_parser("history", help="Show job execution history")
    history_parser.add_argument("job_name", help="Name of the job")
    history_parser.add_argument("--limit", type=int, default=10, help="Number of records to show")
    history_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    
    enable_parser = subparsers.add_parser("enable", help="Enable a job")
    enable_parser.add_argument("job_name", help="Name of the job")
    
    disable_parser = subparsers.add_parser("disable", help="Disable a job")
    disable_parser.add_argument("job_name", help="Name of the job")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        if args.config_dir == "/etc/smartcron/jobs":
            args.config_dir = "./jobs"
        if args.db == "/var/lib/smartcron/logs.db":
            args.db = "./smartcron_logs.db"
    
    if not args.command:
        parser.print_help()
        return
    
    command_map = {
        "list": cmd_list_jobs,
        "show": cmd_show_job,
        "status": cmd_system_status,
        "history": cmd_job_history,
        "enable": cmd_enable_job,
        "disable": cmd_disable_job
    }
    
    if args.command in command_map:
        command_map[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

