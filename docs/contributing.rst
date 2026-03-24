============
Contributing
============

Flowdacity Queue Server is open source and released under the permissive
`MIT License <license.html>`_. Issues and pull requests are welcome.

Repositories
------------

Development is split across two repositories:

1. Flowdacity Queue Server: https://github.com/flowdacity/flowdacity-queue-server
2. Flowdacity Queue core: https://github.com/flowdacity/flowdacity-queue

Local workflow
--------------

1. Install dependencies with ``uv sync --group dev``.
2. Start Redis with ``make redis-up``.
3. Run tests with ``make test``.
4. Update docs and tests when behavior changes.

What to include in a change
---------------------------

* Tests for new behavior or regressions.
* Documentation updates for API or configuration changes.
* Clear reproduction details when reporting a bug.
