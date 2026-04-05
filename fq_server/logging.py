# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import logging


def configure_logging(
    log_level: str,
    suppress_access_logs: bool = True,
) -> None:
    level = getattr(logging, log_level)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )

    logging.getLogger("fq_server").setLevel(level)
    logging.getLogger("uvicorn.access").disabled = suppress_access_logs
