<img src="https://raw.githubusercontent.com/bloomberg/memray/main/docs/_static/images/memray.png" align="right" height="150" width="130"/>

# pytest-memray

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-memray)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/pytest-memray)
![PyPI](https://img.shields.io/pypi/v/pytest-memray)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-memray)
[![Tests](https://github.com/bloomberg/pytest-memray/actions/workflows/build.yml/badge.svg)](https://github.com/bloomberg/pytest-memray/actions/workflows/build.yml)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)



pytest-memray is a pytest plugin for easy integration of `memray`.

## Usage

To use the plugin in a pytest run, simply add `--memray` to the command line invocation:

```
pytest --memray tests/
```

Would produce a report like:

```
python3 -m pytest tests --memray
=============================================================================================================================== test session starts ================================================================================================================================
platform linux -- Python 3.8.10, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
rootdir: /mypackage, configfile: pytest.ini
plugins: cov-2.12.0, memray-0.1.0
collected 21 items

tests/test_package.py .....................                                                                                                                                                                                                                      [100%]


================================================================================================================================= MEMRAY REPORT ==================================================================================================================================
Allocations results for tests/test_package.py::some_test_that_allocates

	 📦 Total memory allocated: 24.4MiB
	 📏 Total allocations: 33929
	 📊 Histogram of allocation sizes: |▂   █    |
	 🥇 Biggest allocating functions:
		- parse:/opt/bb/lib/python3.8/ast.py:47 -> 3.0MiB
		- parse:/opt/bb/lib/python3.8/ast.py:47 -> 2.3MiB
		- _visit:/opt/bb/lib/python3.8/site-packages/astroid/transforms.py:62 -> 576.0KiB
		- parse:/opt/bb/lib/python3.8/ast.py:47 -> 517.6KiB
		- __init__:/opt/bb/lib/python3.8/site-packages/astroid/node_classes.py:1353 -> 512.0KiB
```

## Configuration

This plugin provides a clean minimal set of command line options that are added to pytest.

- `--memray`: Activate memray tracking.
- `--most-allocations=MOST_ALLOCATIONS`: Show the N tests that allocate most memory (N=0 for all).
- `--hide-memray-summary`: Hide the memray summary at the end of the execution.

## Markers

There are some builtin markers and fixtures in `pytest-memray`:

### `limit_memory`

When this marker is applied to a test, it will cause the test to fail if the
execution of the test allocates more memory than allowed. It takes a single
argument with a string indicating the maximum memory that the test can
allocate.

The format for the string is `<NUMBER> ([KMGTP]B|B)`. The marker will raise
ValueError if the string format cannot be parsed correctly.

Example of usage:

```python
@pytest.mark.limit_memory("24 MB")
def test_foobar():
    # do some stuff that allocates memory
```
