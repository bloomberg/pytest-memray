Release History
===============

.. include:: _draft.rst

.. towncrier release notes start

v1.4.0 (2022-12-02)
-------------------

Features - 1.4.0
~~~~~~~~~~~~~~~~
- Allow to run tests marked with memray markers without having to provide "--memray" in the command line. (:issue:`57`)
- Add two new options that allow to customize the ammount of frames in allocation tracebacks as well as including hybrid stack traces. (:issue:`58`)

Bug Fixes - 1.4.0
~~~~~~~~~~~~~~~~~
- Fix pytest raising ``pytest.PytestReturnNotNoneWarning`` from test decorated with memray markers. (:issue:`60`)


v1.3.2 (2022-11-30)
-------------------

Bug Fixes - 1.3.2
~~~~~~~~~~~~~~~~~
- Make the plugin compatible with ``pytest-xdist``

v1.3.1 (2022-11-14)
-------------------

Bug Fixes - 1.3.1
~~~~~~~~~~~~~~~~~
- Declare 3.11 support
- Fix incompatibility with the ``flaky`` plugin

v1.3.0 (2022-08-21)
-------------------

Features - 1.3.0
~~~~~~~~~~~~~~~~
- Ensure Python 3.11 support - by :user:`gaborbernat`. (:issue:`18`)

v1.2.0 (2022-05-26)
-------------------

Features - 1.2.0
~~~~~~~~~~~~~~~~
- Allow specifying the prefix used for ``-memray-bin-path`` dumps via the
  ``-memray-bin-prefix`` (and if specified and file already exists will be recreated) -
  by :user:`gaborbernat`. (:issue:`28`)

Improved Documentation - 1.2.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Fix documentation links to point from Gitub Pages to readthedocs.org - by :user:`gaborbernat`. (:issue:`12`)
- Update examples in configuration and add ``-memray-bin-path`` - by :user:`gaborbernat`. (:issue:`26`)
- Fix minimum python version in documentation from 3.7 to 3.8 - by :user:`ChaoticRoman`. (:issue:`30`)

v1.1.0 (2022-05-17)
-------------------

Features - 1.1.0
~~~~~~~~~~~~~~~~
- Report memory limit and allocated memory in longrepr - by :user:`petr-tik`. (:issue:`5`)
- Allow passing ``--memray-bin-path`` argument to the CLI to allow
  persisting the binary dumps - by :user:`gaborbernat`. (:issue:`10`)
- Release a pure python wheel - by :user:`gaborbernat`. (:issue:`11`)
- Switch build backend from ``setuptools`` to ``hatchling`` - by :user:`gaborbernat`. (:issue:`12`)

Bug Fixes - 1.1.0
~~~~~~~~~~~~~~~~~
- Causes built-in junit-xml results writer to fail - by :user:`petr-tik`. (:issue:`3`)

Improved Documentation - 1.1.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Move documentation from Github Pages to readthedocs - by :user:`gaborbernat`. (:issue:`20`)


v1.0.0 (2022-04-09)
-------------------

-  Initial release.
