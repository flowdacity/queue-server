# -*- coding: utf-8 -*-
# Copyright (c) 2025 Flowdacity Development Team. See LICENSE.txt for details.

import ujson as json

from tests.support import FQServerAsyncTestCase


class TestApiRoutesCore(FQServerAsyncTestCase):
    async def test_root(self):
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello, FQS!"})

    async def test_enqueue(self):
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        response = await self.client.post(
            "/enqueue/sms/johdoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "queued")

        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf1d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
            "requeue_limit": 10,
        }
        response = await self.client.post(
            "/enqueue/sms/johdoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "queued")

    async def test_dequeue_fail(self):
        response = await self.client.get("/dequeue/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

        response = await self.client.get("/dequeue/sms/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

    async def test_dequeue(self):
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        response = await self.client.get("/dequeue/sms/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["job_id"], "ef022088-d2b3-44ad-bf0d-a93d6d93b82c")
        self.assertEqual(data["payload"], {"message": "Hello, world."})
        self.assertEqual(data["queue_id"], "johndoe")
        self.assertEqual(data["requeues_remaining"], -1)

    async def test_finish_fail(self):
        response = await self.client.post(
            "/finish/sms/johndoe/ef022088-d2b3-44ad-bf0d-a93d6d93b82c/"
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "failure")

    async def test_finish(self):
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        await self.client.get("/dequeue/sms/")

        response = await self.client.post(
            "/finish/sms/johndoe/ef022088-d2b3-44ad-bf0d-a93d6d93b82c/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    async def test_interval(self):
        request_params = {
            "job_id": "ef022088-d2b3-44ad-bf0d-a93d6d93b82c",
            "payload": {"message": "Hello, world."},
            "interval": 1000,
        }
        await self.client.post(
            "/enqueue/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )

        request_params = {"interval": 5000}
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.json()["status"], "success")

    async def test_interval_fail(self):
        request_params = {"interval": 5000}
        response = await self.client.post(
            "/interval/sms/johndoe/",
            content=json.dumps(request_params),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.json()["status"], "failure")

    async def test_metrics(self):
        response = await self.client.get("/metrics/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_types", data)
        self.assertIn("enqueue_counts", data)
        self.assertIn("dequeue_counts", data)

    async def test_metrics_with_queue_type(self):
        response = await self.client.get("/metrics/sms/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_ids", data)

    async def test_metrics_with_queue_type_and_queue_id(self):
        response = await self.client.get("/metrics/sms/johndoe/")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("queue_length", data)
        self.assertIn("enqueue_counts", data)
        self.assertIn("dequeue_counts", data)

    async def test_deep_status_success(self):
        response = await self.client.get("/deepstatus/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")