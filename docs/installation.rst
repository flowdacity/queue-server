============
Installation
============

Requirements
------------

* Python 3.12+
* Redis 7+

Install with uv
---------------

::

    uv sync --group dev

This project currently pins ``flowdacity-queue`` to the upstream ``v1.0.0`` Git tag.

Install with pip
----------------

::

    python -m venv .venv
    source .venv/bin/activate
    pip install -e .
    pip install pytest pytest-cov

Next steps
----------

Continue with the `getting started guide <gettingstarted.html>`_ to run Redis,
set environment variables, and start the server.
