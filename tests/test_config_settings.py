# -*- coding: utf-8 -*-
# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import unittest

from pydantic import ValidationError

from fq_server import QueueServerSettings
from tests.support import build_config_from_env


class TestConfigSettings(unittest.TestCase):
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
                "JOB_EXPIRE_INTERVAL": "5000",
                "JOB_REQUEUE_INTERVAL": "6000",
                "DEFAULT_JOB_REQUEUE_LIMIT": "5",
                "ENABLE_REQUEUE_SCRIPT": "false",
                "REDIS_DB": "2",
                "REDIS_KEY_PREFIX": "custom_prefix",
                "REDIS_CONN_TYPE": "unix_sock",
                "REDIS_HOST": "redis.internal",
                "REDIS_PORT": "6380",
                "REDIS_PASSWORD": "secret",
                "REDIS_CLUSTERED": "true",
                "REDIS_UNIX_SOCKET_PATH": "/var/run/redis.sock",
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
        self.assertEqual(config["redis"]["unix_socket_path"], "/var/run/redis.sock")

    def test_build_config_from_env_rejects_invalid_values(self):
        with self.assertRaisesRegex(ValueError, "REDIS_PORT"):
            build_config_from_env({"REDIS_PORT": "redis"})

        with self.assertRaisesRegex(ValueError, "ENABLE_REQUEUE_SCRIPT"):
            build_config_from_env({"ENABLE_REQUEUE_SCRIPT": "yes"})

        with self.assertRaisesRegex(ValueError, "REDIS_CLUSTERED"):
            build_config_from_env({"REDIS_CLUSTERED": "1"})

    def test_queue_server_settings_log_level_override(self):
        settings = QueueServerSettings.from_env({"LOG_LEVEL": "debug"})
        self.assertEqual(settings.log_level, "DEBUG")

    def test_queue_server_settings_suppress_access_logs_default(self):
        settings = QueueServerSettings.from_env({})
        self.assertTrue(settings.suppress_access_logs)

    def test_queue_server_settings_suppress_access_logs_override(self):
        settings = QueueServerSettings.from_env({"SUPPRESS_ACCESS_LOGS": "false"})
        self.assertFalse(settings.suppress_access_logs)

    def test_queue_server_settings_rejects_invalid_log_level(self):
        with self.assertRaisesRegex(ValidationError, "LOG_LEVEL"):
            QueueServerSettings.from_env({"LOG_LEVEL": "verbose"})
