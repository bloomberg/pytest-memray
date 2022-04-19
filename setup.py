#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib

from setuptools import find_namespace_packages
from setuptools import setup

install_requires = [
    "pytest>=3.5.0",
    "memray",
]
docs_requires = [
    "bump2version",
    "furo",
    "sphinx",
    "sphinx-argparse",
    "sphinx-inline-tabs",
    "towncrier",
]

lint_requires = [
    "black",
    "flake8",
    "isort",
    "mypy",
    "check-manifest",
]

test_requires = [
    "pytest",
    "coverage",
]

about = {}
with open("src/pytest_memray/_version.py") as fp:
    exec(fp.read(), about)

HERE = pathlib.Path(__file__).parent.resolve()
LONG_DESCRIPTION = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="pytest-memray",
    url="https://github.com/bloomberg/pytest-memray",
    version=about["__version__"],
    author="Pablo Galindo Salgado",
    author_email="pgalindo3@bloomberg.net",
    maintainer="Pablo Galindo Salgado",
    maintainer_email="pgalindo3@bloomberg.net",
    license="Apache 2.0",
    description="A simple plugin to use with pytest",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Debuggers",
    ],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "test": test_requires,
        "docs": docs_requires,
        "lint": lint_requires,
        "dev": test_requires + lint_requires + docs_requires,
    },
    entry_points={
        "pytest11": [
            "memray = pytest_memray.plugin",
        ],
    },
)
