import argparse
import sys
import os
import json
import time
from .engine import monitor

def main():
    parser = argparse.ArgumentParser(description="LeakWatch Command Line Interface")
    subparsers = parser.add_subparsers(dest="command")
    
    # Run subparser
    run_parser = subparsers.add_parser("run", help="Run a Python script with memory monitoring")
    run_parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Python command/script and its arguments")
    
    # Report subparser
    report_parser = subparsers.add_parser("report", help="Generate report from the last monitoring session")
    report_parser.add_argument("--html", action="store_true", help="Generate HTML report")
    report_parser.add_argument("--json", action="store_true", help="Generate JSON report")
    report_parser.add_argument("--markdown", action="store_true", help="Generate Markdown report")
    report_parser.add_argument("--file", type=str, help="Output file path (optional)")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_command(args.script_args)
    elif args.command == "report":
        report_command(args)
    else:
        parser.print_help()

def format_runtime(seconds):
    if seconds >= 3600:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"
    elif seconds >= 60:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}m {s}s"
    else:
        return f"{seconds:.1f}s"

def run_command(script_args):
    if not script_args:
        print("Error: No script specified to run.")
        sys.exit(1)
        
    script_idx = 0
    if script_args[0] in ("python", "python3"):
        script_idx = 1
        
    if script_idx >= len(script_args):
        print("Error: No script specified to run.")
        sys.exit(1)
        
    script_path = script_args[script_idx]
    
    if not os.path.exists(script_path):
        print(f"Error: Script not found at '{script_path}'")
        sys.exit(1)
        
    # Reconstruct sys.argv for the script
    original_argv = list(sys.argv)
    original_path = list(sys.path)
    
    sys.argv = script_args[script_idx:]
    
    script_dir = os.path.abspath(os.path.dirname(script_path))
    sys.path.insert(0, script_dir)
    
    print("Monitoring Started...\n")
    start_time = time.time()
    
    # We want monitor to not print the exit report to console since we are running in run mode
    # Let's adjust monitor so it saves report data but doesn't print if print_report=False
    # To do that, let's keep monitor subclass or just disable exit_handler print
    m = monitor(interval=5)
    
    try:
        import runpy
        runpy.run_path(script_path, run_name="__main__")
    except SystemExit:
        pass
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        report_data = m.stop()
        runtime = time.time() - start_time
        
        # Save report data to .leakwatch_report.json so 'report' command can read it
        try:
            with open('.leakwatch_report.json', 'w') as f:
                json.dump(report_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save .leakwatch_report.json: {e}")
            
        print(f"Runtime: {format_runtime(runtime)}")
        print(f"\nPotential Leaks Found: {len(report_data.get('leaks', []))}")
        
        # Restore sys.argv and sys.path
        sys.argv = original_argv
        sys.path = original_path

def report_command(args):
    if not os.path.exists('.leakwatch_report.json'):
        print("Error: No session file '.leakwatch_report.json' found. Run 'leakwatch run ...' first.")
        sys.exit(1)
        
    try:
        with open('.leakwatch_report.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to read session file: {e}")
        sys.exit(1)
        
    from .reporter import ConsoleReporter, JSONReporter, MarkdownReporter, HTMLReporter
    
    if args.html:
        HTMLReporter(data).report(args.file)
    elif args.json:
        JSONReporter(data).report(args.file)
    elif args.markdown:
        MarkdownReporter(data).report(args.file)
    else:
        ConsoleReporter(data).report(args.file)

if __name__ == '__main__':
    main()
