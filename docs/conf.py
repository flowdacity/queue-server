# -*- coding: utf-8 -*-

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
version = "0.1.0"
release = "0.1.0"

exclude_patterns = ["_build"]
pygments_style = "sphinx"

html_theme = "alabaster"
html_theme_path = [alabaster.get_path()]
html_theme_options = {
    "logo": "logo.png",
    "github_user": "flowdacity",
    "github_repo": "flowdacity-queue-server",
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
        "flowdacity-queue-server.tex",
        "Flowdacity Queue Server Documentation",
        "Flowdacity Development Team",
        "manual",
    ),
]

man_pages = [
    (
        "index",
        "flowdacity-queue-server",
        "Flowdacity Queue Server Documentation",
        ["Flowdacity Development Team"],
        1,
    )
]

texinfo_documents = [
    (
        "index",
        "flowdacity-queue-server",
        "Flowdacity Queue Server Documentation",
        "Flowdacity Development Team",
        "flowdacity-queue-server",
        "Async HTTP API for Flowdacity Queue.",
        "Miscellaneous",
    ),
]
