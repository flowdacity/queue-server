============
Installation
============

Requirements
------------

* Python 3.12+
* Redis 7+
* `uv <https://docs.astral.sh/uv/>`_ (recommended)

Quick setup
-----------

.. code-block:: bash

    uv sync --group dev

This creates the local virtual environment and installs the project with the
development dependencies from ``uv.lock``.

You can run commands without activating the environment:

.. code-block:: bash

    uv run uvicorn asgi:app --host 0.0.0.0 --port 8300

Alternative with pip
--------------------

.. code-block:: bash

    python -m venv .venv
    source .venv/bin/activate
    pip install -e .
    pip install pytest pytest-cov

Next steps
----------

Continue with the `getting started guide <gettingstarted.html>`_ for Redis,
environment variables, and API usage examples.
