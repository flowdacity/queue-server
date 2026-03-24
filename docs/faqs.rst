==========================
Frequently Asked Questions
==========================

When should I use Flowdacity Queue Server?
==========================================

Use it when you want HTTP access to Flowdacity Queue from workers or services that
should not link directly against the Python FQ library. It is especially useful when
you need dynamic queues, per-queue rate limits, and Redis-backed retry/requeue behavior.

How do I set a rate limit for a queue?
======================================

Set the ``interval`` field when enqueueing a job. The interval is in milliseconds and
represents the minimum gap between successful dequeues for the queue.

How do I change the rate limit of an existing queue?
====================================================

Call the `Interval API <apireference.html#interval>`_:

.. code-block:: bash

    curl -X POST http://127.0.0.1:8080/interval/sms/user42/ \
      -H "Content-Type: application/json" \
      -d '{"interval": 5000}'

How do I write a worker that processes jobs from the server?
============================================================

Any HTTP client can be used. A minimal Python example with ``httpx`` looks like this:

.. code-block:: python

    import time

    import httpx


    with httpx.Client(base_url="http://127.0.0.1:8080") as client:
        while True:
            response = client.get("/dequeue/sms/")

            if response.status_code == 200:
                job = response.json()
                print(job["payload"])
                client.post(
                    f"/finish/sms/{job['queue_id']}/{job['job_id']}/"
                )
                continue

            if response.status_code == 404:
                time.sleep(1)
                continue

            raise RuntimeError(response.text)

How do I configure job expiry and requeue timing?
=================================================

Use environment variables:

* ``JOB_EXPIRE_INTERVAL`` controls how long a dequeued job can remain active
  before it is considered expired.
* ``JOB_REQUEUE_INTERVAL`` controls how often expired jobs are scanned and
  placed back onto their queues.

How do I inspect queue depth and throughput?
============================================

Use the `Metrics API <apireference.html#metrics>`_. It provides:

* Global queue types plus enqueue/dequeue counts.
* Queue IDs for a specific queue type.
* Queue length and per-minute counters for a specific queue.

How do I clear a queue?
=======================

Call the ``DELETE /deletequeue/<queue_type>/<queue_id>/`` endpoint. If you want to
remove related payload and interval metadata as well, send ``{"purge_all": true}``
in the request body.

Where is the source code?
=========================

The codebase is split across two repositories:

* Flowdacity Queue Server: https://github.com/flowdacity/flowdacity-queue-server
* Flowdacity Queue core: https://github.com/flowdacity/flowdacity-queue

How do I report a bug or contribute a fix?
==========================================

Open an issue or pull request in the server repository and include reproduction
steps, Redis details, and any failing requests or tests when possible. The
`Contributing <contributing.html>`_ section covers the local development workflow.
