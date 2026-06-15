import os
import sys
import gc
import tracemalloc
import time
import threading
from collections import Counter

try:
    import psutil
    _has_psutil = True
except ImportError:
    _has_psutil = False

# Global registries
_snapshots = {}
_last_snapshot = None
_last_report_data = None
_global_monitor = None

def get_process_rss():
    if _has_psutil:
        try:
            return psutil.Process(os.getpid()).memory_info().rss
        except Exception:
            pass
    return 0

def format_bytes(b):
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.1f} MB"
    elif b >= 1024:
        return f"{b / 1024:.1f} KB"
    else:
        return f"{b} B"

class Snapshot:
    def __init__(self, name):
        self.name = name
        self.timestamp = time.time()
        self.rss = get_process_rss()
        
        # Ensure tracemalloc is active to capture snapshots
        if not tracemalloc.is_tracing():
            tracemalloc.start(25)
            
        self.tm_snapshot = tracemalloc.take_snapshot()
        self.object_counts, self.object_sizes = self._get_objects_info()

    def _get_objects_info(self):
        counts = Counter()
        sizes = Counter()
        for obj in gc.get_objects():
            try:
                name = type(obj).__name__
                counts[name] += 1
                sizes[name] += sys.getsizeof(obj)
            except Exception:
                pass
        return counts, sizes

def snapshot(name):
    global _last_snapshot, _snapshots
    current = Snapshot(name)
    _snapshots[name] = current
    
    if _last_snapshot is not None:
        # Calculate growth summary and print
        diff_sizes = {}
        all_types = set(_last_snapshot.object_sizes.keys()) | set(current.object_sizes.keys())
        for t in all_types:
            s1 = _last_snapshot.object_sizes.get(t, 0)
            s2 = current.object_sizes.get(t, 0)
            if s2 > s1:
                diff_sizes[t] = s2 - s1
                
        print("\nMemory Growth Summary\n")
        sorted_growth = sorted(diff_sizes.items(), key=lambda x: x[1], reverse=True)
        for t_name, size in sorted_growth[:10]:
            if size > 0:
                print(f"{t_name:<13} +{format_bytes(size)}")
        print()
        
    _last_snapshot = current
    return current

class GrowthAnalyzer:
    def __init__(self, start_snap, end_snap, history=None):
        self.start_snap = start_snap
        self.end_snap = end_snap
        self.history = history or []

    def analyze(self):
        growth_summary = []
        leaks = []
        
        all_types = set(self.start_snap.object_counts.keys()) | set(self.end_snap.object_counts.keys())
        
        for t in all_types:
            c1 = self.start_snap.object_counts.get(t, 0)
            c2 = self.end_snap.object_counts.get(t, 0)
            s1 = self.start_snap.object_sizes.get(t, 0)
            s2 = self.end_snap.object_sizes.get(t, 0)
            
            growth_bytes = s2 - s1
            growth_count = c2 - c1
            
            if growth_bytes <= 0 and growth_count <= 0:
                continue
                
            growth_percent = 0.0
            if c1 > 0:
                growth_percent = (growth_count / c1) * 100
            elif growth_count > 0:
                growth_percent = 100.0
                
            leak_score = self._compute_leak_score(t, c1, c2, s1, s2)
            
            growth_summary.append({
                "type": t,
                "growth_bytes": growth_bytes,
                "start_count": c1,
                "end_count": c2,
                "growth_percent": growth_percent,
                "leak_score": leak_score
            })
            
            if leak_score >= 50:
                created_at = self._get_creation_sources(t)
                leaks.append({
                    "type": t,
                    "start_count": c1,
                    "end_count": c2,
                    "growth_percent": growth_percent,
                    "leak_score": leak_score,
                    "created_at": created_at
                })
                
        growth_summary.sort(key=lambda x: x["growth_bytes"], reverse=True)
        leaks.sort(key=lambda x: x["leak_score"], reverse=True)
        
        runtime = self.end_snap.timestamp - self.start_snap.timestamp
        
        return {
            "start_time": self.start_snap.timestamp,
            "end_time": self.end_snap.timestamp,
            "runtime_seconds": runtime,
            "growth_summary": growth_summary,
            "leaks": leaks
        }

    def _compute_leak_score(self, type_name, c1, c2, s1, s2):
        is_builtin = type_name in ('dict', 'list', 'set', 'tuple', 'str', 'bytes', 'int', 'float', 'frame', 'code', 'function', 'cell')
        score = 20 if is_builtin else 50
        
        growth_count = c2 - c1
        if c1 > 0:
            growth_percent = (growth_count / c1) * 100
        else:
            growth_percent = 100.0 if growth_count > 0 else 0.0
            
        if growth_percent > 1000:
            score += 40
        elif growth_percent > 500:
            score += 30
        elif growth_percent > 100:
            score += 20
        elif growth_percent > 50:
            score += 10
            
        if len(self.history) >= 3:
            monotonic = True
            prev_val = None
            for snap in self.history:
                val = snap.object_counts.get(type_name, 0)
                if prev_val is not None and val < prev_val:
                    monotonic = False
                    break
                prev_val = val
            if monotonic and growth_count > 0:
                score += 20
                
        return min(max(score, 0), 98)

    def _get_creation_sources(self, class_name, limit=2):
        sources = Counter()
        for obj in gc.get_objects():
            try:
                if type(obj).__name__ == class_name:
                    tb = tracemalloc.get_object_traceback(obj)
                    if tb:
                        for frame in tb:
                            if 'leakwatch' not in frame.filename and 'importlib' not in frame.filename:
                                sources[(frame.filename, frame.lineno)] += 1
                                break
            except Exception:
                pass
                
        results = []
        for (fn, line), _ in sources.most_common(limit):
            try:
                rel_path = os.path.relpath(fn)
                if rel_path.startswith('..') or os.path.isabs(rel_path):
                    rel_path = os.path.basename(fn)
            except Exception:
                rel_path = os.path.basename(fn)
            results.append(f"{rel_path}:{line}")
        return results

