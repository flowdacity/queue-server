Flowdacity Queue Server
=======================

Flowdacity Queue Server is an async HTTP API for `Flowdacity Queue (FQ) <https://github.com/flowdacity/flowdacity-queue>`_.
It runs on Starlette and Uvicorn, stores queue state in Redis through the FQ core,
and exposes HTTP endpoints for enqueueing, dequeueing, finishing, requeueing, and
inspecting jobs.

The server is configured entirely through environment variables and is designed to
fit containerized deployments without mounted config files.

To learn more, start with the `getting started guide <gettingstarted.html>`_.

.. toctree::
   :maxdepth: 2

   installation
   gettingstarted
   configuration
   apireference
   internals
   faqs
   contributing
   license
