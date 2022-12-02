from __future__ import annotations

import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import ANY
from unittest.mock import patch

import pytest
from memray import Tracker
from pytest import ExitCode
from pytest import Pytester


def test_help_message(pytester: Pytester) -> None:
    result = pytester.runpytest("--help")
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "memray:",
            "*--memray*Activate memray tracking",
            "*memray (bool)*",
        ]
    )


def test_memray_is_called_when_activated(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        def test_hello_world():
            assert 2 == 1 + 1
    """
    )

    with patch("pytest_memray.plugin.Tracker") as mock:
        result = pytester.runpytest("--memray")

    mock.assert_called_once()
    assert result.ret == ExitCode.OK


def test_memray_is_not_called_when_not_activated(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        def test_hello_world():
            assert 2 == 1 + 1
    """
    )

    with patch("pytest_memray.plugin.Tracker") as mock:
        result = pytester.runpytest()

    mock.assert_not_called()
    assert result.ret == ExitCode.OK


@pytest.mark.parametrize(
    "size, outcome",
    [
        (1024 * 5, ExitCode.TESTS_FAILED),
        (1024 * 2, ExitCode.TESTS_FAILED),
        (1024 * 2 - 1, ExitCode.OK),
        (1024 * 1, ExitCode.OK),
    ],
)
def test_limit_memory_marker(pytester: Pytester, size: int, outcome: ExitCode) -> None:
    pytester.makepyfile(
        f"""
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        @pytest.mark.limit_memory("2KB")
        def test_memory_alloc_fails():
            allocator.valloc({size})
            allocator.free()
        """
    )

    result = pytester.runpytest("--memray")

    assert result.ret == outcome


def test_limit_memory_marker_does_work_if_memray_not_passed(
    pytester: Pytester,
) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        @pytest.mark.limit_memory("2KB")
        def test_memory_alloc_fails():
            allocator.valloc(4*1024)
            allocator.free()
        """
    )

    result = pytester.runpytest()

    assert result.ret == ExitCode.TESTS_FAILED


@pytest.mark.parametrize(
    "memlimit, mem_to_alloc",
    [(5, 100), (10, 200)],
)
def test_memray_with_junit_xml_error_msg(
    pytester: Pytester, memlimit: int, mem_to_alloc: int
):
    xml_output_file = pytester.makefile(".xml", "")
    pytester.makepyfile(
        f"""
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        @pytest.mark.limit_memory("{memlimit}B")
        def test_memory_alloc_fails():
            allocator.valloc({mem_to_alloc})
            allocator.free()
        """
    )
    result = pytester.runpytest("--memray", "--junit-xml", xml_output_file)
    assert result.ret == ExitCode.TESTS_FAILED

    expected = f"Test was limited to {memlimit}.0B but allocated {mem_to_alloc}.0B"
    root = ET.parse(str(xml_output_file)).getroot()
    for testcase in root.iter("testcase"):
        failure = testcase.find("failure")
        assert expected in failure.text


def test_memray_with_junit_xml(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        @pytest.mark.limit_memory("1B")
        def test_memory_alloc_fails():
            allocator.valloc(1234)
            allocator.free()
        """
    )
    path = str(pytester.path / "blech.xml")
    result = pytester.runpytest("--memray", "--junit-xml", path)
    assert result.ret == ExitCode.TESTS_FAILED


@pytest.mark.parametrize("num_stacks", [1, 5, 100])
def test_memray_report_limit_number_stacks(num_stacks: int, pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        def rec(n):
            if n <= 1:
                allocator.valloc(1024*2)
                allocator.free()
                return None
            return rec(n - 1)


        @pytest.mark.limit_memory("1kb")
        def test_foo():
            rec(10)
    """
    )

    result = pytester.runpytest("--memray", f"--stacks={num_stacks}")

    assert result.ret == ExitCode.TESTS_FAILED

    output = result.stdout.str()

    assert "valloc:" in output
    assert output.count("rec:") == min(num_stacks - 1, 10)


@pytest.mark.parametrize("native", [True, False])
def test_memray_report_native(native: bool, pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        @pytest.mark.limit_memory("1kb")
        def test_foo():
            allocator.valloc(1024*2)
            allocator.free()
    """
    )

    with patch("pytest_memray.plugin.Tracker", wraps=Tracker) as mock:
        result = pytester.runpytest("--memray", *(["--native"] if native else []))

    assert result.ret == ExitCode.TESTS_FAILED

    output = result.stdout.str()
    mock.assert_called_once_with(ANY, native_traces=native)

    if native:
        assert "MemoryAllocator_1" in output
    else:
        assert "MemoryAllocator_1" not in output


