"""Tests for object tracking functionality."""

import sys

import pytest

# Skip all tests if Python version is too old
pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 13, 3),
    reason="Object tracking requires Python 3.13.3+",
)


class TestObjectTracking:
    """Test the track_leaked_objects marker."""

    def test_objects_are_tracked_and_reported(self, pytester):
        """Test that leaked objects are detected and reported."""
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.track_leaked_objects
            def test_leak_objects():
                # Create objects that will leak
                leaked_list = [1, 2, 3, 4, 5]
                leaked_dict = {"key": "value", "number": 42}

                # Store them in the test instance to make them survive
                test_leak_objects._leaked = [leaked_list, leaked_dict]
            """
        )

        result = pytester.runpytest("--memray")

        assert result.ret == pytest.ExitCode.TESTS_FAILED
        output = result.stdout.str()

        # Check that the report mentions leaked objects
        assert "Test leaked" in output
        assert "objects" in output
        assert "Object types that leaked" in output
        assert "list" in output
        assert "dict" in output

    def test_no_frames_leak(self, pytester):
        """Test that when no user objects leak, no frames survive either."""
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.track_leaked_objects
            def test_no_leak():
                # Create temporary objects that will be garbage collected
                temp_list = [1, 2, 3]
                temp_dict = {"temp": "value"}

                # Use them but don't keep references
                assert len(temp_list) == 3
                assert "temp" in temp_dict

                # Force garbage collection
                temp_list = None
                temp_dict = None
            """
        )

        result = pytester.runpytest("--memray")
        output = result.stdout.str()
        assert result.ret == 0
        assert "instance(s)" not in output

    def test_complex_object_types(self, pytester):
        """Test tracking of various object types."""
        pytester.makepyfile(
            """
            import pytest

            class CustomClass:
                def __init__(self, value):
                    self.value = value
                def __repr__(self):
                    return f"CustomClass({self.value})"

            @pytest.mark.track_leaked_objects
            def test_various_types():
                # Create various types of objects
                test_various_types._leaks = {
                    "custom": CustomClass(42),
                    "set": {1, 2, 3},
                    "bytes": b"leaked bytes",
                    "tuple": (1, 2, 3),
                    "nested": {
                        "list": [1, [2, 3]],
                        "dict": {"a": {"b": "c"}}
                    }
                }
            """
        )

        result = pytester.runpytest("--memray")

        assert result.ret == pytest.ExitCode.TESTS_FAILED
        output = result.stdout.str()

        assert "CustomClass" in output
        assert "dict" in output

    def test_large_number_of_leaks(self, pytester):
        """Test with many leaked objects."""
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.track_leaked_objects
            def test_many_leaks():
                # Create many objects
                test_many_leaks._leaks = []
                for i in range(100):
                    test_many_leaks._leaks.append({
                        "id": i,
                        "data": f"Object {i}"
                    })
            """
        )

        result = pytester.runpytest("--memray")

        assert result.ret == pytest.ExitCode.TESTS_FAILED
        output = result.stdout.str()

        # Should show summary
        assert "dict" in output
        assert "instance(s)" in output
        assert "... and " in output
        assert " more" in output
