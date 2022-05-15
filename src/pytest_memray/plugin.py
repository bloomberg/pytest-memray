from __future__ import annotations

import collections
import functools
import inspect
import math
import pathlib
import tempfile
import uuid
from dataclasses import dataclass
from itertools import islice
from typing import Any
from typing import Generator
from typing import Iterable
from typing import List
from typing import Tuple
from typing import cast

from _pytest.terminal import TerminalReporter
from memray import AllocationRecord
from memray import FileReader
from memray import Metadata
from memray import Tracker
from pytest import CallInfo
from pytest import CollectReport
from pytest import Config
from pytest import ExitCode
from pytest import Function
from pytest import Item
from pytest import Parser
from pytest import TestReport
from pytest import hookimpl

from .marks import limit_memory
from .utils import sizeof_fmt

MARKERS = {"limit_memory": limit_memory}

N_TOP_ALLOCS = 5
N_HISTOGRAM_BINS = 5


def histogram(
    iterable: Iterable[float], low: float, high: float, bins: int
) -> list[int]:
    """Count elements from the iterable into evenly spaced bins

    >>> scores = [82, 85, 90, 91, 70, 87, 45]
    >>> histogram(scores, 0, 100, 10)
    [0, 0, 0, 0, 1, 0, 0, 1, 3, 2]

    """
    step = ((high - low) / bins) or low
    dist = collections.Counter((x - low) // step for x in iterable)
    return [dist[b] for b in range(bins)]


def cli_hist(data: Iterable[float], bins: int, *, log_scale: bool = True) -> str:
    bars = " ▁▂▃▄▅▆▇█"
    low = min(data)
    high = max(data)
    if log_scale:
        data = map(math.log, filter(lambda number: number != 0, data))
        low = math.log(low)
        high = math.log(high)
    data_bins = histogram(data, low=low, high=high, bins=bins)
    bar_indexes = (int(elem * (len(bars) - 1) / max(data_bins)) for elem in data_bins)
    result = " ".join(bars[bar_index] for bar_index in bar_indexes)
    return result


ResultElement = List[Tuple[object, int]]


@dataclass
class Result:
    metadata: Metadata
    result_file: pathlib.Path


class Manager:
    def __init__(self, config: Config) -> None:
        self.results: dict[str, Result] = {}
        self.config = config
        self.result_path = tempfile.TemporaryDirectory()

    @hookimpl(hookwrapper=True)  # type: ignore[misc] # Untyped decorator
    def pytest_unconfigure(self, config: Config) -> Generator[None, None, None]:
        yield
        self.result_path.cleanup()

    @hookimpl(hookwrapper=True)  # type: ignore[misc] # Untyped decorator
    def pytest_pyfunc_call(self, pyfuncitem: Function) -> object | None:
        testfunction = pyfuncitem.obj

        @functools.wraps(testfunction)
        def wrapper(*args: Any, **kwargs: Any) -> object | None:
            name = f"{uuid.uuid4().hex}.bin"
            result_file = pathlib.Path(self.result_path.name) / name
            with Tracker(result_file):
                result: object | None = testfunction(*args, **kwargs)
            try:
                metadata = FileReader(result_file).metadata
            except OSError:
                return None
            self.results[pyfuncitem.nodeid] = Result(metadata, result_file)
            return result

        pyfuncitem.obj = wrapper

        yield

    @hookimpl(hookwrapper=True)  # type: ignore[misc] # Untyped decorator
    def pytest_runtest_makereport(
        self, item: Item, call: CallInfo[None]
    ) -> Generator[None, TestReport | None, TestReport | None]:
        outcome = yield
        if call.when != "call" or outcome is None:
            return None

        report = outcome.get_result()
        if report.when != "call" or report.outcome != "passed":
            return None

        for marker in item.iter_markers():
            marker_fn = MARKERS.get(marker.name)
            if not marker_fn:
                continue
            result = self.results.get(item.nodeid)
            if not result:
                continue
            reader = FileReader(result.result_file)
            func = reader.get_high_watermark_allocation_records
            allocations = list((func(merge_threads=True)))
            res = marker_fn(*marker.args, **marker.kwargs, _allocations=allocations)
            if res:
                report.outcome = "failed"
                report.longrepr = res.long_repr
                report.sections.append(res.section)
                outcome.force_result(report)
        return None

    @hookimpl(hookwrapper=True, trylast=True)  # type: ignore[misc] # Untyped decorator
    def pytest_report_teststatus(
        self, report: CollectReport | TestReport
    ) -> Generator[None, TestReport, None]:
        outcome = yield
        if report.when != "call" or report.outcome != "failed":
            return None

        if any("memray" in section for section, _ in report.sections):
            outcome.force_result(("failed", "M", "MEMORY PROBLEMS"))
        return None

    @hookimpl  # type: ignore[misc] # Untyped decorator
    def pytest_terminal_summary(
        self, terminalreporter: TerminalReporter, exitstatus: ExitCode
    ) -> None:
        if value_or_ini(self.config, "hide_memray_summary"):
            return

        terminalreporter.write_line("")
        terminalreporter.write_sep("=", "MEMRAY REPORT")

        total_sizes = collections.Counter(
            {
                node_id: result.metadata.peak_memory
                for node_id, result in self.results.items()
                if result.result_file.exists()
            }
        )

        max_results = cast(int, value_or_ini(self.config, "most_allocations"))

        for test_id, total_size in total_sizes.most_common(max_results):
            result = self.results[test_id]
            reader = FileReader(result.result_file)
            func = reader.get_high_watermark_allocation_records
            records = list(func(merge_threads=True))
            if not records:
                continue
            self._report_records_for_test(
                records,
                test_id=test_id,
                metadata=reader.metadata,
                terminalreporter=terminalreporter,
            )

    @staticmethod
    def _report_records_for_test(
        records: Iterable[AllocationRecord],
        test_id: str,
        metadata: Metadata,
        terminalreporter: TerminalReporter,
    ) -> None:
        writeln = terminalreporter.write_line
        writeln(f"Allocations results for {test_id}")
        writeln("")
        writeln(f"\t 📦 Total memory allocated: {sizeof_fmt(metadata.peak_memory)}")
        writeln(f"\t 📏 Total allocations: {metadata.total_allocations}")
        sizes = [allocation.size for allocation in records]
        histogram_txt = cli_hist(sizes, bins=min(len(sizes), N_HISTOGRAM_BINS))
        writeln(f"\t 📊 Histogram of allocation sizes: |{histogram_txt}|")
        writeln("\t 🥇 Biggest allocating functions:")
        sorted_records = sorted(records, key=lambda _record: _record.size, reverse=True)
        for record in islice(sorted_records, N_TOP_ALLOCS):
            stack_trace = record.stack_trace()
            if not stack_trace:
                continue
            (function, file, line), *_ = stack_trace
            writeln(f"\t\t- {function}:{file}:{line} -> {sizeof_fmt(record.size)}")
        writeln("\n")


def pytest_addoption(parser: Parser) -> None:
    group = parser.getgroup("memray")
    group.addoption(
        "--memray",
        action="store_true",
        default=False,
        help="Activate memray tracking",
    )
    group.addoption(
        "--hide-memray-summary",
        action="store_true",
        default=False,
        help="Hide the memray summary at the end of the execution",
    )
    group.addoption(
        "--most-allocations",
        type=int,
        default=5,
        help="Show the N tests that allocate most memory (N=0 for all)",
    )

    parser.addini("memray", "Activate pytest.ini setting", type="bool")
    parser.addini(
        "hide_memray_summary",
        "Hide the memray summary at the end of the execution",
        type="bool",
    )
    parser.addini(
        "most_allocations", "Show the N tests that allocate most memory (N=0 for all)"
    )


def value_or_ini(config: Config, key: str) -> object:
    return config.getvalue(key) or config.getini(key)


def pytest_configure(config: Config) -> None:
    if not value_or_ini(config, "memray"):
        return
    pytest_memray = Manager(config)
    config.pluginmanager.register(pytest_memray, "memray_manager")

    for marker, marker_fn in MARKERS.items():
        [args, *_] = inspect.getfullargspec(marker_fn)
        line = f"{marker}({', '.join(args)}): {marker_fn.__doc__}"
        config.addinivalue_line("markers", line)
