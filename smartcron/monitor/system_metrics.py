import os
import time
from typing import Dict, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SystemMonitor:
    
    def __init__(self):
        self.last_check_time = time.time()
    
    def get_cpu_load(self) -> Dict[str, float]:
        load_avg = os.getloadavg()
        
        if HAS_PSUTIL:
            cpu_percent = psutil.cpu_percent(interval=0.1)
        else:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                fields = line.split()
                total = sum(int(x) for x in fields[1:])
                idle = int(fields[4])
                cpu_percent = 100.0 * (1 - idle / total) if total > 0 else 0.0
        
        return {
            "load_1m": load_avg[0],
            "load_5m": load_avg[1],
            "load_15m": load_avg[2],
            "cpu_percent": cpu_percent
        }
    
    def get_memory_usage(self) -> Dict[str, float]:
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            return {
                "total_mb": mem.total / (1024 ** 2),
                "available_mb": mem.available / (1024 ** 2),
                "used_mb": mem.used / (1024 ** 2),
                "percent": mem.percent
            }
        else:
            mem_info = {}
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].rstrip(':')
                        value = int(parts[1])
                        mem_info[key] = value
            
            total_kb = mem_info.get('MemTotal', 0)
            available_kb = mem_info.get('MemAvailable', mem_info.get('MemFree', 0))
            used_kb = total_kb - available_kb
            
            return {
                "total_mb": total_kb / 1024,
                "available_mb": available_kb / 1024,
                "used_mb": used_kb / 1024,
                "percent": 100.0 * used_kb / total_kb if total_kb > 0 else 0.0
            }
    
    def get_battery_status(self) -> Optional[Dict[str, any]]:
        if HAS_PSUTIL:
            battery = psutil.sensors_battery()
            if battery is None:
                return None
            
            return {
                "percent": battery.percent,
                "is_charging": battery.power_plugged,
                "seconds_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1
            }
        else:
            try:
                battery_path = '/sys/class/power_supply/BAT0'
                if not os.path.exists(battery_path):
                    battery_path = '/sys/class/power_supply/BAT1'
                if not os.path.exists(battery_path):
                    return None
                
                with open(f'{battery_path}/capacity', 'r') as f:
                    percent = int(f.read().strip())
                
                with open(f'{battery_path}/status', 'r') as f:
                    status = f.read().strip()
                
                return {
                    "percent": percent,
                    "is_charging": status in ['Charging', 'Full'],
                    "seconds_left": -1
                }
            except:
                return None
    
    def get_disk_usage(self, path: str = '/') -> Dict[str, float]:
        if HAS_PSUTIL:
            disk = psutil.disk_usage(path)
            return {
                "total_gb": disk.total / (1024 ** 3),
                "used_gb": disk.used / (1024 ** 3),
                "free_gb": disk.free / (1024 ** 3),
                "percent": disk.percent
            }
        else:
            stat = os.statvfs(path)
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = total - free
            
            return {
                "total_gb": total / (1024 ** 3),
                "used_gb": used / (1024 ** 3),
                "free_gb": free / (1024 ** 3),
                "percent": 100.0 * used / total if total > 0 else 0.0
            }
    
    def get_user_idle_time(self) -> Optional[int]:
        try:
            import subprocess
            result = subprocess.run(['xprintidle'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return int(result.stdout.strip()) // 1000
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        
        try:
            idle_time = self._get_idle_time_from_proc()
            return idle_time
        except:
            pass
        
        return None
    
    def _get_idle_time_from_proc(self) -> int:
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
            
            import subprocess
            result = subprocess.run(['who', '-s'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                return 0
            
            return int(uptime_seconds)
        except:
            return 0
    
    def get_all_metrics(self) -> Dict[str, any]:
        metrics = {
            "timestamp": time.time(),
            "cpu": self.get_cpu_load(),
            "memory": self.get_memory_usage(),
            "battery": self.get_battery_status(),
            "disk": self.get_disk_usage(),
            "idle_time_sec": self.get_user_idle_time()
        }
        return metrics
    
    def check_constraints(self, constraints: Dict[str, any]) -> bool:
        metrics = self.get_all_metrics()
        
        if "max_cpu" in constraints:
            if metrics["cpu"]["cpu_percent"] > constraints["max_cpu"]:
                return False
        
        if "max_memory_percent" in constraints:
            if metrics["memory"]["percent"] > constraints["max_memory_percent"]:
                return False
        
        if "min_battery" in constraints:
            battery = metrics["battery"]
            if battery and not battery["is_charging"]:
                if battery["percent"] < constraints["min_battery"]:
                    return False
        
        if "min_disk_free_gb" in constraints:
            if metrics["disk"]["free_gb"] < constraints["min_disk_free_gb"]:
                return False
        
        if "min_idle_time_sec" in constraints:
            idle_time = metrics["idle_time_sec"]
            if idle_time is not None and idle_time < constraints["min_idle_time_sec"]:
                return False
        
        return True

