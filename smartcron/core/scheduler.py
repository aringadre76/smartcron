import time
import signal
import sys
from typing import List, Optional
from pathlib import Path

from smartcron.monitor.system_metrics import SystemMonitor
from smartcron.ai.model import AIPredictor
from smartcron.core.decision import DecisionEngine
from smartcron.core.job_executor import JobExecutor
from smartcron.config.parser import JobConfigParser, JobConfig
from smartcron.utils.logger import SmartCronLogger


class SmartCronScheduler:
    
    def __init__(self, 
                 config_dir: str = "/etc/smartcron/jobs",
                 model_path: str = "models/model.pkl",
                 db_path: str = "/var/lib/smartcron/logs.db",
                 log_dir: str = "/var/log/smartcron",
                 check_interval: int = 60):
        
        self.config_dir = config_dir
        self.check_interval = check_interval
        self.running = False
        
        self.logger = SmartCronLogger(db_path=db_path, log_dir=log_dir)
        self.logger.info("Initializing SmartCron Scheduler")
        
        self.system_monitor = SystemMonitor()
        self.ai_predictor = AIPredictor(model_path=model_path)
        self.decision_engine = DecisionEngine(
            ai_predictor=self.ai_predictor,
            system_monitor=self.system_monitor
        )
        self.job_executor = JobExecutor(logger=self.logger)
        self.job_parser = JobConfigParser(config_dir=config_dir)
        
        self.jobs: List[JobConfig] = []
        self.last_job_load_time = 0
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def load_jobs(self):
        try:
            self.jobs = self.job_parser.load_all_jobs()
            self.last_job_load_time = time.time()
            self.logger.info(f"Loaded {len(self.jobs)} job(s)")
            for job in self.jobs:
                self.logger.debug(f"  - {job.job_name}")
        except Exception as e:
            self.logger.error(f"Error loading jobs: {e}")
    
    def reload_jobs_if_needed(self):
        if time.time() - self.last_job_load_time > 300:
            self.logger.debug("Reloading job configurations...")
            self.load_jobs()
    
    def process_jobs(self):
        self.reload_jobs_if_needed()
        
        ready_deferred = self.decision_engine.get_ready_deferred_jobs()
        jobs_to_check = self.jobs + ready_deferred
        
        if not jobs_to_check:
            return
        
        system_metrics = self.system_monitor.get_all_metrics()
        self.logger.log_system_snapshot(system_metrics)
        
        prioritized = self.decision_engine.prioritize_jobs(jobs_to_check)
        
        for item in prioritized:
            job = item["job"]
            decision = item["decision"]
            
            if decision["should_run"]:
                self.logger.info(f"Running job: {job.job_name} (score={decision['score']:.2f}, reason={decision['reason']})")
                
                result = self.job_executor.execute_with_retry(job, system_metrics)
                
                if not result["success"] and job.retry_on_fail and job.retry_count < job.max_retries:
                    job.retry_count += 1
                    self.decision_engine.add_deferred_job(job, time.time() + 300)
                    self.logger.info(f"Job {job.job_name} will be retried (attempt {job.retry_count}/{job.max_retries})")
                else:
                    job.retry_count = 0
                    self.decision_engine.clear_deferred_job(job.job_name)
                
            elif decision.get("defer_until"):
                self.logger.debug(f"Deferring job: {job.job_name} (reason={decision['reason']})")
                self.decision_engine.add_deferred_job(job, decision["defer_until"])
    
    def run(self):
        self.logger.info("SmartCron Scheduler started")
        self.running = True
        
        self.load_jobs()
        
        while self.running:
            try:
                self.process_jobs()
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                time.sleep(self.check_interval)
        
        self.logger.info("SmartCron Scheduler stopped")
    
    def run_job_now(self, job_name: str) -> bool:
        job = next((j for j in self.jobs if j.job_name == job_name), None)
        if not job:
            self.logger.error(f"Job not found: {job_name}")
            return False
        
        self.logger.info(f"Force running job: {job_name}")
        system_metrics = self.system_monitor.get_all_metrics()
        result = self.job_executor.execute_with_retry(job, system_metrics)
        
        return result["success"]
    
    def get_status(self) -> dict:
        system_metrics = self.system_monitor.get_all_metrics()
        
        job_statuses = []
        for job in self.jobs:
            decision = self.decision_engine.should_run_job(job)
            job_statuses.append({
                "name": job.job_name,
                "enabled": job.enabled,
                "ai_aware": job.ai_aware,
                "last_run": job.last_run_time,
                "last_success": job.last_run_success,
                "decision": decision
            })
        
        return {
            "running": self.running,
            "jobs_loaded": len(self.jobs),
            "system_metrics": system_metrics,
            "jobs": job_statuses,
            "deferred_jobs": len(self.decision_engine.deferred_jobs)
        }


def main():
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="SmartCron AI-Augmented Scheduler")
    parser.add_argument("--config-dir", default="/etc/smartcron/jobs", help="Job configuration directory")
    parser.add_argument("--model", default="models/model.pkl", help="AI model path")
    parser.add_argument("--db", default="/var/lib/smartcron/logs.db", help="Database path")
    parser.add_argument("--log-dir", default="/var/log/smartcron", help="Log directory")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        if args.config_dir == "/etc/smartcron/jobs":
            args.config_dir = "./jobs"
        if args.db == "/var/lib/smartcron/logs.db":
            args.db = "./smartcron_logs.db"
        if args.log_dir == "/var/log/smartcron":
            args.log_dir = "./logs"
    
    scheduler = SmartCronScheduler(
        config_dir=args.config_dir,
        model_path=args.model,
        db_path=args.db,
        log_dir=args.log_dir,
        check_interval=args.interval
    )
    
    scheduler.run()


if __name__ == "__main__":
    main()

