=============
Configuration
=============

Flowdacity Queue Server reads its runtime configuration from environment variables.
Settings are validated at startup with ``pydantic-settings``.

Queue settings
--------------

``JOB_EXPIRE_INTERVAL``
    Milliseconds after which a dequeued job is considered expired.

``JOB_REQUEUE_INTERVAL``
    Milliseconds between requeue passes for expired jobs.

``DEFAULT_JOB_REQUEUE_LIMIT``
    Default retry limit for jobs. ``-1`` means retry forever.

``ENABLE_REQUEUE_SCRIPT``
    Enables or disables the background requeue loop.

``LOG_LEVEL``
    Application log level. Supported values are ``DEBUG``, ``INFO``, ``WARNING``,
    ``ERROR``, and ``CRITICAL``.

``SUPPRESS_ACCESS_LOGS``
    Suppresses all Uvicorn access logs.

Redis settings
--------------

``REDIS_DB``
    Redis database number.

``REDIS_KEY_PREFIX``
    Prefix used for Redis keys created by the queue.

``REDIS_CONN_TYPE``
    Redis connection type. Supported values are ``tcp_sock`` and ``unix_sock``.

``REDIS_HOST``
    Redis host for TCP connections.

``REDIS_PORT``
    Redis port for TCP connections.

``REDIS_PASSWORD``
    Redis password. Leave empty when authentication is not required.

``REDIS_CLUSTERED``
    Enables Redis Cluster mode when set to ``true``.

``REDIS_UNIX_SOCKET_PATH``
    Redis unix socket path when ``REDIS_CONN_TYPE=unix_sock``.

Defaults
--------

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
   * - ``JOB_EXPIRE_INTERVAL``
     - ``1000``
   * - ``JOB_REQUEUE_INTERVAL``
     - ``1000``
   * - ``DEFAULT_JOB_REQUEUE_LIMIT``
     - ``-1``
   * - ``ENABLE_REQUEUE_SCRIPT``
     - ``true``
   * - ``LOG_LEVEL``
     - ``INFO``
   * - ``SUPPRESS_ACCESS_LOGS``
     - ``true``
   * - ``REDIS_DB``
     - ``0``
   * - ``REDIS_KEY_PREFIX``
     - ``fq_server``
   * - ``REDIS_CONN_TYPE``
     - ``tcp_sock``
   * - ``REDIS_HOST``
     - ``127.0.0.1``
   * - ``REDIS_PORT``
     - ``6379``
   * - ``REDIS_PASSWORD``
     - empty
   * - ``REDIS_CLUSTERED``
     - ``false``
   * - ``REDIS_UNIX_SOCKET_PATH``
     - ``/tmp/redis.sock``

Boolean values
--------------

Boolean environment variables accept only ``true`` and ``false``.
