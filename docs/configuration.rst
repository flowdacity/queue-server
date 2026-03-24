=============
Configuration
=============

Flowdacity Queue Server reads its runtime configuration from environment variables.
Settings are validated at startup with ``pydantic-settings``.

Queue settings
--------------

``FQ_JOB_EXPIRE_INTERVAL``
    Milliseconds after which a dequeued job is considered expired.

``FQ_JOB_REQUEUE_INTERVAL``
    Milliseconds between requeue passes for expired jobs.

``FQ_DEFAULT_JOB_REQUEUE_LIMIT``
    Default retry limit for jobs. ``-1`` means retry forever.

``FQ_ENABLE_REQUEUE_SCRIPT``
    Enables or disables the background requeue loop.

``FQ_LOG_LEVEL``
    Application log level. Supported values are ``DEBUG``, ``INFO``, ``WARNING``,
    ``ERROR``, and ``CRITICAL``.

Redis settings
--------------

``FQ_REDIS_DB``
    Redis database number.

``FQ_REDIS_KEY_PREFIX``
    Prefix used for Redis keys created by the queue.

``FQ_REDIS_CONN_TYPE``
    Redis connection type. Supported values are ``tcp_sock`` and ``unix_sock``.

``FQ_REDIS_HOST``
    Redis host for TCP connections.

``FQ_REDIS_PORT``
    Redis port for TCP connections.

``FQ_REDIS_PASSWORD``
    Redis password. Leave empty when authentication is not required.

``FQ_REDIS_CLUSTERED``
    Enables Redis Cluster mode when set to ``true``.

``FQ_REDIS_UNIX_SOCKET_PATH``
    Redis unix socket path when ``FQ_REDIS_CONN_TYPE=unix_sock``.

Defaults
--------

.. list-table::
   :header-rows: 1

   * - Variable
     - Default
   * - ``FQ_JOB_EXPIRE_INTERVAL``
     - ``1000``
   * - ``FQ_JOB_REQUEUE_INTERVAL``
     - ``1000``
   * - ``FQ_DEFAULT_JOB_REQUEUE_LIMIT``
     - ``-1``
   * - ``FQ_ENABLE_REQUEUE_SCRIPT``
     - ``true``
   * - ``FQ_LOG_LEVEL``
     - ``INFO``
   * - ``FQ_REDIS_DB``
     - ``0``
   * - ``FQ_REDIS_KEY_PREFIX``
     - ``fq_server``
   * - ``FQ_REDIS_CONN_TYPE``
     - ``tcp_sock``
   * - ``FQ_REDIS_HOST``
     - ``127.0.0.1``
   * - ``FQ_REDIS_PORT``
     - ``6379``
   * - ``FQ_REDIS_PASSWORD``
     - empty
   * - ``FQ_REDIS_CLUSTERED``
     - ``false``
   * - ``FQ_REDIS_UNIX_SOCKET_PATH``
     - ``/tmp/redis.sock``

Boolean values
--------------

Boolean environment variables accept only ``true`` and ``false``.
