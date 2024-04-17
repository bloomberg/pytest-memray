Usage
=====

Installation
~~~~~~~~~~~~

This plugin can be installed using pip:


.. code-block:: shell

   pip install pytest-memray


``pytest-memray`` is a pytest plugin. It is enabled when you pass ``--memray`` to
pytest:

.. code-block:: shell

   pytest tests/ --memray

Allocation tracking
~~~~~~~~~~~~~~~~~~~

By default, the plugin will track allocations at the high watermark in all tests. This information is
reported after tests run ends:

.. command-output:: env COLUMNS=92 pytest --memray demo
   :returncode: 1

Markers
~~~~~~~

This plugin provides `markers <https://docs.pytest.org/en/latest/example/markers.html>`__
that can be used to enforce additional checks and validations on tests.


.. py:function:: pytest.mark.limit_memory(memory_limit: str, current_thread_only: bool = False)

    Fail the execution of the test if the test allocates more peak memory than allowed.

    When this marker is applied to a test, it will cause the test to fail if the
    execution of the test allocates more memory (at the peak/high watermark) than allowed.
    It takes a single argument with a string indicating the maximum memory that the test
    can allocate.

    The format for the string is ``<NUMBER> ([KMGTP]B|B)``. The marker will raise
    ``ValueError`` if the string format cannot be parsed correctly.

    If the optional keyword-only argument ``current_thread_only`` is set to *True*, the
    plugin will only track memory allocations made by the current thread and all other
    allocations will be ignored.

    .. warning::

        As the Python interpreter has its own
        `object allocator <https://docs.python.org/3/c-api/memory.html>`__ it's possible
        that memory is not immediately released to the system when objects are deleted,
        so tests using this marker may need to give some room to account for this.

    Example of usage:

    .. code-block:: python

        @pytest.mark.limit_memory("24 MB")
        def test_foobar():
            pass  # do some stuff that allocates memory


.. py:function:: pytest.mark.limit_leaks(location_limit: str, filter_fn: LeaksFilterFunction | None = None, current_thread_only: bool = False)

    Fail the execution of the test if any call stack in the test leaks more memory than
    allowed.

    .. important::
       To detect leaks, Memray needs to intercept calls to the Python allocators and
       report native call frames. This is adds significant overhead, and will slow your
       test down.

    When this marker is applied to a test, the plugin will analyze the memory
    allocations that are made while the test body runs and not freed by the time the
    test body function returns. It groups them by the call stack leading to the
    allocation, and sums the amount leaked by each **distinct call stack**. If the total
    amount leaked from any particular call stack is greater than the configured limit,
    the test will fail.

    .. important::
        It's recommended to run your API or code in a loop when utilizing this plugin.
        This practice helps in distinguishing genuine leaks from the "noise" generated
        by internal caches and other incidental allocations.

    The format for the string is ``<NUMBER> ([KMGTP]B|B)``. The marker will raise
    ``ValueError`` if the string format cannot be parsed correctly.

    The marker also takes an optional keyword-only argument ``filter_fn``. This argument
    represents a filtering function that will be called once for each distinct call
    stack that leaked more memory than allowed. If it returns *True*, leaks from that
    location will be included in the final report. If it returns *False*, leaks
    associated with the stack it was called with will be ignored. If all leaks are
    ignored, the test will not fail. This can be used to discard any known false
    positives.

    If the optional keyword-only argument ``current_thread_only`` is set to *True*, the
    plugin will only track memory allocations made by the current thread and all other
    allocations will be ignored.

    .. tip::

       You can pass the ``--memray-bin-path`` argument to ``pytest`` to specify
       a directory where Memray will store the binary files with the results. You
       can then use the ``memray`` CLI to further investigate the allocations and the
       leaks using any Memray reporters you'd like. Check `the memray docs
       <https://bloomberg.github.io/memray/getting_started.html>`_ for more
       information.

    Example of usage:

    .. code-block:: python

        @pytest.mark.limit_leaks("1 MB")
        def test_foobar():
            # Run the function we're testing in a loop to ensure
            # we can differentiate leaks from memory held by
            # caches inside the Python interpreter.
            for _ in range(100):
                do_some_stuff()

    .. warning::
       It is **very** challenging to write tests that do not "leak" memory in some way,
       due to circumstances beyond your control.

       There are many caches inside the Python interpreter itself. Just a few examples:

       - The `re` module caches compiled regexes.
       - The `logging` module caches whether a given log level is active for
         a particular logger the first time you try to log something at that level.
       - A limited number of objects of certain heavily used types are cached for reuse
         so that `object.__new__` does not always need to allocate memory.
       - The mapping from bytecode index to line number for each Python function is
         cached when it is first needed.

       There are many more such caches. Also, within pytest, any message that you log or
       print is captured, so that it can be included in the output if the test fails.

       Memray sees these all as "leaks", because something was allocated while the test
       ran and it was not freed by the time the test body finished. We don't know that
       it's due to an implementation detail of the interpreter or pytest that the memory
       wasn't freed. Morever, because these caches are implementation details, the
       amount of memory allocated, the call stack of the allocation, and even the
       allocator that was used can all change from one version to another.

       Because of this, you will almost certainly need to allow some small amount of
       leaked memory per call stack, or use the ``filter_fn`` argument to filter out
       false-positive leak reports based on the call stack they're associated with.