def test_memray_report(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        def allocating_func1():
            allocator.valloc(1024)
            allocator.free()

        def allocating_func2():
            allocator.valloc(1024*2)
            allocator.free()

        def test_foo():
            allocating_func1()

        def test_bar():
            allocating_func2()
        """
    )

    result = pytester.runpytest("--memray")

    assert result.ret == ExitCode.OK

    output = result.stdout.str()

    assert "MEMRAY REPORT" in output

    assert "results for test_memray_report.py::test_foo" in output
    assert "Total memory allocated: 2.0KiB" in output
    assert "valloc:" in output
    assert "-> 2.0KiB" in output

    assert "results for test_memray_report.py::test_bar" in output
    assert "Total memory allocated: 1.0KiB" in output
    assert "valloc:" in output
    assert "-> 1.0KiB" in output


def test_memray_report_is_not_shown_if_deactivated(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        def allocating_func1():
            allocator.valloc(1024)
            allocator.free()

        def allocating_func2():
            allocator.valloc(1024*2)
            allocator.free()

        def test_foo():
            allocating_func1()

        def test_bar():
            allocating_func2()
        """
    )

    result = pytester.runpytest("--memray", "--hide-memray-summary")

    assert result.ret == ExitCode.OK

    output = result.stdout.str()

    assert "MEMRAY REPORT" not in output

    assert "results for test_memray_report.py::test_foo" not in output
    assert "Total memory allocated: 2.0KiB" not in output
    assert "valloc:" not in output
    assert "-> 2.0KiB" not in output

    assert "results for test_memray_report.py::test_bar" not in output
    assert "Total memory allocated: 1.0KiB" not in output
    assert "valloc:" not in output
    assert "-> 1.0KiB" not in output


def test_memray_report_limit(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        def allocating_func1():
            allocator.valloc(1024)
            allocator.free()

        def allocating_func2():
            allocator.valloc(1024*2)
            allocator.free()

        def test_foo():
            allocating_func1()

        def test_bar():
            allocating_func2()
    """
    )

    result = pytester.runpytest("--memray", "--most-allocations=1")

    assert result.ret == ExitCode.OK

    output = result.stdout.str()

    assert "results for test_memray_report_limit.py::test_foo" not in output
    assert "results for test_memray_report_limit.py::test_bar" in output


def test_failing_tests_are_not_reported(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        def allocating_func1():
            allocator.valloc(1024)
            allocator.free()

        def allocating_func2():
            allocator.valloc(1024*2)
            allocator.free()

        def test_foo():
            allocating_func1()

        def test_bar():
            allocating_func2()
            1/0
        """
    )

    result = pytester.runpytest("--memray")

    assert result.ret == ExitCode.TESTS_FAILED

    output = result.stdout.str()

    assert "results for test_failing_tests_are_not_reported.py::test_foo" in output
    assert "results for test_failing_tests_are_not_reported.py::test_bar" not in output


