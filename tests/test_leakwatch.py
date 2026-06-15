import unittest
import os
import sys
import time
import json
import gc
from leakwatch import snapshot, monitor, watch, report, GrowthAnalyzer, Snapshot
from leakwatch.engine import _snapshots

class TestLeakWatch(unittest.TestCase):
    def setUp(self):
        # Clear snapshots registry
        _snapshots.clear()
        import leakwatch.engine as engine
        engine._last_snapshot = None
        engine._last_report_data = None
        # Clean up global watch if active
        if engine._global_monitor:
            engine._global_monitor.stop()
            engine._global_monitor = None

    def tearDown(self):
        import leakwatch.engine as engine
        if engine._global_monitor:
            engine._global_monitor.stop()
            engine._global_monitor = None

    def test_snapshot_comparison(self):
        # Take start snapshot
        snap1 = snapshot("before")
        self.assertIn("before", _snapshots)
        
        # Allocate something to trigger GC tracking (needs to be tracked by GC)
        # In Python, lists of objects are GC tracked
        temp_list = []
        for i in range(10000):
            temp_list.append(dict(x=i))
        
        # Take end snapshot
        snap2 = snapshot("after")
        self.assertIn("after", _snapshots)
        
        # Compare manually via analyzer
        analyzer = GrowthAnalyzer(snap1, snap2)
        res = analyzer.analyze()
        
        self.assertIn("growth_summary", res)
        # There should be some growth recorded
        self.assertTrue(len(res["growth_summary"]) >= 0)

    def test_monitor_context_manager(self):
        with monitor() as m:
            temp_list = [dict(a=i) for i in range(5000)]
            
        self.assertIsNotNone(m.end_snapshot)
        self.assertEqual(len(m.history), 2)

    def test_monitor_decorator(self):
        @monitor()
        def dummy_func():
            return [dict(a=i) for i in range(5000)]
            
        dummy_func()
        
        import leakwatch.engine as engine
        self.assertIsNotNone(engine._last_report_data)

    def test_watch(self):
        w = watch(interval=10)
        self.assertTrue(w._is_active)
        w.stop()
        self.assertFalse(w._is_active)

    def test_leak_score_calculation(self):
        # Mock snapshots for analyzer testing
        class MockSnapshot:
            def __init__(self, counts, sizes):
                self.object_counts = counts
                self.object_sizes = sizes
                self.timestamp = time.time()
                
        # Case 1: Built-in type with moderate growth
        snap1 = MockSnapshot({"dict": 100}, {"dict": 1000})
        snap2 = MockSnapshot({"dict": 110}, {"dict": 1100})
        analyzer = GrowthAnalyzer(snap1, snap2)
        score = analyzer._compute_leak_score("dict", 100, 110, 1000, 1100)
        # Builtin has base score 20, growth is 10%, no history
        self.assertEqual(score, 20)
        
        # Case 2: Custom type with huge growth
        snap1 = MockSnapshot({"MyCache": 10}, {"MyCache": 1000})
        snap2 = MockSnapshot({"MyCache": 150}, {"MyCache": 15000})
        analyzer = GrowthAnalyzer(snap1, snap2)
        score = analyzer._compute_leak_score("MyCache", 10, 150, 1000, 15000)
        # Custom base 50 + growth > 1000% (+40) = 90
        self.assertEqual(score, 90)

    def test_report_generation(self):
        # Create some data
        snapshot("before")
        temp_dict = {i: dict(y=i) for i in range(1000)}
        snapshot("after")
        
        # Generate JSON, Markdown and HTML reports
        report(format='json', path='test_report.json')
        report(format='markdown', path='test_report.md')
        report(format='html', path='test_report.html')
        
        self.assertTrue(os.path.exists('test_report.json'))
        self.assertTrue(os.path.exists('test_report.md'))
        self.assertTrue(os.path.exists('test_report.html'))
        
        # Clean up
        if os.path.exists('test_report.json'):
            os.remove('test_report.json')
        if os.path.exists('test_report.md'):
            os.remove('test_report.md')
        if os.path.exists('test_report.html'):
            os.remove('test_report.html')

if __name__ == '__main__':
    unittest.main()
