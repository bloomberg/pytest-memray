from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from typing import Optional
from typing import Protocol
from typing import Tuple
from typing import cast

from memray import AllocationRecord
from memray import FileReader
from pytest import Config

from .utils import parse_memory_string
from .utils import sizeof_fmt
from .utils import value_or_ini

PytestSection = Tuple[str, str]


@dataclass
class StackFrame:
    """One frame of a call stack.

    Each frame has attributes to tell you what code was executing.
    """

    function: str
    """The function being executed, or ``"???"`` if unknown."""

    filename: str
    """The source file being executed, or ``"???"`` if unknown."""

    lineno: int
    """The line number of the executing line, or ``0`` if unknown."""


@dataclass
class Stack:
    """The call stack that led to some memory allocation.

    You can inspect the frames which make up the call stack.
    """

    frames: Tuple[StackFrame, ...]
    """The frames that make up the call stack, most recent first."""


class LeaksFilterFunction(Protocol):
    """A callable that can decide whether to ignore some memory leaks.

    This can be used to suppress leak reports from locations that are known to
    leak. For instance, you might know that objects of a certain type are
    cached by the code you're invoking, and so you might want to ignore all
    reports of leaked memory allocated below that type's constructor.

    You can provide any callable with the following signature as the
    ``filter_fn`` keyword argument for the `.limit_leaks` marker:
    """

    def __call__(self, stack: Stack) -> bool:
        """Return whether allocations from this stack should be reported.

        Return ``True`` if you want the leak to be reported, or ``False`` if
        you want it to be suppressed.
        """
        ...


@dataclass
class _MemoryInfo:
    """Type that holds memory-related info for a failed test."""

    max_memory: float
    allocations: list[AllocationRecord]
    num_stacks: int
    native_stacks: bool
    total_allocated_memory: int

    @property
    def section(self) -> PytestSection:
        """Return a tuple in the format expected by section reporters."""
        body = _generate_section_text(
            self.allocations, self.native_stacks, self.num_stacks
        )
        return (
            "memray-max-memory",
            "List of allocations:\n" + body,
        )

    @property
    def long_repr(self) -> str:
        """Generate a longrepr user-facing error message."""
        return (
            f"Test was limited to {sizeof_fmt(self.max_memory)} "
            f"but allocated {sizeof_fmt(self.total_allocated_memory)}"
        )


@dataclass
class _LeakedInfo:
    """Type that holds leaked memory-related info for a failed test."""

    max_memory: float
    allocations: list[AllocationRecord]
    num_stacks: int
    native_stacks: bool

    @property
    def section(self) -> PytestSection:
        """Return a tuple in the format expected by section reporters."""
        body = _generate_section_text(
            self.allocations, self.native_stacks, self.num_stacks
        )
        return (
            "memray-leaked-memory",
            "List of leaked allocations:\n" + body,
        )

    @property
    def long_repr(self) -> str:
        """Generate a longrepr user-facing error message."""
        return (
            f"Test was allowed to leak {sizeof_fmt(self.max_memory)} "
            "per location but at least one location leaked more"
        )


@dataclass
class _MoreMemoryInfo:
    previous_memory: float
    new_memory: float

    @property
    def section(self) -> PytestSection:
        """Return a tuple in the format expected by section reporters."""
        return (
            "memray-max-memory",
            "Test uses more memory than previous run",
        )

    @property
    def long_repr(self) -> str:
        """Generate a longrepr user-facing error message."""
        return (
            f"Test previously used {sizeof_fmt(self.previous_memory)} "
            f"but now uses {sizeof_fmt(self.new_memory)}"
        )


def _generate_section_text(
    allocations: list[AllocationRecord], native_stacks: bool, num_stacks: int
) -> str:
    text_lines = []
    for record in allocations:
        size = record.size
        stack_trace = (
            record.hybrid_stack_trace() if native_stacks else record.stack_trace()
        )
        if not stack_trace:
            continue
        padding = " " * 4
        text_lines.append(f"{padding}- {sizeof_fmt(size)} allocated here:")
        stacks_left = num_stacks
        for function, file, line in stack_trace:
            if stacks_left <= 0:
                text_lines.append(f"{padding*2}...")
                break
            text_lines.append(f"{padding*2}{function}:{file}:{line}")
            stacks_left -= 1

    return "\n".join(text_lines)


def _passes_filter(
    stack: Iterable[Tuple[str, str, int]], filter_fn: Optional[LeaksFilterFunction]
) -> bool:
    if filter_fn is None:
        return True

    frames = tuple(StackFrame(*frame) for frame in stack)
    return filter_fn(Stack(frames))


def limit_memory(
    limit: str,
    *,
    current_thread_only: bool = False,
    _result_file: Path,
    _config: Config,
    _test_id: str,
) -> _MemoryInfo | _MoreMemoryInfo | None:
    """Limit memory used by the test."""
    reader = FileReader(_result_file)
    allocations: list[AllocationRecord] = [
        record
        for record in reader.get_high_watermark_allocation_records(
            merge_threads=not current_thread_only
        )
        if not current_thread_only or record.tid == reader.metadata.main_thread_id
    ]
    max_memory = parse_memory_string(limit)
    total_allocated_memory = sum(record.size for record in allocations)

    if _config.cache is not None:
        cache = _config.cache.get(f"memray/{_test_id}", {})
        previous = cache.get("total_allocated_memory", float("inf"))
        fail_on_increase = cast(bool, value_or_ini(_config, "fail_on_increase"))
        if fail_on_increase and total_allocated_memory > previous:
            return _MoreMemoryInfo(previous, total_allocated_memory)

        cache["total_allocated_memory"] = total_allocated_memory
        _config.cache.set(f"memray/{_test_id}", cache)

    if total_allocated_memory < max_memory:
        return None
    num_stacks: int = cast(int, value_or_ini(_config, "stacks"))
    native_stacks: bool = cast(bool, value_or_ini(_config, "native"))
    return _MemoryInfo(
        max_memory=max_memory,
        allocations=allocations,
        num_stacks=num_stacks,
        native_stacks=native_stacks,
        total_allocated_memory=total_allocated_memory,
    )


def limit_leaks(
    location_limit: str,
    *,
    filter_fn: Optional[LeaksFilterFunction] = None,
    current_thread_only: bool = False,
    _result_file: Path,
    _config: Config,
    _test_id: str,
) -> _LeakedInfo | None:
    reader = FileReader(_result_file)
    allocations: list[AllocationRecord] = [
        record
        for record in reader.get_leaked_allocation_records(
            merge_threads=not current_thread_only
        )
        if not current_thread_only or record.tid == reader.metadata.main_thread_id
    ]

    memory_limit = parse_memory_string(location_limit)

    leaked_allocations = list(
        allocation
        for allocation in allocations
        if (
            allocation.size >= memory_limit
            and _passes_filter(allocation.hybrid_stack_trace(), filter_fn)
        )
    )

    if not leaked_allocations:
        return None

    num_stacks: int = max(cast(int, value_or_ini(_config, "stacks")), 5)
    return _LeakedInfo(
        max_memory=memory_limit,
        allocations=leaked_allocations,
        num_stacks=num_stacks,
        native_stacks=True,
    )


__all__ = [
    "limit_memory",
    "limit_leaks",
    "LeaksFilterFunction",
    "Stack",
    "StackFrame",
]
