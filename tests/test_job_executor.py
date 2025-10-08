import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from smartcron.core.job_executor import JobExecutor
from smartcron.config.parser import JobConfig


class TestJobExecutor(unittest.TestCase):
    
    def setUp(self):
        self.executor = JobExecutor()
    
    def test_execute_simple_command(self):
        config_dict = {
            "job_name": "test_job",
            "command": "echo 'Hello World'",
            "enabled": True
        }
        
        job = JobConfig(config_dict)
        system_metrics = {}
        
        result = self.executor.execute_job(job, system_metrics)
        
        self.assertEqual(result["job_name"], "test_job")
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(result["success"])
        self.assertIn("Hello World", result["stdout"])
    
    def test_execute_failing_command(self):
        config_dict = {
            "job_name": "failing_job",
            "command": "exit 1",
            "enabled": True
        }
        
        job = JobConfig(config_dict)
        system_metrics = {}
        
        result = self.executor.execute_job(job, system_metrics)
        
        self.assertEqual(result["exit_code"], 1)
        self.assertFalse(result["success"])
    
    def test_execute_with_timeout(self):
        config_dict = {
            "job_name": "timeout_job",
            "command": "sleep 10",
            "timeout_sec": 1,
            "enabled": True
        }
        
        job = JobConfig(config_dict)
        system_metrics = {}
        
        result = self.executor.execute_job(job, system_metrics)
        
        self.assertFalse(result["success"])
        self.assertTrue(result["timed_out"])


if __name__ == "__main__":
    unittest.main()

