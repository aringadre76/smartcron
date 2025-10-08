import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from smartcron.core.decision import DecisionEngine
from smartcron.config.parser import JobConfig


class TestDecisionEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = DecisionEngine()
    
    def test_disabled_job(self):
        config_dict = {
            "job_name": "test_job",
            "command": "echo 'test'",
            "enabled": False
        }
        
        job = JobConfig(config_dict)
        decision = self.engine.should_run_job(job)
        
        self.assertFalse(decision["should_run"])
        self.assertIn("disabled", decision["reason"].lower())
    
    def test_force_run(self):
        config_dict = {
            "job_name": "test_job",
            "command": "echo 'test'",
            "enabled": True
        }
        
        job = JobConfig(config_dict)
        decision = self.engine.should_run_job(job, force=True)
        
        self.assertTrue(decision["should_run"])
        self.assertIn("Force", decision["reason"])
    
    def test_prioritize_jobs(self):
        jobs = []
        for i in range(3):
            config_dict = {
                "job_name": f"job_{i}",
                "command": "echo 'test'",
                "enabled": True
            }
            jobs.append(JobConfig(config_dict))
        
        prioritized = self.engine.prioritize_jobs(jobs)
        
        self.assertIsInstance(prioritized, list)
        for item in prioritized:
            self.assertIn("job", item)
            self.assertIn("decision", item)


if __name__ == "__main__":
    unittest.main()

