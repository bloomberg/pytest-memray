# Dependency Compatibility Test Results

## Environment
- Operating system: Kali Linux
- Python: 3.12.7
- Project: pytest-memray
- Tests:
  - test_bin_path_with_long_test_id
  - test_bin_path_with_long_test_id_and_long_prefix

## Results

| pytest | Memray | Result |
|---|---|---|
| 8.0.0 | 1.19.1 | PASS (2 tests) |
| 8.0.0 | 1.20.0 | PASS (2 tests) |
| 9.2.0 | 1.19.1 | FAIL (2 tests) |
| 9.2.0 | 1.20.0 | FAIL (2 tests) |

## Observation

Both tests pass with pytest 8.0.0 and fail with pytest 9.2.0
in the tested environment. Changing Memray between 1.19.1
and 1.20.0 did not change the result.

The failing assertions concern generated binary filenames.
The nested test executions themselves pass.

## Limitation

These results cover two tests on Python 3.12.7 only.
They do not establish compatibility across all supported
Python, pytest, or Memray versions.
