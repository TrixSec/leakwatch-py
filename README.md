# LeakWatch

[![PyPI version](https://img.shields.io/pypi/v/leakwatch-py.svg)](https://pypi.org/project/leakwatch-py/)
[![Python](https://img.shields.io/pypi/pyversions/leakwatch-py.svg)](https://pypi.org/project/leakwatch-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LeakWatch is a lightweight, easy-to-use Python library designed to help developers identify memory leaks and abnormal memory growth within Python applications.

Unlike traditional profilers that provide raw memory statistics, LeakWatch focuses on explaining:
- **What** is growing (which object types).
- **Where** it was created (source attribution / traceback).
- **How fast** it is growing (growth rate over time).
- **Whether** it is likely a memory leak (calculates a leak score).

## Features

- **Snapshot Comparison**: Capture and compare memory states dynamically.
- **Context Monitoring**: Monitor code blocks or decorate functions using `monitor`.
- **Source Attribution**: Resolve file and line tracebacks for allocated objects.
- **Leak Scoring**: Intelligent heuristic to identify the probability of a leak.
- **Report Export**: Generate reports in JSON, Markdown, or beautiful dark-themed HTML.
- **Command-Line Interface**: Run your Python scripts under a monitor or export reports.

## Installation

Install using pip:

```bash
pip install leakwatch-py
```

## Quick Start

### One-liner

```python
from leakwatch import watch

watch()
# Your application code runs...
```

### Snapshot Mode

```python
from leakwatch import snapshot

snapshot("before")

# ... your code ...

snapshot("after")
```

### Context Manager

```python
from leakwatch import monitor

with monitor():
    run_application()
```

### Generate Reports

```python
from leakwatch import report

report(format='html', path='report.html')
report(format='json', path='report.json')
report(format='markdown', path='report.md')
```

## CLI Usage

Monitor a script:

```bash
leakwatch run python app.py
```

Export a report:

```bash
leakwatch report --html
leakwatch report --json
leakwatch report --markdown
```

## How It Works

LeakWatch uses Python's built-in `tracemalloc` and `gc` modules to:

1. **Capture snapshots** of memory allocations and object counts at different points in time.
2. **Analyze growth patterns** by comparing snapshots to identify which object types are increasing.
3. **Compute a leak score** using heuristics such as growth percentage, monotonic increase detection, and object classification (built-in vs custom types).
4. **Attribute sources** by resolving `tracemalloc` tracebacks to find where leaking objects were allocated.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Vicky** — [TrixSec](https://github.com/TrixSec)
