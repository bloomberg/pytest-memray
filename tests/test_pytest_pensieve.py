import xml.etree.ElementTree as ET
from unittest.mock import patch

import pytest
from pytest import ExitCode


def test_help_message(testdir):
    result = testdir.runpytest(
        "--help",
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "memray:",
            "*--memray*Activate memray tracking",
            "*memray (bool)*",
        ]
    )


def test_memray_is_called_when_activated(testdir):
    testdir.makepyfile(
        """
        def test_hello_world():
            assert 2 == 1 + 1
    """
    )

    with patch("pytest_memray.plugin.Tracker") as mock:
        result = testdir.runpytest("--memray")

    mock.assert_called_once()
    assert result.ret == ExitCode.OK


def test_memray_is_not_called_when_not_activated(testdir):
    testdir.makepyfile(
        """
        def test_hello_world():
            assert 2 == 1 + 1
    """
    )

    with patch("pytest_memray.plugin.Tracker") as mock:
        result = testdir.runpytest()

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
def test_limit_memory_marker(testdir, size, outcome):
    testdir.makepyfile(
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

    result = testdir.runpytest("--memray")

    assert result.ret == outcome


def test_limit_memory_marker_doesn_not_work_if_memray_inactive(testdir):
    testdir.makepyfile(
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

    result = testdir.runpytest()

    assert result.ret == ExitCode.OK


@pytest.mark.parametrize(
    "memlimit, mem_to_alloc",
    [(5, 100), (10, 200)],
)
def test_memray_with_junit_xml_error_msg(testdir, memlimit, mem_to_alloc):
    xml_output_file = testdir.makefile(".xml", "")
    testdir.makepyfile(
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
    result = testdir.runpytest("--memray", "--junit-xml", xml_output_file)
    assert result.ret == ExitCode.TESTS_FAILED

    root = ET.parse(str(xml_output_file)).getroot()
    for testcase in root.iter("testcase"):
        failure = testcase.find("failure")
        assert (
            f"""Test was limited to {memlimit}.0B but allocated {mem_to_alloc}.0B"""
            in failure.text
        )


def test_memray_with_junit_xml(testdir):
    testdir.makepyfile(
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

    result = testdir.runpytest(
        "--memray", "--junit-xml", str(testdir.tmpdir / "blech.xml")
    )
    assert result.ret == ExitCode.TESTS_FAILED


def test_memray_report(testdir):
    testdir.makepyfile(
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

    result = testdir.runpytest("--memray")

    assert result.ret == ExitCode.OK

    output = result.stdout.str()

    assert "MEMRAY REPORT" in output

    assert "results for test_memray_report.py::test_foo" in output
    assert "Total memory allocated: 2.0KiB" in output
    assert "valloc:src/memray/_memray_test_utils.pyx" in output
    assert "-> 2.0KiB" in output

    assert "results for test_memray_report.py::test_bar" in output
    assert "Total memory allocated: 1.0KiB" in output
    assert "valloc:src/memray/_memray_test_utils.pyx" in output
    assert "-> 1.0KiB" in output


def test_memray_report_is_not_shown_if_deactivated(testdir):
    testdir.makepyfile(
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

    result = testdir.runpytest("--memray", "--hide-memray-summary")

    assert result.ret == ExitCode.OK

    output = result.stdout.str()

    assert "MEMRAY REPORT" not in output

    assert "results for test_memray_report.py::test_foo" not in output
    assert "Total memory allocated: 2.0KiB" not in output
    assert "valloc:src/memray/_memray.pyx" not in output
    assert "-> 2.0KiB" not in output

    assert "results for test_memray_report.py::test_bar" not in output
    assert "Total memory allocated: 1.0KiB" not in output
    assert "valloc:src/memray/_memray.pyx" not in output
    assert "-> 1.0KiB" not in output


def test_memray_report_limit(testdir):
    testdir.makepyfile(
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

    result = testdir.runpytest("--memray", "--most-allocations=1")

    assert result.ret == ExitCode.OK

    output = result.stdout.str()

    assert "results for test_memray_report_limit.py::test_foo" not in output
    assert "results for test_memray_report_limit.py::test_bar" in output


def test_failing_tests_are_not_reported(testdir):
    testdir.makepyfile(
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

    result = testdir.runpytest("--memray")

    assert result.ret == ExitCode.TESTS_FAILED

    output = result.stdout.str()

    assert "results for test_failing_tests_are_not_reported.py::test_foo" in output
    assert "results for test_failing_tests_are_not_reported.py::test_bar" not in output


def test_plugin_calls_tests_only_once(testdir):
    testdir.makepyfile(
        """
        counter = 0
        def test_hello_world():
            global counter
            counter += 1
            assert counter < 2
    """
    )

    with patch("pytest_memray.plugin.Tracker") as mock:
        result = testdir.runpytest("--memray")

    mock.assert_called_once()
    assert result.ret == ExitCode.OK
