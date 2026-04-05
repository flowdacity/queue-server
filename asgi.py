# Copyright (c) 2025 Flowdacity Team. See LICENSE.txt for details.
# ASGI application entrypoint for Flowdacity Queue (FQ) Server

from fq_server import QueueServerSettings, setup_server
from fq_server.logging import configure_logging


settings = QueueServerSettings.from_env()
configure_logging(
    settings.log_level,
    suppress_access_logs=settings.suppress_access_logs,
)
server = setup_server(settings.to_fq_config())

# ASGI app exposed for Uvicorn/Hypercorn
app = server.app
