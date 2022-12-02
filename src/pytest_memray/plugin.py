from __future__ import annotations

import collections
import functools
import inspect
import math
import os
import pickle
import uuid
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from tempfile import TemporaryDirectory
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
from .utils import WriteEnabledDirectoryAction
from .utils import positive_int
from .utils import sizeof_fmt
from .utils import value_or_ini

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
    test_id: str
    metadata: Metadata
    result_file: Path


class Manager:
    def __init__(self, config: Config) -> None:
        self.results: dict[str, Result] = {}
        self.config = config
        path: Path | None = config.getvalue("memray_bin_path")
        self._tmp_dir: None | TemporaryDirectory[str] = None
        if path is None:
            # Check the MEMRAY_RESULT_PAtH environment variable. If this
            # is set, it means that we are running in a worker and the main
            # process has set it so we'll use it as the directory to store
            # the results.
            result_path = os.getenv("MEMRAY_RESULT_PATH")
            if not result_path:
                # We are not running in a worker, so we'll create a temporary
                # directory to store the results. Other possible workers will
                # use this directory by reading the MEMRAY_RESULT_PATH environment
                # variable.
                self._tmp_dir = TemporaryDirectory()
                os.environ["MEMRAY_RESULT_PATH"] = self._tmp_dir.name
                result_path = self._tmp_dir.name
            self.result_path: Path = Path(result_path)
        else:
            self._tmp_dir = None
            self.result_path = path
        self._bin_prefix = config.getvalue("memray_bin_prefix") or uuid.uuid4().hex
        self.result_metadata_path = self.result_path / "metadata"
        self.result_metadata_path.mkdir(exist_ok=True, parents=True)

    @hookimpl(hookwrapper=True)  # type: ignore[misc] # Untyped decorator
    def pytest_unconfigure(self, config: Config) -> Generator[None, None, None]:
        yield
        if self._tmp_dir is not None:
            self._tmp_dir.cleanup()
        if os.environ.get("MEMRAY_RESULT_PATH"):
            del os.environ["MEMRAY_RESULT_PATH"]

    @hookimpl(hookwrapper=True)  # type: ignore[misc] # Untyped decorator
    def pytest_pyfunc_call(self, pyfuncitem: Function) -> object | None:
        func = pyfuncitem.obj

        markers = {
            marker.name
            for marker in pyfuncitem.iter_markers()
            if marker.name in MARKERS
        }

        if not markers and not value_or_ini(self.config, "memray"):
            yield
            return

        def _build_bin_path() -> Path:
            if self._tmp_dir is None:
                of_id = pyfuncitem.nodeid.replace("::", "-")
                of_id = of_id.replace(os.sep, "-")
                name = f"{self._bin_prefix}-{of_id}.bin"
            else:
                name = f"{uuid.uuid4().hex}.bin"
            result_file = self.result_path / name
            if self._tmp_dir is None and result_file.exists():
                result_file.unlink()
            return result_file

        native: bool = bool(value_or_ini(self.config, "native"))

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> object | None:
            test_result: object | Any = None
            try:
                result_file = _build_bin_path()
                with Tracker(result_file, native_traces=native):
                    test_result = func(*args, **kwargs)
                try:
                    metadata = FileReader(result_file).metadata
                except OSError:
                    return None
                result = Result(pyfuncitem.nodeid, metadata, result_file)
                metadata_path = (
                    self.result_metadata_path
                    / result_file.with_suffix(".metadata").name
                )
                with open(metadata_path, "wb") as file_handler:
                    pickle.dump(result, file_handler)
                self.results[pyfuncitem.nodeid] = result
            finally:
                # Restore the original function. This is needed because some
                # pytest plugins (e.g. flaky) will call our pytest_pyfunc_call
                # hook again with whatever is here, which will cause the wrapper
                # to be wrapped again.
                pyfuncitem.obj = func
            return test_result

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
            res = marker_fn(
                *marker.args,
                **marker.kwargs,
                _allocations=allocations,
                _config=self.config,
            )
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
        if value_or_ini(self.config, "hide_memray_summary") or not value_or_ini(
            self.config, "memray"
        ):
            return

        terminalreporter.write_line("")
        terminalreporter.write_sep("=", "MEMRAY REPORT")

        if not self.results:
            # If there are not results is because we are likely running under
            # pytest-xdist, and the master process is not running the tests.  In
            # this case, we can retrieve the results from the metadata directory
            # instead, that is common for all workers.
            for result_file in self.result_metadata_path.glob("*.metadata"):
                result = pickle.loads(result_file.read_bytes())
                self.results[result.test_id] = result

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
        if self._tmp_dir is None:
            msg = f"Created {len(total_sizes)} binary dumps at {self.result_path}"
            msg += f" with prefix {self._bin_prefix}"
            terminalreporter.write_line(msg)

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
        "--memray-bin-path",
        action=WriteEnabledDirectoryAction,
        default=None,
        help="Path where to write the memray binary dumps (by default a temporary folder)",
    )
    group.addoption(
        "--memray-bin-prefix",
        default=None,
        help="Prefix to use for the binary dump (by default a random UUID4 hex)",
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
    group.addoption(
        "--stacks",
        type=positive_int,
        default=1,
        help="Show the N stack entries when showing tracebacks of memory allocations",
    )
    group.addoption(
        "--native",
        action="store_true",
        default=False,
        help="Show native frames when showing tracebacks of memory allocations "
        "(will be slower)",
    )

    parser.addini("memray", "Activate pytest.ini setting", type="bool")
    parser.addini(
        "hide_memray_summary",
        "Hide the memray summary at the end of the execution",
        type="bool",
    )
    parser.addini(
        "stacks",
        help="Show the N stack entries when showing tracebacks of memory allocations",
        type="string",
    )
    parser.addini(
        "native",
        help="Show native frames when showing tracebacks of memory allocations "
        "(will be slower)",
        type="bool",
    )
    help_msg = "Show the N tests that allocate most memory (N=0 for all)"
    parser.addini("most_allocations", help_msg)


def pytest_configure(config: Config) -> None:
    pytest_memray = Manager(config)
    config.pluginmanager.register(pytest_memray, "memray_manager")

    for marker, marker_fn in MARKERS.items():
        [args, *_] = inspect.getfullargspec(marker_fn)
        line = f"{marker}({', '.join(args)}): {marker_fn.__doc__}"
        config.addinivalue_line("markers", line)
