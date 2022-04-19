import pytest

from pytest_memray.utils import parse_memory_string


@pytest.mark.parametrize(
    "the_str, expected",
    [
        ("100 B", 100),
        ("100B", 100),
        ("100.0B", 100),
        ("100.0   B", 100),
        ("100 KB", 100 * 1024),
        ("3 MB", 3 * 1024**2),
        ("3.0 GB", 3 * 1024**3),
        ("60.0 TB", 60 * 1024**4),
        ("3.14 PB", 3.14 * 1024**5),
        ("+100.0B", 100),
        ("+100.0   B", 100),
        ("+100 KB", 100 * 1024),
        ("100 Kb", 100 * 1024),
        ("3 Mb", 3 * 1024**2),
        ("3.0 Gb", 3 * 1024**3),
        ("60.0 Tb", 60 * 1024**4),
        ("3.14 Pb", 3.14 * 1024**5),
        ("+100.0b", 100),
        ("+100.0   b", 100),
        ("+100 Kb", 100 * 1024),
    ],
)
def test_parse_memory_string(the_str, expected):
    assert parse_memory_string(the_str) == expected


@pytest.mark.parametrize(
    "the_str",
    [
        "Some bad string",
        "100.0",
        "100",
        "100 NB",
        "100 K",
        "100.0 PK",
        "100 PK",
        "-100 B",
        "-100.0 B",
        "+100.0 K",
    ],
)
def test_parse_incorrect_memory_string(the_str):
    with pytest.raises(ValueError):
        parse_memory_string(the_str)
