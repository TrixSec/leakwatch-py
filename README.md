# LeakWatch

<p align="center">
  <a href="https://pypi.org/project/leakwatch-py/"><img src="https://img.shields.io/pypi/v/leakwatch-py?style=for-the-badge&logo=pypi&logoColor=white&color=blue" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/leakwatch-py/"><img src="https://img.shields.io/pypi/pyversions/leakwatch-py?style=for-the-badge&logo=python&logoColor=white" alt="Python Versions"></a>
  <a href="https://github.com/TrixSec/LeakWatch/blob/main/LICENSE"><img src="https://img.shields.io/github/license/TrixSec/LeakWatch?style=for-the-badge&logo=gnu&logoColor=white&color=green" alt="License"></a>
  <a href="https://pypi.org/project/leakwatch-py/"><img src="https://img.shields.io/pypi/dm/leakwatch-py?style=for-the-badge&logo=pypi&logoColor=white&color=orange" alt="PyPI Downloads"></a>
</p>

<p align="center">
  <a href="https://github.com/TrixSec/LeakWatch/stargazers"><img src="https://img.shields.io/github/stars/TrixSec/LeakWatch?style=for-the-badge&logo=github&color=yellow" alt="GitHub Stars"></a>
  <a href="https://github.com/TrixSec/LeakWatch/network/members"><img src="https://img.shields.io/github/forks/TrixSec/LeakWatch?style=for-the-badge&logo=github&color=lightgrey" alt="GitHub Forks"></a>
  <a href="https://github.com/TrixSec/LeakWatch/issues"><img src="https://img.shields.io/github/issues/TrixSec/LeakWatch?style=for-the-badge&logo=github&color=red" alt="GitHub Issues"></a>
  <a href="https://github.com/TrixSec/LeakWatch/commits/main"><img src="https://img.shields.io/github/last-commit/TrixSec/LeakWatch?style=for-the-badge&logo=github&color=purple" alt="Last Commit"></a>
</p>

<p align="center">
  <a href="https://github.com/TrixSec/LeakWatch"><img src="https://img.shields.io/github/repo-size/TrixSec/LeakWatch?style=for-the-badge&logo=github&color=teal" alt="Repository Size"></a>
  <a href="https://github.com/TrixSec/LeakWatch/releases"><img src="https://img.shields.io/github/v/release/TrixSec/LeakWatch?style=for-the-badge&logo=github&color=darkgreen" alt="Latest Release"></a>
  <a href="https://t.me/Trixsec"><img src="https://img.shields.io/badge/Telegram-Channel-blue?style=for-the-badge&logo=telegram" alt="Telegram"></a>
</p>


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
