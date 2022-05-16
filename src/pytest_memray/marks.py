from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from typing import Tuple

from memray import AllocationRecord

from .utils import parse_memory_string
from .utils import sizeof_fmt

PytestSection = Tuple[str, str]


@dataclass
class _MemoryInfo:
    """Type that holds all memray-related info for a failed test."""

    max_memory: float
    total_allocated_memory: int
    allocations: list[AllocationRecord]

    @property
    def section(self) -> PytestSection:
        """Return a tuple in the format expected by section reporters."""
        total_memory_str = sizeof_fmt(self.total_allocated_memory)
        max_memory_str = sizeof_fmt(self.max_memory)
        text_lines = [
            f"Test is using {total_memory_str} out of limit of {max_memory_str}",
            "List of allocations: ",
        ]
        for record in self.allocations:
            size = record.size
            stack_trace = record.stack_trace()
            if not stack_trace:
                continue
            (function, file, line), *_ = stack_trace
            text_lines.append(f"\t- {function}:{file}:{line} -> {sizeof_fmt(size)}")
        return "memray-max-memory", "\n".join(text_lines)

    @property
    def long_repr(self) -> str:
        """Generate a longrepr user-facing error message."""
        total_memory_str = sizeof_fmt(self.total_allocated_memory)
        max_memory_str = sizeof_fmt(self.max_memory)
        return f"Test was limited to {max_memory_str} but allocated {total_memory_str}"


def limit_memory(
    limit: str, *, _allocations: list[AllocationRecord]
) -> Optional[_MemoryInfo]:
    """Limit memory used by the test."""
    max_memory = parse_memory_string(limit)
    total_allocated_memory = sum(record.size for record in _allocations)
    if total_allocated_memory < max_memory:
        return None
    return _MemoryInfo(max_memory, total_allocated_memory, _allocations)


__all__ = [
    "limit_memory",
]
