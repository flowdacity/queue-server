# -*- coding: utf-8 -*-
# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import asyncio
import unittest

import ujson as json
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError
from starlette.types import ASGIApp
from unittest.mock import AsyncMock, patch

from fq_server import FQConfig, QueueServerSettings, build_config_from_env, setup_server


def build_test_config() -> FQConfig:
    return {
        "fq": {
            "job_expire_interval": 1000,
            "job_requeue_interval": 1000,
            "default_job_requeue_limit": -1,
            "enable_requeue_script": True,
        },
        "redis": {
            "db": 0,
            "key_prefix": "fq_server_test",
            "conn_type": "tcp_sock",
            "host": "127.0.0.1",
            "port": 6379,
            "password": "",
            "clustered": False,
            "unix_socket_path": "/tmp/redis.sock",
        },
    }


class FQConfigTestCase(unittest.TestCase):
    """Tests for configuration validation."""

    def test_build_config_from_env_defaults(self):
        config = build_config_from_env({})
        self.assertEqual(config["fq"]["job_expire_interval"], 1000)
        self.assertEqual(config["fq"]["job_requeue_interval"], 1000)
        self.assertEqual(config["fq"]["default_job_requeue_limit"], -1)
        self.assertTrue(config["fq"]["enable_requeue_script"])
        self.assertEqual(config["redis"]["host"], "127.0.0.1")
        self.assertEqual(config["redis"]["port"], 6379)
        self.assertEqual(config["redis"]["key_prefix"], "fq_server")

    def test_build_config_from_env_overrides(self):
        config = build_config_from_env(
            {
                "FQ_JOB_EXPIRE_INTERVAL": "5000",
                "FQ_JOB_REQUEUE_INTERVAL": "6000",
                "FQ_DEFAULT_JOB_REQUEUE_LIMIT": "5",
                "FQ_ENABLE_REQUEUE_SCRIPT": "false",
                "FQ_REDIS_DB": "2",
                "FQ_REDIS_KEY_PREFIX": "custom_prefix",
                "FQ_REDIS_CONN_TYPE": "unix_sock",
                "FQ_REDIS_HOST": "redis.internal",
                "FQ_REDIS_PORT": "6380",
                "FQ_REDIS_PASSWORD": "secret",
                "FQ_REDIS_CLUSTERED": "true",
                "FQ_REDIS_UNIX_SOCKET_PATH": "/var/run/redis.sock",
            }
        )
        self.assertEqual(config["fq"]["job_expire_interval"], 5000)
        self.assertEqual(config["fq"]["job_requeue_interval"], 6000)
        self.assertEqual(config["fq"]["default_job_requeue_limit"], 5)
        self.assertFalse(config["fq"]["enable_requeue_script"])
        self.assertEqual(config["redis"]["db"], 2)
        self.assertEqual(config["redis"]["key_prefix"], "custom_prefix")
        self.assertEqual(config["redis"]["conn_type"], "unix_sock")
        self.assertEqual(config["redis"]["host"], "redis.internal")
        self.assertEqual(config["redis"]["port"], 6380)
        self.assertEqual(config["redis"]["password"], "secret")
        self.assertTrue(config["redis"]["clustered"])
        self.assertEqual(
            config["redis"]["unix_socket_path"], "/var/run/redis.sock"
        )

    def test_build_config_from_env_rejects_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "FQ_REDIS_PORT"):
            build_config_from_env({"FQ_REDIS_PORT": "redis"})

        with self.assertRaisesRegex(ValueError, "FQ_ENABLE_REQUEUE_SCRIPT"):
            build_config_from_env({"FQ_ENABLE_REQUEUE_SCRIPT": "yes"})

        with self.assertRaisesRegex(ValueError, "FQ_REDIS_CLUSTERED"):
            build_config_from_env({"FQ_REDIS_CLUSTERED": "1"})

    def test_queue_server_settings_log_level_override(self):
        settings = QueueServerSettings.from_env({"FQ_LOG_LEVEL": "debug"})
        self.assertEqual(settings.log_level, "DEBUG")

    def test_queue_server_settings_rejects_invalid_log_level(self):
        with self.assertRaisesRegex(ValidationError, "FQ_LOG_LEVEL"):
            QueueServerSettings.from_env({"FQ_LOG_LEVEL": "verbose"})


class FQServerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # build server and Starlette app
        server = setup_server(build_test_config())
        self.server = server
        self.app: ASGIApp = server.app

        # queue + redis client (async)
        self.queue = server.queue
        await self.queue.initialize()  # important: same loop as tests
        self.r = self.queue._r

        # flush redis before each test
        await self.r.flushdb()

        # async HTTP client bound to this ASGI app & this loop
        transport = ASGITransport(app=self.app)
        self.client = AsyncClient(transport=transport, base_url="http://test")

    async def asyncTearDown(self):
        # flush redis after each test
        await self.r.flushdb()
        await self.client.aclose()
        await self.queue.close()

    async def test_root(self):
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, FQS!"})

    async def test_enqueue(self):
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        response = await self.client.post(
            "/enqueue/sms/johdoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "queued")

        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf1d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
            "requeue_limit": 10,
        }
        response = await self.client.post(
            "/enqueue/sms/johdoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "queued")

    async def test_dequeue_fail(self):
        response = await self.client.get("/dequeue/")
        # your Starlette handler returns 400 or 404 – pick what your code actually does
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

        response = await self.client.get("/dequeue/sms/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

    async def test_dequeue(self):
        # enqueue a job
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        # dequeue a job
        response = await self.client.get("/dequeue/sms/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["job_id"], "ef022088-d2b3-44ad-bf0d-a93d6d93b82c")
        self.assertEqual(data["payload"], {"message": "Hello, world."})
        self.assertEqual(data["queue_id"], "johndoe")
        self.assertEqual(data["requeues_remaining"], -1)  # from config

    async def test_finish_fail(self):
        response = await self.client.post(
            "/finish/sms/johndoe/ef022088-d2b3-44ad-bf0d-a93d6d93b82c/"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

    async def test_finish(self):
        # enqueue a job
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        # dequeue a job
        await self.client.get("/dequeue/sms/")

        # mark it as finished
        response = await self.client.post(
            "/finish/sms/johndoe/ef022088-d2b3-44ad-bf0d-a93d6d93b82c/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    async def test_interval(self):
        # enqueue a job
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        # change the interval
        request_params = {"interval": 5000}
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.json()["status"], "success")

    async def test_interval_fail(self):
        request_params = {"interval": 5000}
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.json()["status"], "failure")

    async def test_metrics(self):
        response = await self.client.get("/metrics/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_types", data)
        self.assertIn("enqueue_counts", data)
        self.assertIn("dequeue_counts", data)

    async def test_metrics_with_queue_type(self):
        response = await self.client.get("/metrics/sms/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_ids", data)

    async def test_metrics_with_queue_type_and_queue_id(self):
        response = await self.client.get("/metrics/sms/johndoe/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_length", data)
        self.assertIn("enqueue_counts", data)
        self.assertIn("dequeue_counts", data)

    # ===== NEW TESTS FOR UNCOVERED EXCEPTION PATHS =====

    async def test_enqueue_malformed_json(self):
        """Test enqueue with malformed JSON body."""
        response = await self.client.post(
            "/enqueue/sms/johndoe/",
            content=b"invalid json {",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")
        self.assertIn("message", response.json())

    async def test_enqueue_empty_body(self):
        """Test enqueue with empty body - fails because required fields missing."""
        response = await self.client.post(
            "/enqueue/sms/johndoe/",
            content=b"",
            headers={"Content-Type": "application/json"},
        )
        # Empty body becomes {}, but FQ requires payload, interval, job_id
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")

    async def test_enqueue_with_max_queued_length_not_exceeded(self):
        """Test enqueue with max_queued_length when queue is below limit."""
        request_params = {
            "job_id": "job-1",
            "payload": {"message": "Test 1", "max_queued_length": 10},
            "interval": 1000,
        }
        response = await self.client.post(
            "/enqueue/sms/test_queue_1/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "queued")
        self.assertEqual(response.json()["current_queue_length"], 0)

    async def test_enqueue_with_max_queued_length_exceeded(self):
        """Test enqueue when max_queued_length is exceeded (429 response)."""
        # First, enqueue some jobs to fill queue
        for i in range(3):
            request_params = {
                "job_id": f"job-{i}",
                "payload": {"message": f"Test {i}"},
                "interval": 1000,
            }
            await self.client.post(
                "/enqueue/sms/test_queue_2/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )

        # Now try to enqueue with max_queued_length=2 (should fail with 429)
        request_params = {
            "job_id": "job-overflow",
            "payload": {"message": "Overflow", "max_queued_length": 2},
            "interval": 1000,
        }
        response = await self.client.post(
            "/enqueue/sms/test_queue_2/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["status"], "failure")
        self.assertIn("Max queue length reached", response.json()["message"])
        self.assertGreaterEqual(response.json()["current_queue_length"], 2)

    async def test_enqueue_get_queue_length_exception(self):
        """Test enqueue when get_queue_length() raises an exception."""
        request_params = {
            "job_id": "job-error",
            "payload": {"message": "Error test", "max_queued_length": 5},
            "interval": 1000,
        }

        # Mock get_queue_length to fail, but let enqueue succeed normally
        with patch.object(self.queue, "get_queue_length", side_effect=Exception("Redis error")):
            response = await self.client.post(
                "/enqueue/sms/test_queue_3/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )
            # When get_queue_length fails, enqueue still succeeds with current_queue_length=0
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["status"], "queued")
            self.assertEqual(response.json()["current_queue_length"], 0)

    async def test_enqueue_queue_enqueue_exception(self):
        """Test enqueue when queue.enqueue() raises an exception."""
        request_params = {
            "job_id": "job-queue-error",
            "payload": {"message": "Queue error"},
            "interval": 1000,
        }

        with patch.object(self.queue, "enqueue", side_effect=Exception("Queue error")):
            response = await self.client.post(
                "/enqueue/sms/johndoe/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Queue error", response.json()["message"])

    async def test_dequeue_get_queue_length_exception(self):
        """Test dequeue when get_queue_length() raises an exception."""
        # First enqueue a job
        request_params = {
            "job_id": "job-for-dequeue",
            "payload": {"message": "Dequeue test"},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/dequeue_error_queue/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        # Now dequeue but mock get_queue_length to fail
        with patch.object(self.queue, "get_queue_length", side_effect=Exception("Redis error")):
            response = await self.client.get("/dequeue/sms/")
            # Should still return 200 but without current_queue_length
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "success")
            self.assertEqual(response.json()["current_queue_length"], 0)

    async def test_dequeue_exception_general(self):
        """Test dequeue when queue.dequeue() raises a general exception."""
        with patch.object(self.queue, "dequeue", side_effect=Exception("Dequeue failed")):
            response = await self.client.get("/dequeue/sms/")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Dequeue failed", response.json()["message"])

    async def test_finish_exception(self):
        """Test finish when queue.finish() raises an exception."""
        with patch.object(self.queue, "finish", side_effect=Exception("Finish error")):
            response = await self.client.post(
                "/finish/sms/johndoe/job-123/"
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Finish error", response.json()["message"])

    async def test_interval_malformed_json(self):
        """Test interval with malformed JSON body."""
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=b"invalid json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")

    async def test_interval_missing_interval_key(self):
        """Test interval request without 'interval' key."""
        request_params = {"some_other_key": 5000}
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")

    async def test_interval_exception(self):
        """Test interval when queue.interval() raises an exception."""
        request_params = {"interval": 5000}

        with patch.object(self.queue, "interval", side_effect=Exception("Interval error")):
            response = await self.client.post(
                "/interval/sms/johndoe/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Interval error", response.json()["message"])

    async def test_metrics_exception(self):
        """Test metrics when queue.metrics() raises an exception."""
        with patch.object(self.queue, "metrics", side_effect=Exception("Metrics error")):
            response = await self.client.get("/metrics/")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Metrics error", response.json()["message"])

    async def test_metrics_with_queue_type_exception(self):
        """Test metrics with queue_type when exception occurs."""
        with patch.object(self.queue, "metrics", side_effect=Exception("Metrics error")):
            response = await self.client.get("/metrics/sms/")
            self.assertEqual(response.status_code, 400)

    async def test_clear_queue_malformed_json(self):
        """Test clear_queue with malformed JSON body."""
        response = await self.client.request(
            "DELETE",
            "/deletequeue/sms/johndoe/",
            content=b"invalid json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")

    async def test_clear_queue_exception(self):
        """Test clear_queue when queue.clear_queue() raises an exception."""
        with patch.object(self.queue, "clear_queue", side_effect=Exception("Clear error")):
            response = await self.client.delete("/deletequeue/sms/johndoe/")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Clear error", response.json()["message"])

    async def test_enqueue_max_length_with_queue_exception(self):
        """Test enqueue max_queued_length when enqueue itself throws."""
        request_params = {
            "job_id": "job-with-max",
            "payload": {"message": "Test", "max_queued_length": 10},
            "interval": 1000,
        }
        
        with patch.object(self.queue, "enqueue", side_effect=Exception("Enqueue failed")):
            response = await self.client.post(
                "/enqueue/sms/johndoe/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Enqueue failed", response.json()["message"])

    async def test_deep_status_exception(self):
        """Test deep_status when queue.deep_status() raises an exception."""
        with patch.object(self.queue, "deep_status", side_effect=Exception("Status check failed")):
            with self.assertRaises(Exception):
                await self.client.get("/deepstatus/")

    async def test_deep_status_success(self):
        """Test deep_status successful response."""
        response = await self.client.get("/deepstatus/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    # ===== TESTS FOR REQUEUE AND LIFESPAN =====

    async def test_requeue_exception_handling(self):
        """Test requeue loop catches and continues on exception."""
        server = self.server
        
        # Mock the queue.requeue to raise an exception
        with patch.object(server.queue, "requeue", side_effect=Exception("Requeue failed")):
            # Create a requeue coroutine and run it briefly
            requeue_task = asyncio.create_task(server.requeue())
            
            # Let it run for a short moment
            await asyncio.sleep(0.1)
            
            # Cancel the task
            requeue_task.cancel()
            
            with self.assertRaises(asyncio.CancelledError):
                await requeue_task

    async def test_requeue_with_lock_disabled(self):
        """Test requeue_with_lock when requeue is disabled."""
        server = self.server

        server.config["fq"]["enable_requeue_script"] = False
        requeue_task = asyncio.create_task(server.requeue_with_lock())

        # Should return immediately (task completes)
        await asyncio.sleep(0.1)

        # Task should be done (returned, not cancelled)
        self.assertTrue(requeue_task.done())
        server.config["fq"]["enable_requeue_script"] = True

    async def test_requeue_with_lock_lock_error(self):
        """Test requeue_with_lock when lock acquisition fails with LockError."""
        from redis.exceptions import LockError
        server = self.server
        
        # Create an async context manager that raises LockError on enter
        class FailingLock:
            async def __aenter__(self):
                raise LockError("Failed to acquire lock")
            
            async def __aexit__(self, *args):
                pass
        
        # Mock redis_client with a lock method that returns the failing lock
        mock_redis = AsyncMock()
        # Make lock a regular (non-async) function that returns the context manager
        mock_redis.lock = lambda *args, **kwargs: FailingLock()
        
        with patch.object(server.queue, "redis_client", return_value=mock_redis):
            requeue_task = asyncio.create_task(server.requeue_with_lock())
            
            # Let it try to acquire lock and handle LockError (sleeps and continues)
            await asyncio.sleep(0.15)
            
            # Cancel it
            requeue_task.cancel()
            
            try:
                await requeue_task
            except asyncio.CancelledError:
                pass  # Expected - loop continues after LockError, then cancelled

    async def test_requeue_with_lock_inner_exception(self):
        """Test requeue_with_lock when requeue() inside lock context fails."""
        server = self.server
        
        # First request succeeds to get past initial try, second fails
        call_count = [0]
        
        async def mock_requeue_with_failure():
            call_count[0] += 1
            if call_count[0] >= 1:  # Fail on first and subsequent calls
                raise Exception("Inner requeue error")
            return None
        
        with patch.object(server.queue, "requeue", side_effect=mock_requeue_with_failure):
            requeue_task = asyncio.create_task(server.requeue_with_lock())
            
            # Let it run enough times to hit the exception in lock
            await asyncio.sleep(0.15)
            requeue_task.cancel()
            
            try:
                await requeue_task
            except asyncio.CancelledError:
                pass  # Expected - task was cancelled after executing exception code path


class FQServerLifespanTestCase(unittest.IsolatedAsyncioTestCase):
    """Test FQServer lifespan (startup/shutdown)."""

    async def test_lifespan_startup_shutdown(self):
        """Test lifespan startup and graceful shutdown."""
        server = setup_server(build_test_config())
        
        # Simulate startup
        app = server.app
        lifespan_cm = server._lifespan(app)
        
        # Enter lifespan (startup)
        await lifespan_cm.__aenter__()
        
        # Check that requeue task was created
        self.assertIsNotNone(server._requeue_task)
        self.assertFalse(server._requeue_task.done())
        
        # Exit lifespan (shutdown)
        try:
            await lifespan_cm.__aexit__(None, None, None)
        except asyncio.CancelledError:
            # Expected if the requeue task is cancelled during shutdown
            pass
        
        # Task should be cancelled or done
        await asyncio.sleep(0.05)
        self.assertTrue(server._requeue_task.done() or server._requeue_task.cancelled())

    async def test_lifespan_initializes_queue(self):
        """Test that lifespan calls queue.initialize()."""
        server = setup_server(build_test_config())

        # Stub out both queue.initialize and the background requeue task to make
        # startup/shutdown deterministic and avoid hitting an uninitialized queue.
        with patch.object(
            server.queue, "initialize", new_callable=AsyncMock
        ) as mock_init, patch.object(
            server.queue, "close", new_callable=AsyncMock
        ) as mock_close, patch.object(
            server, "requeue_with_lock", new_callable=AsyncMock
        ):
            lifespan_cm = server._lifespan(server.app)
            await lifespan_cm.__aenter__()

            mock_init.assert_called_once()

            # Cleanup
            if server._requeue_task is not None and not server._requeue_task.done():
                server._requeue_task.cancel()
            try:
                await lifespan_cm.__aexit__(None, None, None)
            except asyncio.CancelledError:
                # Expected if the requeue task is cancelled during shutdown
                pass
            mock_close.assert_called_once()



if __name__ == "__main__":
    unittest.main()
