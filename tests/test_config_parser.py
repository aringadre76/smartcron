import unittest
import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from smartcron.config.parser import JobConfigParser, JobConfig


class TestJobConfig(unittest.TestCase):
    
    def test_job_config_creation(self):
        config_dict = {
            "job_name": "test_job",
            "command": "echo 'test'",
            "max_cpu": 50,
            "ai_aware": True
        }
        
        job = JobConfig(config_dict)
        
        self.assertEqual(job.job_name, "test_job")
        self.assertEqual(job.command, "echo 'test'")
        self.assertEqual(job.max_cpu, 50)
        self.assertTrue(job.ai_aware)
        self.assertTrue(job.enabled)
    
    def test_get_constraints(self):
        config_dict = {
            "job_name": "test_job",
            "command": "echo 'test'",
            "max_cpu": 60,
            "min_battery": 30
        }
        
        job = JobConfig(config_dict)
        constraints = job.get_constraints()
        
        self.assertEqual(constraints["max_cpu"], 60)
        self.assertEqual(constraints["min_battery"], 30)
    
    def test_schedule_window(self):
        config_dict = {
            "job_name": "test_job",
            "command": "echo 'test'",
            "schedule_window_start": "00:00",
            "schedule_window_end": "23:59"
        }
        
        job = JobConfig(config_dict)
        result = job.is_in_schedule_window()
        
        self.assertTrue(result)


class TestJobConfigParser(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.parser = JobConfigParser(config_dir=self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_job(self):
        config_dict = {
            "job_name": "backup_job",
            "command": "rsync -av /src /dest",
            "max_cpu": 50,
            "ai_aware": True,
            "enabled": True
        }
        
        job = JobConfig(config_dict)
        job_file = os.path.join(self.temp_dir, "backup_job.yaml")
        
        self.parser.save_job(job, job_file)
        self.assertTrue(os.path.exists(job_file))
        
        loaded_job = self.parser.load_job(job_file)
        self.assertEqual(loaded_job.job_name, "backup_job")
        self.assertEqual(loaded_job.max_cpu, 50)
        self.assertTrue(loaded_job.ai_aware)


if __name__ == "__main__":
    unittest.main()

