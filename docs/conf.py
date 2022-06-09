"""Sphinx configuration file for pytest-memray documentation."""
from __future__ import annotations

import sys
from pathlib import Path
from subprocess import check_output

from sphinx.application import Sphinx
from sphinxcontrib.programoutput import Command

extensions = [
    "sphinx.ext.extlinks",
    "sphinx.ext.githubpages",
    "sphinxarg.ext",
    "sphinx_inline_tabs",
    "sphinxcontrib.programoutput",
]
exclude_patterns = ["_build", "news/*", "_draft.rst"]
project = "pytest-memray"
author = "Pablo Galindo Salgado"
html_title = project
html_theme = "furo"
html_static_path = ["_static"]
html_logo = "_static/images/logo.png"
html_theme_options = {
    "sidebar_hide_name": True,
}
extlinks = {
    "user": ("https://github.com/%s", "@%s"),
    "issue": ("https://github.com/bloomberg/pytest-memray/issue/%s", "#%s"),
}
programoutput_prompt_template = "$ pytest --memray /w/demo \n{output}"
prev = Command.get_output
here = Path(__file__).parent


def _get_output(self):
    code, out = prev(self)
    out = out.replace(str(Path(sys.executable).parents[1]), "/v")
    out = out.replace(str(here), "/w")
    return code, out


Command.get_output = _get_output


def setup(app: Sphinx) -> None:
    here = Path(__file__).parent
    root, exe = here.parent, Path(sys.executable)
    towncrier = exe.with_name(f"towncrier{exe.suffix}")
    cmd = [str(towncrier), "build", "--draft", "--version", "NEXT"]
    new = check_output(cmd, cwd=root, text=True)
    to = root / "docs" / "_draft.rst"
    to.write_text("" if "No significant changes" in new else new)
