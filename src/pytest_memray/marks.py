from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple
from typing import cast
from typing import Callable
from typing import Iterable
from typing import Optional

from memray import AllocationRecord
from memray import FileReader
from pytest import Config

from .utils import parse_memory_string
from .utils import sizeof_fmt
from .utils import value_or_ini

PytestSection = Tuple[str, str]

StackElement = Tuple[str, str, int]
LeaksFilteringFunction = Callable[[Iterable[StackElement]], bool]


@dataclass
class _MemoryInfo:
    """Type that holds memory-related info for a failed test."""

    max_memory: float
    total_allocated_memory: int
    allocations: list[AllocationRecord]
    num_stacks: int
    native_stacks: bool

    def _generate_section_text(self, limit_text: str, header_text: str) -> str:
        text_lines = [
            f"{header_text} {sizeof_fmt(self.total_allocated_memory)} out of limit of {sizeof_fmt(self.max_memory)}"
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

        return "\n".join(text_lines)

    @property
    def section(self) -> PytestSection:
        """Return a tuple in the format expected by section reporters."""
        return (
            "memray-max-memory",
            self._generate_section_text("Test is using", "List of allocations:"),
        )

    @property
    def long_repr(self) -> str:
        """Generate a longrepr user-facing error message."""
        return f"Test was limited to {sizeof_fmt(self.max_memory)} but allocated {sizeof_fmt(self.total_allocated_memory)}"


@dataclass
class _LeakedInfo(_MemoryInfo):
    """Type that holds leaked memory-related info for a failed test."""

    @property
    def section(self) -> PytestSection:
        """Return a tuple in the format expected by section reporters."""
        return (
            "memray-leaked-memory",
            self._generate_section_text("Test leaked", "List of leaked allocations:"),
        )

    @property
    def long_repr(self) -> str:
        """Generate a longrepr user-facing error message."""
        return (
            f"Test was allowed to leak {sizeof_fmt(self.max_memory)} "
            "per location but at least one location leaked more"
        )


def limit_memory(
    limit: str, *, _result_file: Path, _config: Config
) -> _MemoryInfo | None:
    """Limit memory used by the test."""
    reader = FileReader(_result_file)
    func = reader.get_high_watermark_allocation_records
    allocations: list[AllocationRecord] = list((func(merge_threads=True)))
    max_memory = parse_memory_string(limit)
    total_allocated_memory = sum(record.size for record in allocations)
    if total_allocated_memory < max_memory:
        return None
    num_stacks: int = cast(int, value_or_ini(_config, "stacks"))
    native_stacks: bool = cast(bool, value_or_ini(_config, "native"))
    return _MemoryInfo(
        max_memory, total_allocated_memory, allocations, num_stacks, native_stacks
    )


def limit_leaks(
    location_limit: str,
    *,
    filter_fn: Optional[LeaksFilteringFunction] = None,
    _result_file: Path,
    _config: Config,
) -> _MemoryInfo | None:
    reader = FileReader(_result_file)
    func = reader.get_leaked_allocation_records
    allocations: list[AllocationRecord] = list((func(merge_threads=True)))

    memory_limit = parse_memory_string(location_limit)

    leaked_allocations = list(
        allocation
        for allocation in allocations
        if (
            allocation.size >= memory_limit
            and (filter_fn is None or filter_fn(allocation.hybrid_stack_trace()))
        )
    )
    if not leaked_allocations:
        return None
    total_leaked_memory = sum(allocation.size for allocation in leaked_allocations)

    num_stacks: int = cast(int, value_or_ini(_config, "stacks"))
    return _LeakedInfo(
        memory_limit,
        total_leaked_memory,
        leaked_allocations,
        num_stacks,
        native_stacks=True,
    )


__all__ = [
    "limit_memory",
]
