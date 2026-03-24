=============
API Reference
=============

This document describes the HTTP API exposed by Flowdacity Queue Server. All
documented routes include a trailing slash.

Root
~~~~

::

    GET /

Response:

.. code-block:: json

    {
      "message": "Hello, FQS!"
    }

Enqueue
~~~~~~~

::

    POST /enqueue/<queue_type>/<queue_id>/

Request body:

.. code-block:: json

    {
      "job_id": "job-1",
      "interval": 1000,
      "payload": {
        "message": "hello, world"
      }
    }

Optional request fields:

* ``requeue_limit``: override the default retry limit for the job.
* ``payload.max_queued_length``: reject the enqueue with HTTP ``429`` if the queue
  already contains at least that many jobs.

Success response:

* HTTP ``201``
* Body:

.. code-block:: json

    {
      "status": "queued"
    }

Dequeue
~~~~~~~

::

    GET /dequeue/
    GET /dequeue/<queue_type>/

``/dequeue/`` uses the default queue type ``default``.

Success response:

* HTTP ``200``
* Body:

.. code-block:: json

    {
      "status": "success",
      "queue_id": "user42",
      "job_id": "job-1",
      "payload": {
        "message": "hello, world"
      },
      "requeues_remaining": -1,
      "current_queue_length": 0
    }

If no job is ready, the server returns HTTP ``404`` with:

.. code-block:: json

    {
      "status": "failure"
    }

Finish
~~~~~~

::

    POST /finish/<queue_type>/<queue_id>/<job_id>/

Success response:

* HTTP ``200``
* Body:

.. code-block:: json

    {
      "status": "success"
    }

If the active job is not found, the server returns HTTP ``404``.

Interval
~~~~~~~~

::

    POST /interval/<queue_type>/<queue_id>/

Request body:

.. code-block:: json

    {
      "interval": 5000
    }

Success response:

.. code-block:: json

    {
      "status": "success"
    }

If the queue does not exist, the server returns HTTP ``404``.

Metrics
~~~~~~~

Global metrics:

::

    GET /metrics/

Response fields:

* ``queue_types``
* ``enqueue_counts``
* ``dequeue_counts``
* ``status``

Queue IDs for a queue type:

::

    GET /metrics/<queue_type>/

Response fields:

* ``queue_ids``
* ``status``

Queue-specific metrics:

::

    GET /metrics/<queue_type>/<queue_id>/

Response fields:

* ``queue_length``
* ``enqueue_counts``
* ``dequeue_counts``
* ``status``

Delete Queue
~~~~~~~~~~~~

::

    DELETE /deletequeue/<queue_type>/<queue_id>/

Optional request body:

.. code-block:: json

    {
      "purge_all": true
    }

This removes queued jobs for the target queue. When ``purge_all`` is ``true``,
related payload and interval metadata are removed as well.

Deep Status
~~~~~~~~~~~

::

    GET /deepstatus/

If Redis is reachable and writable, the server returns:

.. code-block:: json

    {
      "status": "success"
    }

Common failures
~~~~~~~~~~~~~~~

* HTTP ``400``: invalid route parameters, invalid JSON, or invalid FQ arguments.
* HTTP ``404``: no job ready to dequeue or target queue/job was not found.
* HTTP ``429``: enqueue rejected because ``payload.max_queued_length`` was reached.
* HTTP ``500``: backend health check failed during ``/deepstatus/``.
