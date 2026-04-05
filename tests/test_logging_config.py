# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import logging
import unittest

from asgi import configure_logging


class TestLoggingConfig(unittest.TestCase):
    def setUp(self):
        self.access_logger = logging.getLogger("uvicorn.access")
        self.original_disabled = self.access_logger.disabled

    def tearDown(self):
        self.access_logger.disabled = self.original_disabled

    def test_configure_logging_disables_access_logger_when_suppressed(self):
        self.access_logger.disabled = False
        configure_logging("INFO", suppress_access_logs=True)
        self.assertTrue(self.access_logger.disabled)

    def test_configure_logging_enables_access_logger_when_not_suppressed(self):
        self.access_logger.disabled = True
        configure_logging("INFO", suppress_access_logs=False)
        self.assertFalse(self.access_logger.disabled)
