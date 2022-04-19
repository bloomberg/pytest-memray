<p align="center">
<img src="https://raw.githubusercontent.com/bloomberg/pytest-memray/main/docs/_static/images/logo.png" width="70%">
</p>



# pytest-memray

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-memray)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/pytest-memray)
![PyPI](https://img.shields.io/pypi/v/pytest-memray)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-memray)
[![Tests](https://github.com/bloomberg/pytest-memray/actions/workflows/build.yml/badge.svg)](https://github.com/bloomberg/pytest-memray/actions/workflows/build.yml)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)



pytest-memray is a pytest plugin for easy integration of `memray`.

# Installation

pytest-memray requires Python 3.7+ and can be easily installed using most common Python
packaging tools. We recommend installing the latest stable release from
[PyPI](https://pypi.org/project/pytest-memray/) with pip:

```shell
    pip install pytest-memray
```

# Documentation

You can find the latest documentation available [here](https://bloomberg.github.io/pytest-memray/).

# Usage

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

# License

pytest-memray is Apache-2.0 licensed, as found in the [LICENSE](LICENSE) file.

# Code of Conduct

- [Code of Conduct](https://github.com/bloomberg/.github/blob/main/CODE_OF_CONDUCT.md)

This project has adopted a Code of Conduct. If you have any concerns about the Code, or behavior which you have experienced in the project, please contact us at opensource@bloomberg.net.

# Security Policy

- [Security Policy](https://github.com/bloomberg/pytest-memray/security/policy)

If you believe you have identified a security vulnerability in this project, please send email to the project team at opensource@bloomberg.net, detailing the suspected issue and any methods you've found to reproduce it.

Please do NOT open an issue in the GitHub repository, as we'd prefer to keep vulnerability reports private until we've had an opportunity to review and address them.

# Contributing

We welcome your contributions to help us improve and extend this project!

Below you will find some basic steps required to be able to contribute to the project. If you have any questions about this process or any other aspect of contributing to a Bloomberg open source project, feel free to send an email to opensource@bloomberg.net and we'll get your questions answered as quickly as we can.

## Contribution Licensing

Since this project is distributed under the terms of an [open source license](LICENSE), contributions that you make
are licensed under the same terms. In order for us to be able to accept your contributions,
we will need explicit confirmation from you that you are able and willing to provide them under
these terms, and the mechanism we use to do this is called a Developer's Certificate of Origin
[(DCO)](https://github.com/bloomberg/.github/blob/main/DCO.md). This is very similar to the process used by the Linux(R) kernel, Samba, and many
other major open source projects.

To participate under these terms, all that you must do is include a line like the following as the
last line of the commit message for each commit in your contribution:

    Signed-Off-By: Random J. Developer <random@developer.example.org>

The simplest way to accomplish this is to add `-s` or `--signoff` to your `git commit` command.

You must use your real name (sorry, no pseudonyms, and no anonymous contributions).

## Steps

- Create an Issue, selecting 'Feature Request', and explain the proposed change.
- Follow the guidelines in the issue template presented to you.
- Submit the Issue.
- Submit a Pull Request and link it to the Issue by including "#<issue number>" in the Pull Request summary.
