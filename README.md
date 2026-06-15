# LeakWatch

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
- **Command-Line Interface**: Run your Python scripts under a monitor or export reports to JSON, Markdown, or HTML.

## Installation

Install using pip:

```bash
pip install .
```

## Quick Start

```python
from leakwatch import watch

# Call watch at the start of your script
watch()

# Your application code runs...
```

For more examples, refer to the documentation or [prd2.md](prd2.md).
