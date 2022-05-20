<img src="https://raw.githubusercontent.com/bloomberg/pytest-memray/main/docs/_static/images/logo.png" width="70%" style="display: block; margin: 0 auto"  alt="logo"/>

# pytest-memray

[![PyPI](https://img.shields.io/pypi/v/pytest-memray?style=flat-square)](https://pypi.org/project/pytest-memray)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/pytest-memray?style=flat-square)](https://pypi.org/project/pytest-memray)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pytest-memray?style=flat-square)](https://pypi.org/project/pytest-memray)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-memray?style=flat-square)](https://pypistats.org/packages/pytest-memray)
[![PyPI - License](https://img.shields.io/pypi/l/pytest-memray?style=flat-square)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/bloomberg/pytest-memray/actions/workflows/build.yml/badge.svg)](https://github.com/bloomberg/pytest-memray/actions/workflows/build.yml)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)

pytest-memray is a pytest plugin for easy integration of
[memray](https://github.com/bloomberg/memray).

## Installation

pytest-memray requires Python 3.8 or higher and can be easily installed using most common
Python packaging tools. We recommend installing the latest stable release from
[PyPI](https://pypi.org/project/pytest-memray/) with pip:

```shell
pip install pytest-memray
```

## Documentation

You can find the latest documentation available
[here](https://pytest-memray.readthedocs.io/en/latest/).

## Quick introduction

To use the plugin in a pytest run, simply add `--memray` to the command line invocation:

```shell
pytest --memray tests
```

After the test suite runs you'll see a memory report printed:

```bash
=================================== test session starts ====================================
platform linux -- Python 3.10.4, pytest-7.1.2, pluggy-1.0.0
cachedir: /v/.pytest_cache
rootdir: /w
plugins: memray-1.1.0
collected 2 items

demo/test_ok.py .M                                                                   [100%]

========================================= FAILURES =========================================
____________________________________ test_memory_exceed ____________________________________
Test was limited to 100.0KiB but allocated 117.2KiB
------------------------------------ memray-max-memory -------------------------------------
Test is using 117.2KiB out of limit of 100.0KiB
List of allocations:
	- <listcomp>:/w/demo/test_ok.py:17 -> 117.2KiB

====================================== MEMRAY REPORT =======================================
Allocations results for demo/test_ok.py::test_memory_exceed

	 📦 Total memory allocated: 117.2KiB
	 📏 Total allocations: 30
	 📊 Histogram of allocation sizes: |█|
	 🥇 Biggest allocating functions:
		- <listcomp>:/w/demo/test_ok.py:17 -> 117.2KiB


Allocations results for demo/test_ok.py::test_track

	 📦 Total memory allocated: 54.9KiB
	 📏 Total allocations: 71
	 📊 Histogram of allocation sizes: |█   ▅    |
	 🥇 Biggest allocating functions:
		- test_track:/w/demo/test_ok.py:12 -> 39.1KiB
		- _compile_bytecode:<frozen importlib._bootstrap_external>:672 -> 7.2KiB
		- _call_with_frames_removed:<frozen importlib._bootstrap>:241 -> 4.7KiB
		- _call_with_frames_removed:<frozen importlib._bootstrap>:241 -> 1.8KiB
		- _is_marked_for_rewrite:/v/lib/python3.10/site-packages/_pytest/assertion/rewrite.py:240 -> 1.1KiB


================================= short test summary info ==================================
MEMORY PROBLEMS demo/test_ok.py::test_memory_exceed
=============================== 1 failed, 1 passed in 0.01s ================================
```

## Configuration - CLI flags

- `--memray` - activate memray tracking
- `--most-allocations=MOST_ALLOCATIONS` - show the N tests that allocate most memory
  (N=0 for all)
- `--hide-memray-summary` - hide the memray summary at the end of the execution
- `--memray-bin-path` - path where to write the memray binary dumps (by default a
  temporary folder)

## Configuration - INI

- `memray(bool)` - activate memray tracking
- `most-allocations(string)` - show the N tests that allocate most memory (N=0 for all)
- `hide_memray_summary(bool)` - hide the memray summary at the end of the execution

## License

pytest-memray is Apache-2.0 licensed, as found in the [LICENSE](LICENSE) file.

## Code of Conduct

- [Code of Conduct](https://github.com/bloomberg/.github/blob/main/CODE_OF_CONDUCT.md)

This project has adopted a Code of Conduct. If you have any concerns about the Code, or
behavior which you have experienced in the project, please contact us at
opensource@bloomberg.net.

## Security Policy

- [Security Policy](https://github.com/bloomberg/pytest-memray/security/policy)

If you believe you have identified a security vulnerability in this project, please send
email to the project team at opensource@bloomberg.net, detailing the suspected issue and
any methods you've found to reproduce it.

Please do NOT open an issue in the GitHub repository, as we'd prefer to keep
vulnerability reports private until we've had an opportunity to review and address them.

## Contributing

We welcome your contributions to help us improve and extend this project!

Below you will find some basic steps required to be able to contribute to the project.
If you have any questions about this process or any other aspect of contributing to a
Bloomberg open source project, feel free to email opensource@bloomberg.net, and we'll
get your questions answered as quickly as we can.

### Contribution Licensing

Since this project is distributed under the terms of an [open source license](LICENSE),
contributions that you make are licensed under the same terms. In order for us to be
able to accept your contributions, we will need explicit confirmation from you that you
are able and willing to provide them under these terms, and the mechanism we use to do
this is called a Developer's Certificate of Origin
[(DCO)](https://github.com/bloomberg/.github/blob/main/DCO.md). This is very similar to
the process used by the Linux(R) kernel, Samba, and many other major open source
projects.

To participate under these terms, all that you must do is include a line like the
following as the last line of the commit message for each commit in your contribution:

```git
Signed-Off-By: Random J. Developer <random@developer.example.org>
```

The simplest way to accomplish this is to add `-s` or `--signoff` to your `git commit`
command.

You must use your real name (sorry, no pseudonyms, and no anonymous contributions).

### Steps

- Create an Issue, selecting 'Feature Request', and explain the proposed change.
- Follow the guidelines in the issue template presented to you.
- Submit the Issue.
- Submit a Pull Request and link it to the Issue by including "#<issue number>" in the
  Pull Request summary.

### Development

The project requires a Linux OS to work. To set up a DEV environment use tox (or
directly the make targets). You can use Docker to run the test suite on non Linux as in
(you can parametrize tox by passing additional arguments at the end):

```shell
docker-compose run --rm test tox
```