def test_plugin_calls_tests_only_once(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        counter = 0
        def test_hello_world():
            global counter
            counter += 1
            assert counter < 2
        """
    )

    with patch("pytest_memray.plugin.Tracker") as mock:
        result = pytester.runpytest("--memray")

    mock.assert_called_once()
    assert result.ret == ExitCode.OK


def test_bin_path(pytester: Pytester) -> None:
    py = """
    import pytest

    def test_a():
        assert [1]
    @pytest.mark.parametrize('i', [1, 2])
    def test_b(i):
        assert [2] * i
    """
    pytester.makepyfile(**{"magic/test_a": py})
    dump = pytester.path / "d"
    with patch("uuid.uuid4", return_value=SimpleNamespace(hex="H")) as mock:
        result = pytester.runpytest("--memray", "--memray-bin-path", str(dump))

    assert result.ret == ExitCode.OK
    mock.assert_called_once()

    assert dump.exists()
    assert {i.name for i in dump.iterdir()} == {
        "H-magic-test_a.py-test_b[2].bin",
        "H-magic-test_a.py-test_a.bin",
        "H-magic-test_a.py-test_b[1].bin",
        "metadata",
    }

    output = result.stdout.str()
    assert f"Created 3 binary dumps at {dump} with prefix H" in output


@pytest.mark.parametrize("override", [True, False])
def test_bin_path_prefix(pytester: Pytester, override: bool) -> None:
    py = """
    import pytest
    def test_t():
        assert [1]
    """
    pytester.makepyfile(test_a=py)

    bin_path = pytester.path / "p-test_a.py-test_t.bin"
    if override:
        bin_path.write_bytes(b"")

    args = ["--memray", "--memray-bin-path", str(pytester.path)]
    args.extend(["--memray-bin-prefix", "p"])
    result = pytester.runpytest(*args)
    res = list(pytester.path.iterdir())

    assert res

    assert result.ret == ExitCode.OK
    assert bin_path.exists()


def test_plugin_works_with_the_flaky_plugin(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        from flaky import flaky

        @flaky
        def test_hello_world():
            1/0
        """
    )

    with patch("pytest_memray.plugin.Tracker") as mock:
        result = pytester.runpytest("--memray")

    # Ensure that flaky has only called our Tracker once per retry (2 times)
    # and not more times because it has incorrectly wrapped our plugin and
    # called it multiple times per retry.
    assert mock.call_count == 2
    assert result.ret == ExitCode.TESTS_FAILED


def test_memray_report_with_pytest_xdist(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        def allocating_func1():
            allocator.valloc(1024)
            allocator.free()

        def allocating_func2():
            allocator.valloc(1024*2)
            allocator.free()

        def test_foo():
            allocating_func1()

        def test_bar():
            allocating_func2()
        """
    )

    result = pytester.runpytest("--memray", "-n", "2")

    assert result.ret == ExitCode.OK

    output = result.stdout.str()

    assert "MEMRAY REPORT" in output

    # We don't check the exact number of memory allocated because pytest-xdist
    # can spawn some threads using the `execnet` library which can allocate extra
    # memory.
    assert "Total memory allocated:" in output

    assert "results for test_memray_report_with_pytest_xdist.py::test_foo" in output
    assert "valloc:" in output
    assert "-> 2.0KiB" in output

    assert "results for test_memray_report_with_pytest_xdist.py::test_bar" in output
    assert "valloc:" in output
    assert "-> 1.0KiB" in output


@pytest.mark.parametrize(
    "size, outcome",
    [
        (1024 * 5, ExitCode.TESTS_FAILED),
        (1024 * 2, ExitCode.TESTS_FAILED),
        (1024 * 2 - 1, ExitCode.OK),
        (1024 * 1, ExitCode.OK),
    ],
)
def test_limit_memory_marker_with_pytest_xdist(
    pytester: Pytester, size: int, outcome: ExitCode
) -> None:
    pytester.makepyfile(
        f"""
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        @pytest.mark.limit_memory("2KB")
        def test_memory_alloc_fails():
            allocator.valloc({size})
            allocator.free()

        @pytest.mark.limit_memory("2KB")
        def test_memory_alloc_fails_2():
            allocator.valloc({size})
            allocator.free()
        """
    )

    result = pytester.runpytest("--memray", "-n", "2")
    assert result.ret == outcome


def test_memray_does_not_raise_warnings(pytester: Pytester) -> None:
    pytester.makepyfile(
        """
        import pytest
        from memray._test import MemoryAllocator
        allocator = MemoryAllocator()

        @pytest.mark.limit_memory("1MB")
        def test_memory_alloc_fails():
            allocator.valloc(1234)
            allocator.free()
        """
    )
    result = pytester.runpytest("-Werror", "--memray")
    assert result.ret == ExitCode.OK
