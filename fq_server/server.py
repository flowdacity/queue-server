# -*- coding: utf-8 -*-
# Copyright (c) 2014 Plivo Team. See LICENSE.txt for details.
# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import asyncio
import logging
import ujson as json
from collections.abc import Mapping
from contextlib import asynccontextmanager, suppress
from typing import Any, TypeAlias
from fq import FQ
from pydantic import ValidationError
from redis.exceptions import (
    ConnectionError as RedisConnectionError,
    LockError,
    RedisError,
    TimeoutError as RedisTimeoutError,
)

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from fq_server.settings import FQConfig, QueueServerSettings

JSONDict: TypeAlias = dict[str, Any]
logger = logging.getLogger(__name__)


def build_config_from_env(
    env: Mapping[str, str] | None = None,
) -> FQConfig:
    """Build the FQ/FQ server configuration from environment variables."""
    try:
        return QueueServerSettings.from_env(env).to_fq_config()
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


class FQServer(object):
    """Defines a HTTP based API on top of FQ and
    exposes the app to run the server (Starlette).
    """

    def __init__(self, config: FQConfig):
        """Load the FQ config mapping and define the routes."""
        self.config = config
        self.queue = FQ(self.config)
        self._requeue_task: asyncio.Task | None = None

        # Starlette app with routes and startup hook
        self.app = Starlette(
            routes=self._build_routes(),
            lifespan=self._lifespan,
        )

    # ------------------------------------------------------------------
    # Background requeue loops (async version of gevent ones)
    # ------------------------------------------------------------------
    async def requeue(self):
        """Loop endlessly and requeue expired jobs (no lock)."""
        job_requeue_interval = float(self.config["fq"]["job_requeue_interval"])
        while True:
            try:
                await self.queue.requeue()
            except Exception:
                logger.exception("Failed to requeue expired jobs")
            # in seconds
            await asyncio.sleep(job_requeue_interval / 1000.0)

    async def requeue_with_lock(self):
        """Loop endlessly and requeue expired jobs, but with a distributed lock."""
        if not self.config["fq"]["enable_requeue_script"]:
            logger.info("Requeue loop disabled")
            return

        job_requeue_interval = float(self.config["fq"]["job_requeue_interval"])

        logger.info(
            "Starting requeue loop",
            extra={"job_requeue_interval": job_requeue_interval},
        )

        while True:
            try:
                redis = self.queue.redis_client()
                if redis is None:
                    logger.error("Redis client is not initialized; stopping requeue loop")
                    return
                # assumes async lock
                async with redis.lock("fq-requeue-lock-key", timeout=15):
                    try:
                        await self.queue.requeue()
                    except Exception:
                        logger.exception("Failed to requeue expired jobs while holding lock")
            except LockError:
                # the lock wasn't acquired within specified time
                logger.debug("Requeue lock is already held by another worker")
            except (RedisConnectionError, RedisTimeoutError, RedisError):
                logger.exception(
                    "Transient Redis error in requeue loop while managing lock"
                )
            except Exception:
                logger.exception("Unexpected error in requeue loop while managing lock")
            finally:
                await asyncio.sleep(job_requeue_interval / 1000.0)

    # ------------------------------------------------------------------
    # Lifespan handler
    # ------------------------------------------------------------------
    @asynccontextmanager
    async def _lifespan(self, app: Starlette):
        # --- startup ---
        await self.queue.initialize()
        # mimic original behavior: use requeue_with_lock loop
        self._requeue_task = asyncio.create_task(self.requeue_with_lock())

        try:
            yield
        finally:
            # --- shutdown ---
            if self._requeue_task is not None:
                self._requeue_task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._requeue_task
            await self.queue.close()

    # ------------------------------------------------------------------
    # Routes definition
    # ------------------------------------------------------------------
    def _build_routes(self):
        return [
            # '/'
            Route("/", self._view_index, methods=["GET"]),
            # '/enqueue/<queue_type>/<queue_id>/'
            Route(
                "/enqueue/{queue_type}/{queue_id}/",
                self._view_enqueue,
                methods=["POST"],
            ),
            # '/dequeue/' defaults={'queue_type': 'default'}
            Route(
                "/dequeue/",
                self._view_dequeue_default,
                methods=["GET"],
            ),
            # '/dequeue/<queue_type>/'
            Route(
                "/dequeue/{queue_type}/",
                self._view_dequeue,
                methods=["GET"],
            ),
            # '/finish/<queue_type>/<queue_id>/<job_id>/'
            Route(
                "/finish/{queue_type}/{queue_id}/{job_id}/",
                self._view_finish,
                methods=["POST"],
            ),
            # '/interval/<queue_type>/<queue_id>/'
            Route(
                "/interval/{queue_type}/{queue_id}/",
                self._view_interval,
                methods=["POST"],
            ),
            # '/metrics/' defaults={'queue_type': None, 'queue_id': None}
            Route(
                "/metrics/",
                self._view_metrics,
                methods=["GET"],
            ),
            # '/metrics/<queue_type>/' defaults={'queue_id': None}
            Route(
                "/metrics/{queue_type}/",
                self._view_metrics,
                methods=["GET"],
            ),
            # '/metrics/<queue_type>/<queue_id>/'
            Route(
                "/metrics/{queue_type}/{queue_id}/",
                self._view_metrics,
                methods=["GET"],
            ),
            # '/deletequeue/<queue_type>/<queue_id>/'
            Route(
                "/deletequeue/{queue_type}/{queue_id}/",
                self._view_clear_queue,
                methods=["DELETE"],
            ),
            # '/deepstatus/'
            Route(
                "/deepstatus/",
                self._view_deep_status,
                methods=["GET"],
            ),
        ]

    # ------------------------------------------------------------------
    # Views (handlers) – re-implemented as async, keeping behavior & status codes
    # ------------------------------------------------------------------
    async def _view_index(self, request: Request):
        """Greetings at the index."""
        return JSONResponse({"message": "Hello, FQS!"})

    async def _view_enqueue(self, request: Request):
        """Enqueues a job into FQ."""
        queue_type = request.path_params["queue_type"]
        queue_id = request.path_params["queue_id"]

        response: JSONDict = {"status": "failure"}
        try:
            raw_body = await request.body()
            request_data: JSONDict = json.loads(raw_body or b"{}")
        except Exception as e:
            response["message"] = str(e)
            return JSONResponse(response, status_code=400)

        request_data.update(
            {
                "queue_type": queue_type,
                "queue_id": queue_id,
            }
        )

        # if max_queued_length is present in request param,
        # then only queue length will limit to this value
        max_queued_length = request_data.get("payload", {}).get(
            "max_queued_length", None
        )
        if max_queued_length is not None:
            current_queue_length = 0
            try:
                current_queue_length = await self.queue.get_queue_length(
                    queue_type, queue_id
                )
            except Exception as e:
                logger.warning(
                    "Failed to fetch queue length during enqueue",
                    exc_info=e,
                    extra={"queue_type": queue_type, "queue_id": queue_id},
                )

            if current_queue_length < max_queued_length:
                try:
                    response = await self.queue.enqueue(**request_data)
                    response["current_queue_length"] = current_queue_length
                except Exception as e:
                    logger.exception(
                        "Enqueue failed",
                        extra={"queue_type": queue_type, "queue_id": queue_id},
                    )
                    response["message"] = str(e)
                    return JSONResponse(response, status_code=400)

                return JSONResponse(response, status_code=201)
            else:
                response["message"] = "Max queue length reached"
                response["current_queue_length"] = current_queue_length
                return JSONResponse(response, status_code=429)
        else:
            try:
                response = await self.queue.enqueue(**request_data)
            except Exception as e:
                logger.exception(
                    "Enqueue failed",
                    extra={"queue_type": queue_type, "queue_id": queue_id},
                )
                response["message"] = str(e)
                return JSONResponse(response, status_code=400)

            return JSONResponse(response, status_code=201)

    async def _view_dequeue_default(self, request: Request):
        """Dequeues from default queue_type ('default')."""
        return await self._dequeue_with_type("default")

    async def _view_dequeue(self, request: Request):
        """Dequeues a job from FQ."""
        queue_type = request.path_params["queue_type"]
        return await self._dequeue_with_type(queue_type)

    async def _dequeue_with_type(self, queue_type: str):
        response: JSONDict = {"status": "failure"}
        request_data: JSONDict = {"queue_type": queue_type}

        try:
            response = await self.queue.dequeue(**request_data)
            if response["status"] == "failure":
                return JSONResponse(response, status_code=404)

            current_queue_length = 0
            try:
                current_queue_length = await self.queue.get_queue_length(
                    queue_type, response["queue_id"]
                )
            except Exception as e:
                logger.warning(
                    "Failed to fetch queue length during dequeue",
                    exc_info=e,
                    extra={"queue_type": queue_type, "queue_id": response["queue_id"]},
                )
            response["current_queue_length"] = current_queue_length
        except Exception as e:
            logger.exception("Dequeue failed", extra={"queue_type": queue_type})
            response["message"] = str(e)
            return JSONResponse(response, status_code=400)

        return JSONResponse(response)

    async def _view_finish(self, request: Request):
        """Marks a job as finished in FQ."""
        queue_type = request.path_params["queue_type"]
        queue_id = request.path_params["queue_id"]
        job_id = request.path_params["job_id"]

        response: JSONDict = {"status": "failure"}
        request_data: JSONDict = {
            "queue_type": queue_type,
            "queue_id": queue_id,
            "job_id": job_id,
        }

        try:
            response = await self.queue.finish(**request_data)
            if response["status"] == "failure":
                return JSONResponse(response, status_code=404)
        except Exception as e:
            logger.exception(
                "Finish failed",
                extra={"queue_type": queue_type, "queue_id": queue_id, "job_id": job_id},
            )
            response["message"] = str(e)
            return JSONResponse(response, status_code=400)

        return JSONResponse(response)

    async def _view_interval(self, request: Request):
        """Updates the queue interval in FQ."""
        queue_type = request.path_params["queue_type"]
        queue_id = request.path_params["queue_id"]

        response: JSONDict = {"status": "failure"}
        try:
            raw_body = await request.body()
            body: JSONDict = json.loads(raw_body or b"{}")
            interval = body["interval"]
        except Exception as e:
            response["message"] = str(e)
            return JSONResponse(response, status_code=400)

        request_data: JSONDict = {
            "queue_type": queue_type,
            "queue_id": queue_id,
            "interval": interval,
        }

        try:
            response = await self.queue.interval(**request_data)
            if response["status"] == "failure":
                return JSONResponse(response, status_code=404)
        except Exception as e:
            logger.exception(
                "Interval update failed",
                extra={"queue_type": queue_type, "queue_id": queue_id},
            )
            response["message"] = str(e)
            return JSONResponse(response, status_code=400)

        return JSONResponse(response)

    async def _view_metrics(self, request: Request):
        """Gets FQ metrics based on the params."""
        response: JSONDict = {"status": "failure"}
        request_data: JSONDict = {}

        # queue_type and/or queue_id may be absent depending on the route
        queue_type = request.path_params.get("queue_type")
        queue_id = request.path_params.get("queue_id")

        if queue_type is not None:
            request_data["queue_type"] = queue_type
        if queue_id is not None:
            request_data["queue_id"] = queue_id

        try:
            response = await self.queue.metrics(**request_data)
        except Exception as e:
            logger.exception("Metrics query failed", extra=request_data)
            response["message"] = str(e)
            return JSONResponse(response, status_code=400)

        return JSONResponse(response)

    async def _view_deep_status(self, request: Request):
        """Checks underlying data store health."""
        try:
            await self.queue.deep_status()
            response: JSONDict = {"status": "success"}
            return JSONResponse(response)
        except Exception as e:
            logger.exception("Deep status check failed")
            # preserve original behavior: raise generic exception -> 500
            raise Exception from e

    async def _view_clear_queue(self, request: Request):
        """Remove queue from FQ based on the queue_type and queue_id."""
        queue_type = request.path_params["queue_type"]
        queue_id = request.path_params["queue_id"]

        response: JSONDict = {"status": "failure"}
        try:
            raw_body = await request.body()
            request_data: JSONDict = json.loads(raw_body or b"{}")
        except Exception as e:
            response["message"] = str(e)
            return JSONResponse(response, status_code=400)

        request_data.update(
            {
                "queue_type": queue_type,
                "queue_id": queue_id,
            }
        )

        try:
            response = await self.queue.clear_queue(**request_data)
        except Exception as e:
            logger.exception(
                "Clear queue failed",
                extra={"queue_type": queue_type, "queue_id": queue_id},
            )
            response["message"] = str(e)
            return JSONResponse(response, status_code=400)

        return JSONResponse(response)


# ----------------------------------------------------------------------
# Setup helpers to create and configure the server
# ----------------------------------------------------------------------
def setup_server(
    config: FQConfig | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> FQServer:
    """Configure FQ server and return the server instance."""
    server_config = build_config_from_env(env) if config is None else config
    return FQServer(server_config)
