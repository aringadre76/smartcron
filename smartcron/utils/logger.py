import logging
import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path


class SmartCronLogger:
    
    def __init__(self, db_path: str = "/var/lib/smartcron/logs.db", log_dir: str = "/var/log/smartcron"):
        self.db_path = db_path
        self.log_dir = log_dir
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        
        self._init_db()
        self._setup_file_logging()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                exit_code INTEGER,
                stdout TEXT,
                stderr TEXT,
                execution_time_sec REAL,
                system_state TEXT,
                ai_decision_reason TEXT,
                success BOOLEAN,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                cpu_load REAL,
                memory_percent REAL,
                battery_percent REAL,
                is_charging BOOLEAN,
                idle_time_sec INTEGER,
                metrics_json TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_file_logging(self):
        self.logger = logging.getLogger('smartcron')
        self.logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        main_log_path = os.path.join(self.log_dir, 'smartcron.log')
        fh = logging.FileHandler(main_log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def log_job_execution(self, job_name: str, start_time: float, end_time: float,
                          exit_code: int, stdout: str, stderr: str,
                          system_state: Dict, ai_decision_reason: Optional[str] = None):
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        execution_time = end_time - start_time
        success = exit_code == 0
        
        cursor.execute('''
            INSERT INTO job_executions 
            (job_name, start_time, end_time, exit_code, stdout, stderr, 
             execution_time_sec, system_state, ai_decision_reason, success, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_name,
            start_time,
            end_time,
            exit_code,
            stdout,
            stderr,
            execution_time,
            json.dumps(system_state),
            ai_decision_reason,
            success,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Job '{job_name}' {status} (exit_code={exit_code}, duration={execution_time:.2f}s)")
        
        job_log_path = os.path.join(self.log_dir, f"{job_name}.log")
        with open(job_log_path, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Execution at {datetime.fromtimestamp(start_time).isoformat()}\n")
            f.write(f"Status: {status}\n")
            f.write(f"Exit Code: {exit_code}\n")
            f.write(f"Duration: {execution_time:.2f}s\n")
            if ai_decision_reason:
                f.write(f"AI Decision: {ai_decision_reason}\n")
            f.write(f"\nSTDOUT:\n{stdout}\n")
            if stderr:
                f.write(f"\nSTDERR:\n{stderr}\n")
            f.write(f"{'='*80}\n")
    
    def log_system_snapshot(self, metrics: Dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_snapshots 
            (timestamp, cpu_load, memory_percent, battery_percent, is_charging, idle_time_sec, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.get("timestamp", 0),
            metrics.get("cpu", {}).get("cpu_percent", 0),
            metrics.get("memory", {}).get("percent", 0),
            metrics.get("battery", {}).get("percent") if metrics.get("battery") else None,
            metrics.get("battery", {}).get("is_charging") if metrics.get("battery") else None,
            metrics.get("idle_time_sec"),
            json.dumps(metrics)
        ))
        
        conn.commit()
        conn.close()
    
    def get_job_history(self, job_name: str, limit: int = 100) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM job_executions 
            WHERE job_name = ?
            ORDER BY start_time DESC
            LIMIT ?
        ''', (job_name, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_job_success_rate(self, job_name: str, last_n: int = 10) -> float:
        history = self.get_job_history(job_name, limit=last_n)
        if not history:
            return 1.0
        
        successes = sum(1 for h in history if h['success'])
        return successes / len(history)
    
    def get_average_execution_time(self, job_name: str, last_n: int = 10) -> float:
        history = self.get_job_history(job_name, limit=last_n)
        if not history:
            return 0.0
        
        times = [h['execution_time_sec'] for h in history if h['execution_time_sec']]
        return sum(times) / len(times) if times else 0.0
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def debug(self, message: str):
        self.logger.debug(message)

