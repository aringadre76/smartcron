import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from smartcron.monitor.system_metrics import SystemMonitor


class TestSystemMonitor(unittest.TestCase):
    
    def setUp(self):
        self.monitor = SystemMonitor()
    
    def test_get_cpu_load(self):
        cpu = self.monitor.get_cpu_load()
        
        self.assertIn("load_1m", cpu)
        self.assertIn("load_5m", cpu)
        self.assertIn("load_15m", cpu)
        self.assertIn("cpu_percent", cpu)
        
        self.assertGreaterEqual(cpu["cpu_percent"], 0)
        self.assertLessEqual(cpu["cpu_percent"], 100)
    
    def test_get_memory_usage(self):
        mem = self.monitor.get_memory_usage()
        
        self.assertIn("total_mb", mem)
        self.assertIn("used_mb", mem)
        self.assertIn("percent", mem)
        
        self.assertGreater(mem["total_mb"], 0)
        self.assertGreaterEqual(mem["percent"], 0)
        self.assertLessEqual(mem["percent"], 100)
    
    def test_get_disk_usage(self):
        disk = self.monitor.get_disk_usage()
        
        self.assertIn("total_gb", disk)
        self.assertIn("free_gb", disk)
        self.assertIn("percent", disk)
        
        self.assertGreater(disk["total_gb"], 0)
    
    def test_get_all_metrics(self):
        metrics = self.monitor.get_all_metrics()
        
        self.assertIn("timestamp", metrics)
        self.assertIn("cpu", metrics)
        self.assertIn("memory", metrics)
        self.assertIn("disk", metrics)
    
    def test_check_constraints(self):
        constraints = {
            "max_cpu": 100,
            "max_memory_percent": 100
        }
        
        result = self.monitor.check_constraints(constraints)
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()

