# Copyright (c) 2025 Flowdacity Team. See LICENSE.txt for details.
# ASGI application entrypoint for Flowdacity Queue (FQ) Server

import logging

from fq_server import QueueServerSettings, setup_server


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


settings = QueueServerSettings.from_env()
configure_logging(
    settings.log_level,
    suppress_access_logs=settings.suppress_access_logs,
)
server = setup_server(settings.to_fq_config())

# ASGI app exposed for Uvicorn/Hypercorn
app = server.app
