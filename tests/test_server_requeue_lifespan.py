# -*- coding: utf-8 -*-
# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from fq_server import setup_server
from tests.support import FQServerAsyncTestCase, build_test_config


class TestServerRequeue(FQServerAsyncTestCase):
    async def test_requeue_exception_handling(self):
        server = self.server

        with patch.object(server.queue, "requeue", side_effect=Exception("Requeue failed")):
            requeue_task = asyncio.create_task(server.requeue())
            await asyncio.sleep(0.1)

            requeue_task.cancel()

            with self.assertRaises(asyncio.CancelledError):
                await requeue_task

    async def test_requeue_with_lock_disabled(self):
        server = self.server

        server.config["fq"]["enable_requeue_script"] = False
        requeue_task = asyncio.create_task(server.requeue_with_lock())

        await asyncio.sleep(0.1)

        self.assertTrue(requeue_task.done())
        server.config["fq"]["enable_requeue_script"] = True

    async def test_requeue_with_lock_lock_error(self):
        from redis.exceptions import LockError

        server = self.server

        class FailingLock:
            async def __aenter__(self):
                raise LockError("Failed to acquire lock")

            async def __aexit__(self, *args):
                return None

        mock_redis = AsyncMock()
        mock_redis.lock = lambda *args, **kwargs: FailingLock()

        with patch.object(server.queue, "redis_client", return_value=mock_redis):
            requeue_task = asyncio.create_task(server.requeue_with_lock())
            await asyncio.sleep(0.15)

            requeue_task.cancel()

            try:
                await requeue_task
            except asyncio.CancelledError:
                pass

    async def test_requeue_with_lock_inner_exception(self):
        server = self.server

        call_count = [0]

        async def mock_requeue_with_failure():
            call_count[0] += 1
            if call_count[0] >= 1:
                raise Exception("Inner requeue error")
            return None

        with patch.object(server.queue, "requeue", side_effect=mock_requeue_with_failure):
            requeue_task = asyncio.create_task(server.requeue_with_lock())

            await asyncio.sleep(0.15)
            requeue_task.cancel()

            try:
                await requeue_task
            except asyncio.CancelledError:
                pass

    async def test_requeue_with_lock_missing_redis_client(self):
        server = self.server
        server.config["fq"]["job_requeue_interval"] = 1

        with patch.object(server.queue, "redis_client", return_value=None):
            requeue_task = asyncio.create_task(server.requeue_with_lock())
            await asyncio.sleep(0.05)

            self.assertTrue(requeue_task.done())
            self.assertIsNone(requeue_task.exception())


class TestServerRequeueRedisErrors(unittest.IsolatedAsyncioTestCase):
    """Focused tests for requeue loop error handling that do not need Redis."""

    async def test_requeue_with_lock_redis_error(self):
        from redis.exceptions import RedisError

        server = setup_server(build_test_config())

        def failing_lock(*args, **kwargs):
            raise RedisError("Redis lock creation failed")

        mock_redis = AsyncMock()
        mock_redis.lock = failing_lock

        with patch.object(server.queue, "redis_client", return_value=mock_redis):
            with self.assertLogs("fq_server.server", level="ERROR") as captured:
                requeue_task = asyncio.create_task(server.requeue_with_lock())
                await asyncio.sleep(0.05)

                self.assertFalse(requeue_task.done())

                requeue_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await requeue_task

        self.assertTrue(
            any(
                "Transient Redis error in requeue loop while managing lock" in message
                for message in captured.output
            )
        )

    async def test_requeue_with_lock_lock_context_timeout(self):
        from redis.exceptions import TimeoutError as RedisTimeoutError

        server = setup_server(build_test_config())

        class FailingLock:
            async def __aenter__(self):
                raise RedisTimeoutError("Timed out entering lock context")

            async def __aexit__(self, *args):
                return None

        mock_redis = AsyncMock()
        mock_redis.lock = lambda *args, **kwargs: FailingLock()

        with patch.object(server.queue, "redis_client", return_value=mock_redis):
            with self.assertLogs("fq_server.server", level="ERROR") as captured:
                requeue_task = asyncio.create_task(server.requeue_with_lock())
                await asyncio.sleep(0.05)

                self.assertFalse(requeue_task.done())

                requeue_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await requeue_task

        self.assertTrue(
            any(
                "Transient Redis error in requeue loop while managing lock" in message
                for message in captured.output
            )
        )


class TestServerLifespan(unittest.IsolatedAsyncioTestCase):
    """Test FQServer lifespan (startup/shutdown)."""

    async def test_lifespan_startup_shutdown(self):
        server = setup_server(build_test_config())

        app = server.app
        lifespan_cm = server._lifespan(app)

        await lifespan_cm.__aenter__()

        self.assertIsNotNone(server._requeue_task)
        self.assertFalse(server._requeue_task.done())

        try:
            await lifespan_cm.__aexit__(None, None, None)
        except asyncio.CancelledError:
            pass

        await asyncio.sleep(0.05)
        self.assertTrue(server._requeue_task.done() or server._requeue_task.cancelled())

    async def test_lifespan_initializes_queue(self):
        server = setup_server(build_test_config())

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

            if server._requeue_task is not None and not server._requeue_task.done():
                server._requeue_task.cancel()
            try:
                await lifespan_cm.__aexit__(None, None, None)
            except asyncio.CancelledError:
                pass
            mock_close.assert_called_once()