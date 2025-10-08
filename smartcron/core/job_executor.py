import subprocess
import time
import signal
import os
from typing import Dict, Optional, Tuple
from threading import Timer


class JobExecutor:
    
    def __init__(self, logger=None):
        self.logger = logger
        self.running_jobs = {}
    
    def execute_job(self, job_config, system_metrics: Dict) -> Dict[str, any]:
        job_name = job_config.job_name
        command = job_config.command
        timeout = job_config.timeout_sec
        
        if self.logger:
            self.logger.info(f"Starting job: {job_name}")
            self.logger.debug(f"Command: {command}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            end_time = time.time()
            
            execution_result = {
                "job_name": job_name,
                "start_time": start_time,
                "end_time": end_time,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": end_time - start_time,
                "success": result.returncode == 0,
                "timed_out": False
            }
            
            if self.logger:
                status = "SUCCESS" if execution_result["success"] else "FAILED"
                self.logger.info(
                    f"Job {job_name} completed: {status} "
                    f"(exit_code={result.returncode}, duration={execution_result['execution_time']:.2f}s)"
                )
                
                self.logger.log_job_execution(
                    job_name=job_name,
                    start_time=start_time,
                    end_time=end_time,
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    system_state=system_metrics,
                    ai_decision_reason=None
                )
            
            job_config.last_run_time = end_time
            job_config.last_run_success = execution_result["success"]
            
            return execution_result
            
        except subprocess.TimeoutExpired as e:
            end_time = time.time()
            
            execution_result = {
                "job_name": job_name,
                "start_time": start_time,
                "end_time": end_time,
                "exit_code": -1,
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": e.stderr.decode() if e.stderr else "Job timed out",
                "execution_time": end_time - start_time,
                "success": False,
                "timed_out": True
            }
            
            if self.logger:
                self.logger.error(f"Job {job_name} timed out after {timeout}s")
                self.logger.log_job_execution(
                    job_name=job_name,
                    start_time=start_time,
                    end_time=end_time,
                    exit_code=-1,
                    stdout=execution_result["stdout"],
                    stderr=execution_result["stderr"],
                    system_state=system_metrics,
                    ai_decision_reason="Timed out"
                )
            
            job_config.last_run_time = end_time
            job_config.last_run_success = False
            
            return execution_result
            
        except Exception as e:
            end_time = time.time()
            
            execution_result = {
                "job_name": job_name,
                "start_time": start_time,
                "end_time": end_time,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "execution_time": end_time - start_time,
                "success": False,
                "timed_out": False
            }
            
            if self.logger:
                self.logger.error(f"Job {job_name} failed with exception: {e}")
                self.logger.log_job_execution(
                    job_name=job_name,
                    start_time=start_time,
                    end_time=end_time,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    system_state=system_metrics,
                    ai_decision_reason=None
                )
            
            job_config.last_run_time = end_time
            job_config.last_run_success = False
            
            return execution_result
    
    def execute_with_retry(self, job_config, system_metrics: Dict) -> Dict[str, any]:
        max_retries = job_config.max_retries if job_config.retry_on_fail else 0
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                if self.logger:
                    self.logger.info(f"Retrying job {job_config.job_name} (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(60)
            
            result = self.execute_job(job_config, system_metrics)
            
            if result["success"]:
                return result
        
        return result
    
    def execute_sandboxed(self, job_config, system_metrics: Dict, use_systemd: bool = False) -> Dict[str, any]:
        if use_systemd:
            sandboxed_command = f"systemd-run --user --scope --quiet {job_config.command}"
        else:
            sandboxed_command = job_config.command
        
        original_command = job_config.command
        job_config.command = sandboxed_command
        
        result = self.execute_with_retry(job_config, system_metrics)
        
        job_config.command = original_command
        
        return result

