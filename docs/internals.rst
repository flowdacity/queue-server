=============
The Internals
=============

Flowdacity Queue Server has two main layers:

* The `Flowdacity Queue core <https://github.com/flowdacity/flowdacity-queue>`_,
  which manages queue state in Redis and executes Lua scripts for queue operations.
* The HTTP server in this repository, which maps REST endpoints to FQ operations,
  loads configuration from environment variables, and runs the background requeue loop.

Architecture
------------

1. A request reaches the Starlette app in ``fq_server.server``.
2. The handler validates the route and request body, then calls the matching FQ method.
3. FQ uses Redis data structures and Lua scripts to mutate queue state atomically.
4. The server translates the FQ result into an HTTP status code and JSON response.

Background requeue loop
-----------------------

During startup, the server initializes the FQ client and starts a background task
that periodically calls ``queue.requeue()``. A Redis distributed lock is used so
multiple server instances do not requeue expired jobs at the same time.

The loop is controlled by:

* ``FQ_ENABLE_REQUEUE_SCRIPT``
* ``FQ_JOB_REQUEUE_INTERVAL``

Shutdown
--------

On shutdown, the server cancels the background requeue task and closes the Redis
client cleanly.

Related repositories
--------------------

* Server: https://github.com/flowdacity/flowdacity-queue-server
* Core queue library: https://github.com/flowdacity/flowdacity-queue
