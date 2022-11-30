from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from typing import cast

from memray import AllocationRecord
from pytest import Config

from .utils import parse_memory_string
from .utils import sizeof_fmt
from .utils import value_or_ini

PytestSection = Tuple[str, str]


@dataclass
class _MemoryInfo:
    """Type that holds all memray-related info for a failed test."""

    max_memory: float
    total_allocated_memory: int
    allocations: list[AllocationRecord]
    num_stacks: int
    native_stacks: bool

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
            stack_trace = (
                record.hybrid_stack_trace()
                if self.native_stacks
                else record.stack_trace()
            )
            if not stack_trace:
                continue
            padding = " " * 4
            text_lines.append(f"{padding}- {sizeof_fmt(size)} allocated here:")
            stacks_left = self.num_stacks
            for function, file, line in stack_trace:
                if stacks_left <= 0:
                    break
                text_lines.append(f"{padding*2}{function}:{file}:{line}")
                stacks_left -= 1

        return "memray-max-memory", "\n".join(text_lines)

    @property
    def long_repr(self) -> str:
        """Generate a longrepr user-facing error message."""
        total_memory_str = sizeof_fmt(self.total_allocated_memory)
        max_memory_str = sizeof_fmt(self.max_memory)
        return f"Test was limited to {max_memory_str} but allocated {total_memory_str}"


def limit_memory(
    limit: str, *, _allocations: list[AllocationRecord], _config: Config
) -> _MemoryInfo | None:
    """Limit memory used by the test."""
    max_memory = parse_memory_string(limit)
    total_allocated_memory = sum(record.size for record in _allocations)
    if total_allocated_memory < max_memory:
        return None
    num_stacks: int = cast(int, value_or_ini(_config, "stacks"))
    native_stacks: bool = cast(bool, value_or_ini(_config, "native"))
    return _MemoryInfo(
        max_memory, total_allocated_memory, _allocations, num_stacks, native_stacks
    )


__all__ = [
    "limit_memory",
]
