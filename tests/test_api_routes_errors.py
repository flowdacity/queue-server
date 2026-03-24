# -*- coding: utf-8 -*-
# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

from unittest.mock import patch

import ujson as json

from tests.support import FQServerAsyncTestCase


class TestApiRoutesErrors(FQServerAsyncTestCase):
    async def test_enqueue_malformed_json(self):
        response = await self.client.post(
            "/enqueue/sms/johndoe/",
            content=b"invalid json {",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")
        self.assertIn("message", response.json())

    async def test_enqueue_empty_body(self):
        response = await self.client.post(
            "/enqueue/sms/johndoe/",
            content=b"",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")

    async def test_enqueue_with_max_queued_length_not_exceeded(self):
        request_params = {
            "job_id": "job-1",
            "payload": {"message": "Test 1", "max_queued_length": 10},
            "interval": 1000,
        }
        response = await self.client.post(
            "/enqueue/sms/test_queue_1/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "queued")
        self.assertEqual(response.json()["current_queue_length"], 0)

    async def test_enqueue_with_max_queued_length_exceeded(self):
        for i in range(3):
            request_params = {
                "job_id": f"job-{i}",
                "payload": {"message": f"Test {i}"},
                "interval": 1000,
            }
            await self.client.post(
                "/enqueue/sms/test_queue_2/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )

        request_params = {
            "job_id": "job-overflow",
            "payload": {"message": "Overflow", "max_queued_length": 2},
            "interval": 1000,
        }
        response = await self.client.post(
            "/enqueue/sms/test_queue_2/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["status"], "failure")
        self.assertIn("Max queue length reached", response.json()["message"])
        self.assertGreaterEqual(response.json()["current_queue_length"], 2)

    async def test_enqueue_get_queue_length_exception(self):
        request_params = {
            "job_id": "job-error",
            "payload": {"message": "Error test", "max_queued_length": 5},
            "interval": 1000,
        }

        with patch.object(
            self.queue, "get_queue_length", side_effect=Exception("Redis error")
        ):
            response = await self.client.post(
                "/enqueue/sms/test_queue_3/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["status"], "queued")
            self.assertEqual(response.json()["current_queue_length"], 0)

    async def test_enqueue_queue_enqueue_exception(self):
        request_params = {
            "job_id": "job-queue-error",
            "payload": {"message": "Queue error"},
            "interval": 1000,
        }

        with patch.object(self.queue, "enqueue", side_effect=Exception("Queue error")):
            response = await self.client.post(
                "/enqueue/sms/johndoe/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Queue error", response.json()["message"])

    async def test_enqueue_max_length_with_queue_exception(self):
        request_params = {
            "job_id": "job-with-max",
            "payload": {"message": "Test", "max_queued_length": 10},
            "interval": 1000,
        }

        with patch.object(self.queue, "enqueue", side_effect=Exception("Enqueue failed")):
            response = await self.client.post(
                "/enqueue/sms/johndoe/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Enqueue failed", response.json()["message"])

    async def test_dequeue_get_queue_length_exception(self):
        request_params = {
            "job_id": "job-for-dequeue",
            "payload": {"message": "Dequeue test"},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/dequeue_error_queue/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        with patch.object(
            self.queue, "get_queue_length", side_effect=Exception("Redis error")
        ):
            response = await self.client.get("/dequeue/sms/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "success")
            self.assertEqual(response.json()["current_queue_length"], 0)

    async def test_dequeue_exception_general(self):
        with patch.object(self.queue, "dequeue", side_effect=Exception("Dequeue failed")):
            response = await self.client.get("/dequeue/sms/")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Dequeue failed", response.json()["message"])

    async def test_finish_exception(self):
        with patch.object(self.queue, "finish", side_effect=Exception("Finish error")):
            response = await self.client.post("/finish/sms/johndoe/job-123/")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Finish error", response.json()["message"])

    async def test_interval_malformed_json(self):
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=b"invalid json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")

    async def test_interval_missing_interval_key(self):
        request_params = {"some_other_key": 5000}
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")

    async def test_interval_exception(self):
        request_params = {"interval": 5000}

        with patch.object(self.queue, "interval", side_effect=Exception("Interval error")):
            response = await self.client.post(
                "/interval/sms/johndoe/",
                content=json.dumps(request_params),
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Interval error", response.json()["message"])

    async def test_metrics_exception(self):
        with patch.object(self.queue, "metrics", side_effect=Exception("Metrics error")):
            response = await self.client.get("/metrics/")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Metrics error", response.json()["message"])

    async def test_metrics_with_queue_type_exception(self):
        with patch.object(self.queue, "metrics", side_effect=Exception("Metrics error")):
            response = await self.client.get("/metrics/sms/")
            self.assertEqual(response.status_code, 400)

    async def test_clear_queue_malformed_json(self):
        response = await self.client.request(
            "DELETE",
            "/deletequeue/sms/johndoe/",
            content=b"invalid json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "failure")

    async def test_clear_queue_exception(self):
        with patch.object(
            self.queue, "clear_queue", side_effect=Exception("Clear error")
        ):
            response = await self.client.delete("/deletequeue/sms/johndoe/")
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["status"], "failure")
            self.assertIn("Clear error", response.json()["message"])

    async def test_deep_status_exception(self):
        with patch.object(
            self.queue, "deep_status", side_effect=Exception("Status check failed")
        ):
            with self.assertRaises(Exception):
                await self.client.get("/deepstatus/")