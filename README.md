[![Run tests and upload coverage](https://github.com/flowdacity/queue-server/actions/workflows/test.yml/badge.svg)](https://github.com/flowdacity/queue-server/actions/workflows/test.yml)
[![codecov](https://codecov.io/github/flowdacity/queue-server/graph/badge.svg?token=9AK3GR856C)](https://codecov.io/github/flowdacity/queue-server)

Flowdacity Queue Server
=======================

An async HTTP API for [Flowdacity Queue (FQ)](https://github.com/flowdacity/queue-engine), built with Starlette and Uvicorn.

## Prerequisites

- Python 3.12+
- Redis 7+

## Installation

```bash
uv sync --group dev
```

If you prefer a virtualenv without `uv`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest pytest-cov
```

## Configuration

The server reads all queue and Redis settings from environment variables. No config file is required.
Values are validated at startup with `pydantic-settings`.

| Variable | Default | Description |
| --- | --- | --- |
| `JOB_EXPIRE_INTERVAL` | `1000` | Milliseconds before a dequeued job is considered expired. |
| `JOB_REQUEUE_INTERVAL` | `1000` | Milliseconds between expired-job requeue passes. |
| `DEFAULT_JOB_REQUEUE_LIMIT` | `-1` | Default retry limit. `-1` retries forever. |
| `ENABLE_REQUEUE_SCRIPT` | `true` | Enables the background requeue loop. |
| `LOG_LEVEL` | `INFO` | Application log level. |
| `REDIS_DB` | `0` | Redis database number. |
| `REDIS_KEY_PREFIX` | `fq_server` | Prefix used for Redis keys. |
| `REDIS_CONN_TYPE` | `tcp_sock` | Redis connection type: `tcp_sock` or `unix_sock`. |
| `REDIS_HOST` | `127.0.0.1` | Redis host for TCP connections. |
| `REDIS_PORT` | `6379` | Redis port for TCP connections. |
| `REDIS_PASSWORD` | empty | Redis password. |
| `REDIS_CLUSTERED` | `false` | Enables Redis Cluster mode. |
| `REDIS_UNIX_SOCKET_PATH` | `/tmp/redis.sock` | Redis socket path when `REDIS_CONN_TYPE=unix_sock`. |
| `PORT` | `8300` | Uvicorn port used by the container and local examples. |

Boolean env vars accept only `true` or `false`.

## Run locally

Start Redis:

```bash
make redis-up
```

Run the API:

```bash
PORT=8300 \
REDIS_HOST=127.0.0.1 \
uv run uvicorn asgi:app --host 0.0.0.0 --port 8300
```

## Docker

`docker-compose.yml` now passes the queue settings through env vars, so there is no mounted config file:

```bash
docker compose up --build
```

## API quick start

```bash
curl http://127.0.0.1:8300/

curl -X POST http://127.0.0.1:8300/enqueue/sms/user42/ \
  -H "Content-Type: application/json" \
  -d '{"job_id":"job-1","payload":{"message":"hi"},"interval":1000}'

curl http://127.0.0.1:8300/dequeue/sms/

curl -X POST http://127.0.0.1:8300/finish/sms/user42/job-1/

curl http://127.0.0.1:8300/metrics/
curl http://127.0.0.1:8300/metrics/sms/user42/
```

## Testing

```bash
make test
```

## License

MIT — see `LICENSE.txt`.
