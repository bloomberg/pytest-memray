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

By default, the plugin will track allocations in all tests. This information is
reported after tests run ends:

.. command-output:: env COLUMNS=92 pytest --memray demo
   :returncode: 1

Markers
~~~~~~~

This plugin provides markers that can be used to enforce additional checks and
validations on tests when this plugin is enabled.

.. important:: These markers do nothing when the plugin is not enabled.


``limit_memory``
----------------

When this marker is applied to a test, it will cause the test to fail if the execution
of the test allocates more memory than allowed. It takes a single argument with a
string indicating the maximum memory that the test can allocate.

The format for the string is ``<NUMBER> ([KMGTP]B|B)``. The marker will raise
``ValueError`` if the string format cannot be parsed correctly.

.. warning::

    As the Python interpreter has its own
    `object allocator <https://docs.python.org/3/c-api/memory.html>`__ is possible
    that memory is not immediately released to the system when objects are deleted, so
    tests using this marker may need to give some room to account for this.

Example of usage:

.. code-block:: python

    @pytest.mark.limit_memory("24 MB")
    def test_foobar():
        pass # do some stuff that allocates memory
