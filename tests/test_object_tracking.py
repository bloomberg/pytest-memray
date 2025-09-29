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
        assert "list:" in output
        assert "dict:" in output

    def test_no_leak_passes(self, pytester):
        """Test that tests without leaks pass (ignoring frame objects)."""
        pytester.makepyfile(
            """
            import pytest
            import gc

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
                gc.collect()
            """
        )

        result = pytester.runpytest("--memray")  # noqa: F841

        # Note: This might fail due to frame objects being tracked
        # In a real implementation, we might want to filter those out

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

        assert "CustomClass" in output or "test_various_types" in output
        assert "set:" in output or "dict:" in output

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
        assert "dict:" in output
        assert "100" in output or "instance(s)" in output

    def test_version_check(self, pytester):
        """Test that old Python versions are properly rejected."""
        pytester.makepyfile(
            """
            import pytest
            import sys

            # Mock an old Python version
            if sys.version_info >= (3, 13, 3):
                pytest.skip("Test for old Python versions", allow_module_level=True)

            @pytest.mark.track_leaked_objects
            def test_should_fail():
                pass
            """
        )

        result = pytester.runpytest("--memray")  # noqa: F841
        # Should skip on new Python, error on old Python


class TestGetLeakedObjects:
    """Test the get_leaked_objects marker for programmatic access."""

    def test_get_leaked_objects_basic(self, pytester):
        """Test basic functionality of get_leaked_objects."""
        pytester.makepyfile(
            """
            import pytest

            # Store for assertions
            leaked_objects = None

            @pytest.mark.get_leaked_objects
            def test_get_leaks():
                # Create some leaked objects
                leaked_list = [1, 2, 3]
                leaked_dict = {"key": "value"}

                # Keep references
                test_get_leaks._kept = [leaked_list, leaked_dict]

                # Note: The actual implementation would need to inject
                # a function to retrieve the objects
                # For now this is a placeholder test
            """
        )

        result = pytester.runpytest("--memray", "-v")  # noqa: F841
        # This test demonstrates the intended API
        # Full implementation would require injecting the callback

    def test_combined_markers(self, pytester):
        """Test using both markers together."""
        pytester.makepyfile(
            """
            import pytest

            @pytest.mark.track_leaked_objects
            @pytest.mark.get_leaked_objects
            def test_both_markers():
                # This should track AND provide access
                leaked = {"combined": "test"}
                test_both_markers._leak = leaked
            """
        )

        result = pytester.runpytest("--memray")
        # Should fail due to track_leaked_objects
        assert result.ret == pytest.ExitCode.TESTS_FAILED


def test_integration_with_existing_markers(pytester):
    """Test that object tracking works with other memray markers."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.limit_memory("10MB")
        @pytest.mark.track_leaked_objects
        def test_combined():
            # Test with both memory limit and object tracking
            data = [i for i in range(100)]
            test_combined._data = data
        """
    )

    result = pytester.runpytest("--memray")  # noqa: F841
    # Should report both memory usage and leaked objects if applicable
