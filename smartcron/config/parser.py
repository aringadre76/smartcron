import yaml
import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, time as dt_time

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema not available, skipping validation")


JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "job_name": {"type": "string"},
        "command": {"type": "string"},
        "preferred_time": {
            "type": "array",
            "items": {"type": "string"}
        },
        "max_cpu": {"type": "number"},
        "max_memory_percent": {"type": "number"},
        "min_battery": {"type": "number"},
        "min_disk_free_gb": {"type": "number"},
        "min_idle_time_sec": {"type": "number"},
        "ai_aware": {"type": "boolean"},
        "retry_on_fail": {"type": "boolean"},
        "max_retries": {"type": "integer"},
        "timeout_sec": {"type": "number"},
        "enabled": {"type": "boolean"},
        "schedule_window_start": {"type": "string"},
        "schedule_window_end": {"type": "string"}
    },
    "required": ["job_name", "command"]
}


class JobConfig:
    
    def __init__(self, config_dict: Dict):
        if HAS_JSONSCHEMA:
            jsonschema.validate(config_dict, JOB_SCHEMA)
        
        self.job_name = config_dict["job_name"]
        self.command = config_dict["command"]
        self.preferred_time = config_dict.get("preferred_time", [])
        self.max_cpu = config_dict.get("max_cpu")
        self.max_memory_percent = config_dict.get("max_memory_percent")
        self.min_battery = config_dict.get("min_battery")
        self.min_disk_free_gb = config_dict.get("min_disk_free_gb")
        self.min_idle_time_sec = config_dict.get("min_idle_time_sec")
        self.ai_aware = config_dict.get("ai_aware", False)
        self.retry_on_fail = config_dict.get("retry_on_fail", False)
        self.max_retries = config_dict.get("max_retries", 3)
        self.timeout_sec = config_dict.get("timeout_sec")
        self.enabled = config_dict.get("enabled", True)
        self.schedule_window_start = config_dict.get("schedule_window_start")
        self.schedule_window_end = config_dict.get("schedule_window_end")
        
        self.retry_count = 0
        self.last_run_time = None
        self.last_run_success = None
    
    def get_constraints(self) -> Dict:
        constraints = {}
        if self.max_cpu is not None:
            constraints["max_cpu"] = self.max_cpu
        if self.max_memory_percent is not None:
            constraints["max_memory_percent"] = self.max_memory_percent
        if self.min_battery is not None:
            constraints["min_battery"] = self.min_battery
        if self.min_disk_free_gb is not None:
            constraints["min_disk_free_gb"] = self.min_disk_free_gb
        if self.min_idle_time_sec is not None:
            constraints["min_idle_time_sec"] = self.min_idle_time_sec
        return constraints
    
    def is_in_schedule_window(self) -> bool:
        if not self.schedule_window_start or not self.schedule_window_end:
            return True
        
        now = datetime.now().time()
        
        try:
            start = datetime.strptime(self.schedule_window_start, "%H:%M").time()
            end = datetime.strptime(self.schedule_window_end, "%H:%M").time()
        except ValueError:
            return True
        
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end
    
    def should_run_at_preferred_time(self) -> bool:
        if not self.preferred_time:
            return True
        
        now = datetime.now().strftime("%H:%M")
        current_hour = datetime.now().hour
        
        for pref_time in self.preferred_time:
            try:
                pref_hour = int(pref_time.split(":")[0])
                if abs(current_hour - pref_hour) <= 1:
                    return True
            except (ValueError, IndexError):
                continue
        
        return False
    
    def to_dict(self) -> Dict:
        return {
            "job_name": self.job_name,
            "command": self.command,
            "preferred_time": self.preferred_time,
            "max_cpu": self.max_cpu,
            "max_memory_percent": self.max_memory_percent,
            "min_battery": self.min_battery,
            "ai_aware": self.ai_aware,
            "retry_on_fail": self.retry_on_fail,
            "enabled": self.enabled,
            "last_run_time": self.last_run_time,
            "last_run_success": self.last_run_success
        }


class JobConfigParser:
    
    def __init__(self, config_dir: str = "/etc/smartcron/jobs"):
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
    
    def load_job(self, file_path: str) -> JobConfig:
        with open(file_path, 'r') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                config_dict = yaml.safe_load(f)
            elif file_path.endswith('.json'):
                config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
        
        return JobConfig(config_dict)
    
    def load_all_jobs(self) -> List[JobConfig]:
        jobs = []
        
        if not os.path.exists(self.config_dir):
            return jobs
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith(('.yaml', '.yml', '.json')):
                file_path = os.path.join(self.config_dir, filename)
                try:
                    job = self.load_job(file_path)
                    if job.enabled:
                        jobs.append(job)
                except Exception as e:
                    print(f"Error loading job from {filename}: {e}")
        
        return jobs
    
    def save_job(self, job: JobConfig, file_path: Optional[str] = None):
        if file_path is None:
            file_path = os.path.join(self.config_dir, f"{job.job_name}.yaml")
        
        with open(file_path, 'w') as f:
            yaml.dump(job.to_dict(), f, default_flow_style=False)

