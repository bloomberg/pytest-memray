from __future__ import annotations

import argparse
import os
import re
from argparse import Action
from argparse import ArgumentParser
from argparse import Namespace
from pathlib import Path
from typing import Sequence

from pytest import Config


def sizeof_fmt(num: int | float, suffix: str = "B") -> str:
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}{'Yi'}{suffix}"


UNIT_REGEXP = re.compile(
    r"""
(?P<quantity>\+?\d*\.\d+|\+?\d+) # A number
\s*                              # Some optional spaces
(?P<unit>[KMGTP]B|B)             # The unit, e.g. KB, MB, B,...
""",
    re.VERBOSE | re.IGNORECASE,
)
UNIT_TO_MULTIPLIER = {
    "B": 1,
    "KB": 1024**1,
    "MB": 1024**2,
    "GB": 1024**3,
    "TB": 1024**4,
    "PB": 1024**5,
}


def parse_memory_string(mem_str: str) -> float:
    match = UNIT_REGEXP.match(mem_str)
    if not match:
        raise ValueError(f"Invalid memory size format: {mem_str}")
    quantity, unit = match.groups()
    return float(quantity) * UNIT_TO_MULTIPLIER[unit.upper()]


def value_or_ini(config: Config, key: str) -> object:
    value = config.getvalue(key)
    if value:
        return value
    try:
        return config.getini(key)
    except (KeyError, ValueError):
        return value


class WriteEnabledDirectoryAction(Action):
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[str] | None,
        option_string: str | None = None,
    ) -> None:
        assert isinstance(values, str)
        folder = Path(values).absolute()
        if folder.exists():
            if folder.is_dir():
                if not os.access(folder, os.W_OK):
                    parser.error(f"{folder} is read-only")
            else:
                parser.error(f"{folder} must be a directory")
        else:
            try:
                folder.mkdir(parents=True)
            except OSError as exc:
                parser.error(f"cannot create directory {folder} due to {exc}")
        setattr(namespace, self.dest, folder)


def positive_int(value: str) -> int:
    the_int = int(value)
    if the_int <= 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")
    return the_int


__all__ = [
    "WriteEnabledDirectoryAction",
    "parse_memory_string",
    "sizeof_fmt",
    "value_or_ini",
    "positive_int",
]
