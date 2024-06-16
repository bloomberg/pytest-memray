Configuration
=============

This plugin provides a clean minimal set of command line options that are added to pytest.
You can also specify most options in `pytest.ini` file.
The complete list of command line options is:

.. tab:: Command line options

  ``--memray``
    Activate memray tracking.

  ``--most-allocations=MOST_ALLOCATIONS``
    Show the N tests that allocate most memory (N=0 for all).

  ``--hide-memray-summary``
    Hide the memray summary at the end of the execution.

  ``--memray-bin-path``
    Path where to write the memray binary dumps (by default a temporary folder).

  ``--memray-bin-prefix``
    Prefix to use for the binary dump (by default a random UUID4 hex)

  ``--stacks=STACKS``
    Show the N most recent stack entries when showing tracebacks of memory allocations

  ``--native``
    Include native frames when showing tracebacks of memory allocations (will be slower)

  ``--trace-python-allocators``
    Record allocations made by the Pymalloc allocator (will be slower)
  
  ``--fail-on-increase``
    Fail a test with the limit_memory marker if it uses more memory than its last successful run

.. tab:: Config file options

  ``memray(bool)``
    Activate memray tracking.

  ``most_allocations(int)``
    Show the N tests that allocate most memory (N=0 for all, default=5).

  ``hide_memray_summary(bool)``
    Hide the memray summary at the end of the execution.

  ``stacks(int)``
    Show the N most recent stack entries when showing tracebacks of memory allocations

  ``native(bool)``
    Include native frames when showing tracebacks of memory allocations (will be slower)

  ``trace_python_allocators(bool)``
    Record allocations made by the Pymalloc allocator (will be slower)

  ``fail-on-increase(bool)``
    Fail a test with the limit_memory marker if it uses more memory than its last successful run
