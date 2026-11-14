# Dependency Compatibility Test Results

## Environment
- Operating system: Kali Linux
- Python: 3.12.7
- Project: pytest-memray

## Initial Tests (Before Fix)

| pytest | Memray | Result |
|---|---|---|
| 8.0.0 | 1.19.1 | PASS (2 tests) |
| 8.0.0 | 1.20.0 | PASS (2 tests) |
| 9.2.0 | 1.19.1 | FAIL (2 tests) |
| 9.2.0 | 1.20.0 | FAIL (2 tests) |

## Root Cause

Pytest 9.2.0 generated a shortened parameter ID for the 300-character string used in the tests. The tests expected the long parameter ID to be retained when generating binary filenames.

## Fix

Both test cases were updated to specify the parameter ID explicitly:

`@pytest.mark.parametrize('v', ['a' * 300], ids=['a' * 300])`

This makes the intended long parameter ID deterministic.

## Post-Fix Verification

| pytest | Memray | Result |
|---|---|---|
| 8.0.0 | 1.20.0 | PASS (2 tests) |
| 9.2.0 | 1.20.0 | PASS (2 tests) |

Full test suite using pytest 9.2.0 and Memray 1.20.0:

- 99 passed
- 6 skipped
- 0 failed

The six skipped tests require Python 3.13.3 or later.

## Limitations

Testing was performed on Python 3.12.7 only. These results do not establish compatibility across all supported Python, pytest, or Memray versions.
