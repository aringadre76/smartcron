from typing import Dict, Optional, List
from datetime import datetime
import time


class DecisionEngine:
    
    def __init__(self, ai_predictor=None, system_monitor=None):
        self.ai_predictor = ai_predictor
        self.system_monitor = system_monitor
        self.pending_jobs = []
        self.deferred_jobs = {}
    
    def should_run_job(self, job_config, force: bool = False) -> Dict[str, any]:
        decision = {
            "should_run": False,
            "reason": "",
            "score": 0.0,
            "defer_until": None
        }
        
        if not job_config.enabled:
            decision["reason"] = "Job is disabled"
            return decision
        
        if force:
            decision["should_run"] = True
            decision["reason"] = "Force run requested"
            decision["score"] = 1.0
            return decision
        
        if not job_config.is_in_schedule_window():
            decision["reason"] = "Outside of schedule window"
            decision["defer_until"] = time.time() + 3600
            return decision
        
        system_metrics = self.system_monitor.get_all_metrics() if self.system_monitor else {}
        
        constraints_met = True
        constraint_failures = []
        
        if self.system_monitor:
            constraints = job_config.get_constraints()
            if constraints:
                constraints_met = self.system_monitor.check_constraints(constraints)
                
                if not constraints_met:
                    metrics = system_metrics
                    if "max_cpu" in constraints and metrics["cpu"]["cpu_percent"] > constraints["max_cpu"]:
                        constraint_failures.append(f"CPU {metrics['cpu']['cpu_percent']:.1f}% > {constraints['max_cpu']}%")
                    
                    if "max_memory_percent" in constraints and metrics["memory"]["percent"] > constraints["max_memory_percent"]:
                        constraint_failures.append(f"RAM {metrics['memory']['percent']:.1f}% > {constraints['max_memory_percent']}%")
                    
                    if "min_battery" in constraints:
                        battery = metrics.get("battery")
                        if battery and not battery["is_charging"] and battery["percent"] < constraints["min_battery"]:
                            constraint_failures.append(f"Battery {battery['percent']:.1f}% < {constraints['min_battery']}%")
        
        if not constraints_met:
            decision["reason"] = f"Constraints not met: {', '.join(constraint_failures)}"
            decision["defer_until"] = time.time() + 300
            return decision
        
        if job_config.ai_aware and self.ai_predictor:
            job_info = {
                "last_job_success": job_config.last_run_success if job_config.last_run_success is not None else True,
                "avg_execution_time": 60
            }
            
            ai_decision = self.ai_predictor.get_decision_score(system_metrics, job_info)
            
            decision["score"] = ai_decision["probability_of_success"]
            decision["reason"] = ai_decision["reason"]
            
            if ai_decision["decision"] == "run_now":
                decision["should_run"] = True
            elif ai_decision["decision"] == "defer":
                decision["defer_until"] = time.time() + 600
            else:
                decision["defer_until"] = time.time() + 1800
        else:
            decision["should_run"] = True
            decision["score"] = 1.0
            decision["reason"] = "Static scheduling: constraints met"
        
        if decision["should_run"] and not job_config.should_run_at_preferred_time():
            if job_config.ai_aware:
                pass
            else:
                decision["should_run"] = False
                decision["reason"] = "Not at preferred time"
                decision["defer_until"] = time.time() + 1800
        
        return decision
    
    def prioritize_jobs(self, jobs: List) -> List:
        scored_jobs = []
        
        for job in jobs:
            decision = self.should_run_job(job)
            if decision["should_run"] or decision["defer_until"]:
                scored_jobs.append({
                    "job": job,
                    "decision": decision,
                    "priority": decision["score"]
                })
        
        scored_jobs.sort(key=lambda x: x["priority"], reverse=True)
        
        return scored_jobs
    
    def add_deferred_job(self, job_config, defer_until: float):
        self.deferred_jobs[job_config.job_name] = {
            "job": job_config,
            "defer_until": defer_until
        }
    
    def get_ready_deferred_jobs(self) -> List:
        ready_jobs = []
        current_time = time.time()
        
        jobs_to_remove = []
        for job_name, deferred in self.deferred_jobs.items():
            if current_time >= deferred["defer_until"]:
                ready_jobs.append(deferred["job"])
                jobs_to_remove.append(job_name)
        
        for job_name in jobs_to_remove:
            del self.deferred_jobs[job_name]
        
        return ready_jobs
    
    def clear_deferred_job(self, job_name: str):
        if job_name in self.deferred_jobs:
            del self.deferred_jobs[job_name]

