# -*- coding: utf-8 -*-

from pathlib import Path
import tomllib

import alabaster

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "alabaster",
]

templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

project = "Flowdacity Queue Server"
copyright = "2025, Flowdacity Development Team"
project_root = Path(__file__).resolve().parents[1]
release = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))[
    "project"
]["version"]
version = release

exclude_patterns = ["_build"]
pygments_style = "sphinx"

html_theme = "alabaster"
html_theme_path = [alabaster.get_path()]
html_theme_options = {
    "logo": "logo.png",
    "github_user": "flowdacity",
    "github_repo": "queue-server",
    "description": "Async HTTP API for Flowdacity Queue",
}

html_static_path = ["_static"]
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "searchbox.html",
    ]
}

htmlhelp_basename = "flowdacityqueueserverdoc"

latex_documents = [
    (
        "index",
        "queue-server.tex",
        "Flowdacity Queue Server Documentation",
        "Flowdacity Development Team",
        "manual",
    ),
]

man_pages = [
    (
        "index",
        "queue-server",
        "Flowdacity Queue Server Documentation",
        ["Flowdacity Development Team"],
        1,
    )
]

texinfo_documents = [
    (
        "index",
        "queue-server",
        "Flowdacity Queue Server Documentation",
        "Flowdacity Development Team",
        "queue-server",
        "Async HTTP API for Flowdacity Queue.",
        "Miscellaneous",
    ),
]
