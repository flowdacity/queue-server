# Copyright (c) 2025 Flowdacity Team. See LICENSE.txt for details.
# ASGI application entrypoint for Flowdacity Queue (FQ) Server

from fq_server import setup_server

server = setup_server()

# ASGI app exposed for Uvicorn/Hypercorn
app = server.app
