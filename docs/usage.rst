=====
Usage
=====

``pytest-memray`` is a pytest plugin. It is enabled when you pass
``--memray`` to pytest::

    $ python3.9 -m pytest tests/ --memray

Allocation tracking
===================

By default, the plugin will track allocations in all tests. This information is
reported after tests run ends::

.. example report starts

.. code-block:: console

    $ python3 -m pytest tests --memray
    =============================== test session starts ================================
    platform linux -- Python 3.8.10, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
    rootdir: /mypackage, configfile: pytest.ini
    plugins: cov-2.12.0, memray-0.1.0
    collected 21 items

    tests/test_package.py .....................                                   [100%]


    ================================= MEMRAY REPORT ==================================
    Allocations results for tests/test_package.py::some_test_that_allocates

         📦 Total memory allocated: 24.4MiB
         📏 Total allocations: 33929
         📊 Histogram of allocation sizes: |▂   █    |
         🥇 Biggest allocating functions:
            - parse:/opt/bb/lib/python3.8/ast.py:47 -> 3.0MiB
            - parse:/opt/bb/lib/python3.8/ast.py:47 -> 2.3MiB
            - _visit:/opt/bb/lib/python3.8/site-packages/astroid/transforms.py:62 -> 576.0KiB
            - parse:/opt/bb/lib/python3.8/ast.py:47 -> 517.6KiB
            - __init__:/opt/bb/lib/python3.8/site-packages/astroid/node_classes.py:1353 -> 512.0KiB

.. example report ends

Markers
=======

This plugin provides markers that can be used to enforce additional checks and
validations on tests when this plugin is enabled.

.. important:: These markers do nothing when the plugin is not enabled.


``limit_memory``
----------------

When this marker is applied to a test, it will cause the test to fail if
the execution of the test allocates more memory than allowed. It takes a single
argument with a string indicating the maximum memory that the test can allocate.

The format for the string is ``<NUMBER> ([KMGTP]B|B)``. The marker will raise
``ValueError`` if the string format cannot be parsed correctly.

.. warning::

    As the Python interpreter has its own `object allocator <https://docs.python.org/3/c-api/memory.html>`__
    is possible that memory is not immediately released to the system when objects are deleted, so tests
    using this marker may need to give some room to account for this.

Example of usage:

.. code-block:: python

    @pytest.mark.limit_memory("24 MB")
    def test_foobar():
        # do some stuff that allocates memory


Fixtures
========

None provided at this time.
