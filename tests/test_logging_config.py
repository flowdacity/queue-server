# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import logging
import unittest

from fq_server.logging import configure_logging


class TestLoggingConfig(unittest.TestCase):
    def setUp(self):
        self.root_logger = logging.getLogger()
        self.original_root_handlers = list(self.root_logger.handlers)
        self.original_root_level = self.root_logger.level
        self.fq_logger = logging.getLogger("fq_server")
        self.original_fq_level = self.fq_logger.level
        self.access_logger = logging.getLogger("uvicorn.access")
        self.original_disabled = self.access_logger.disabled

    def tearDown(self):
        for handler in list(self.root_logger.handlers):
            if handler not in self.original_root_handlers:
                self.root_logger.removeHandler(handler)
                handler.close()

        self.root_logger.setLevel(self.original_root_level)
        self.fq_logger.setLevel(self.original_fq_level)
        self.access_logger.disabled = self.original_disabled

    def test_configure_logging_disables_access_logger_when_suppressed(self):
        self.access_logger.disabled = False
        configure_logging("INFO", suppress_access_logs=True)
        self.assertTrue(self.access_logger.disabled)

    def test_configure_logging_enables_access_logger_when_not_suppressed(self):
        self.access_logger.disabled = True
        configure_logging("INFO", suppress_access_logs=False)
        self.assertFalse(self.access_logger.disabled)

    def test_configure_logging_sets_fq_logger_level(self):
        self.fq_logger.setLevel(logging.NOTSET)
        configure_logging("WARNING", suppress_access_logs=False)
        self.assertEqual(self.fq_logger.level, logging.WARNING)
