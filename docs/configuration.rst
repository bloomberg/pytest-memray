=============
Configuration
=============

This plugin provides a clean minimal set of command line options that are added to pytest.

Reference
=========

The complete list of command line options is:

.. tab:: Command line options

  ``--memray``
    Activate memray tracking.

  ``--most-allocations=MOST_ALLOCATIONS``
    Show the N tests that allocate most memory (N=0 for all).

  ``--hide-memray-summary``
    Hide the memray summary at the end of the execution.

.. tab:: Config file options

  ``memray(bool)``
    Activate memray tracking.

  ``most-allocations(string)``
    Show the N tests that allocate most memory (N=0 for all).

  ``hide_memray_summary(bool)``
    Hide the memray summary at the end of the execution.

