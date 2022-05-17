from __future__ import annotations

import re
from argparse import ArgumentParser
from argparse import Namespace
from pathlib import Path
from stat import S_IWGRP
from stat import S_IWOTH
from stat import S_IWUSR
from typing import Callable
from typing import NoReturn
from unittest.mock import create_autospec

import pytest

from pytest_memray.utils import WriteEnabledDirectoryAction
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
def test_parse_memory_string(the_str: str, expected: float) -> None:
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
def test_parse_incorrect_memory_string(the_str: str) -> None:
    with pytest.raises(ValueError):
        parse_memory_string(the_str)


WDirCheck = Callable[[Path], Namespace]


@pytest.fixture()
def w_dir_check() -> WDirCheck:
    def _func(path: Path) -> Namespace:
        action = WriteEnabledDirectoryAction(option_strings=["-m"], dest="d")
        parser = create_autospec(ArgumentParser)

        def error(message: str) -> NoReturn:
            raise ValueError(message)

        parser.error.side_effect = error
        namespace = Namespace()
        action(parser, namespace, str(path))
        return namespace

    return _func


def test_write_enabled_dir_ok(w_dir_check: WDirCheck, tmp_path: Path) -> None:
    namespace = w_dir_check(tmp_path)
    assert namespace.d == tmp_path


def test_write_enabled_dir_is_file(w_dir_check: WDirCheck, tmp_path: Path) -> None:
    path = tmp_path / "a"
    path.write_text("")
    exp = f"{path} must be a directory"
    with pytest.raises(ValueError, match=re.escape(exp)):
        w_dir_check(path)


def test_write_enabled_dir_read_only(w_dir_check: WDirCheck, tmp_path: Path) -> None:
    path = tmp_path
    write = S_IWUSR | S_IWGRP | S_IWOTH
    path.chmod(path.stat().st_mode & ~write)
    exp = f"{path} is read-only"
    try:
        with pytest.raises(ValueError, match=re.escape(exp)):
            w_dir_check(path)
    finally:
        path.chmod(path.stat().st_mode | write)


def test_write_enabled_dir_cannot_create(
    w_dir_check: WDirCheck, tmp_path: Path
) -> None:
    path = tmp_path / "d"
    write = S_IWUSR | S_IWGRP | S_IWOTH
    tmp_path.chmod(tmp_path.stat().st_mode & ~write)
    exp = f"cannot create directory {path} due to [Errno 13] Permission denied:"
    try:
        with pytest.raises(ValueError, match=re.escape(exp)):
            w_dir_check(path)
    finally:
        tmp_path.chmod(tmp_path.stat().st_mode | write)
