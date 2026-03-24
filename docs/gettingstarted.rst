===============
Getting Started
===============

Run Redis locally, then start the API with environment variables.

Start Redis
-----------

::

    make redis-up

Start the server
----------------

::

    PORT=8300 \
    REDIS_HOST=127.0.0.1 \
    uv run uvicorn asgi:app --host 0.0.0.0 --port 8300

Check the root endpoint
-----------------------

.. code-block:: bash

    curl http://127.0.0.1:8300/

Queue workflow
--------------

* Enqueue a job with ``queue_type``, ``queue_id``, ``job_id``, ``interval``, and ``payload``.
* Dequeue work by queue type.
* Finish a dequeued job after processing it successfully.
* Expired jobs are requeued automatically based on ``JOB_EXPIRE_INTERVAL`` and
  ``JOB_REQUEUE_INTERVAL``.

Examples
--------

Enqueue
```````

.. code-block:: bash

    curl -X POST http://127.0.0.1:8300/enqueue/sms/user42/ \
      -H "Content-Type: application/json" \
      -d '{"job_id":"job-1","payload":{"message":"hello, world"},"interval":1000}'

Dequeue
```````

.. code-block:: bash

    curl http://127.0.0.1:8300/dequeue/sms/

Finish
``````

.. code-block:: bash

    curl -X POST http://127.0.0.1:8300/finish/sms/user42/job-1/

Metrics
```````

.. code-block:: bash

    curl http://127.0.0.1:8300/metrics/
    curl http://127.0.0.1:8300/metrics/sms/user42/
