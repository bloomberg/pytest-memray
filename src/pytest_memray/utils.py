from __future__ import annotations

import re


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
    "KB": 1024 ** 1,
    "MB": 1024 ** 2,
    "GB": 1024 ** 3,
    "TB": 1024 ** 4,
    "PB": 1024 ** 5,
}


def parse_memory_string(mem_str: str) -> float:
    match = UNIT_REGEXP.match(mem_str)
    if not match:
        raise ValueError(f"Invalid memory size format: {mem_str}")
    quantity, unit = match.groups()
    return float(quantity) * UNIT_TO_MULTIPLIER[unit.upper()]
