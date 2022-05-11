from .utils import parse_memory_string
from .utils import sizeof_fmt


def limit_memory(limit, *, _allocations):
    "Limit memory used by the test"
    max_memory = parse_memory_string(limit)
    total_allocated_memory = sum(record.size for record in _allocations)
    if total_allocated_memory < max_memory:
        return
    total_memory_str = sizeof_fmt(total_allocated_memory)
    max_memory_str = sizeof_fmt(max_memory)
    text_lines = [f"Test is using {total_memory_str} out of limit of {max_memory_str}"]
    text_lines.append("List of allocations: ")
    for record in _allocations:
        size = record.size
        stack_trace = record.stack_trace()
        if not stack_trace:
            continue
        (function, file, line), *_ = stack_trace
        text_lines.append(f"\t- {function}:{file}:{line} -> {sizeof_fmt(size)}")

    return ("memray-max-memory", "\n".join(text_lines))