class monitor:
    def __init__(self, interval=5):
        self.interval = interval
        self.start_snapshot = None
        self.end_snapshot = None
        self.history = []
        self._is_active = False
        self._stop_event = threading.Event()
        self._thread = None
        
        # Start immediately when instantiated (e.g. from monitor() call)
        self.start()

    def start(self):
        if self._is_active:
            return
        self._is_active = True
        if not tracemalloc.is_tracing():
            tracemalloc.start(25)
        self.start_snapshot = Snapshot("start")
        self.history.append(self.start_snapshot)
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        # Register atexit handler to ensure we report on exit if not manually stopped
        import atexit
        def exit_handler():
            if self._is_active:
                report_data = self.stop()
                print("\n" + "="*50)
                print("LeakWatch Final Report")
                print("="*50)
                from .reporter import ConsoleReporter
                ConsoleReporter(report_data).report()
        atexit.register(exit_handler)

    def stop(self):
        if not self._is_active:
            return None
        self._is_active = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            
        self.end_snapshot = Snapshot("end")
        self.history.append(self.end_snapshot)
        
        analyzer = GrowthAnalyzer(self.start_snapshot, self.end_snapshot, self.history)
        report_data = analyzer.analyze()
        
        global _last_report_data
        _last_report_data = report_data
        
        return report_data

    def _monitor_loop(self):
        alerted_types = set()
        while not self._stop_event.is_set():
            elapsed = 0.0
            while elapsed < self.interval:
                if self._stop_event.is_set():
                    return
                time.sleep(0.1)
                elapsed += 0.1
                
            current_snap = Snapshot(f"check_{len(self.history)}")
            self.history.append(current_snap)
            
            analyzer = GrowthAnalyzer(self.start_snapshot, current_snap, self.history)
            report_data = analyzer.analyze()
            
            for item in report_data["growth_summary"]:
                t_name = item["type"]
                if item["leak_score"] >= 75 and item["growth_percent"] >= 50 and t_name not in alerted_types:
                    alerted_types.add(t_name)
                    print(f"\nPotential Leak Detected\n")
                    print(f"Object:")
                    print(f"{t_name}\n")
                    print(f"Instances:")
                    print(f"{item['start_count']:,} -> {item['end_count']:,}\n")
                    print(f"Growth:")
                    print(f"{item['growth_percent']:.0f}%\n")
                    
    def __enter__(self):
        # Already started in __init__, return self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        report_data = self.stop()
        if report_data:
            from .reporter import ConsoleReporter
            ConsoleReporter(report_data).report()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper

def watch(interval=10):
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = monitor(interval=interval)
    return _global_monitor

def report(format='console', path=None):
    global _last_report_data
    report_data = _last_report_data
    
    if report_data is None:
        # Fallback: check if we have manually captured snapshots
        snaps = sorted(_snapshots.values(), key=lambda x: x.timestamp)
        if len(snaps) >= 2:
            analyzer = GrowthAnalyzer(snaps[0], snaps[-1], snaps)
            report_data = analyzer.analyze()
        else:
            print("No monitoring data or snapshots available to generate a report.")
            return
            
    if format == 'console':
        from .reporter import ConsoleReporter
        ConsoleReporter(report_data).report(path)
    elif format == 'json':
        from .reporter import JSONReporter
        JSONReporter(report_data).report(path)
    elif format == 'markdown':
        from .reporter import MarkdownReporter
        MarkdownReporter(report_data).report(path)
    elif format == 'html':
        from .reporter import HTMLReporter
        HTMLReporter(report_data).report(path)
