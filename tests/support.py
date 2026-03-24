# -*- coding: utf-8 -*-
# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import unittest

from httpx import ASGITransport, AsyncClient
from starlette.types import ASGIApp

from fq_server import FQConfig, build_config_from_env, setup_server


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


class FQServerAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        server = setup_server(build_test_config())
        self.server = server
        self.app: ASGIApp = server.app

        self.queue = server.queue
        await self.queue.initialize()
        self.r = self.queue._r

        await self.r.flushdb()

        transport = ASGITransport(app=self.app)
        self.client = AsyncClient(transport=transport, base_url="http://test")

    async def asyncTearDown(self):
        await self.r.flushdb()
        await self.client.aclose()
        await self.queue.close()


__all__ = [
    "FQServerAsyncTestCase",
    "build_config_from_env",
    "build_test_config",
]