import asyncio
import json
from typing import Optional

from fastapi.testclient import TestClient

from app.api import app, get_redis


class FakeRedis:
    def __init__(self):
        self.data = {"999": "example"}

    async def set(self, k, v):
        self.data[k] = v

    async def get(self, k) -> Optional[str]:
        if k not in self.data:
            return None
        return self.data[k]


def test_health_endpoint():
    """Expect a simple health check at GET /health returning JSON with a 'status' key."""
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "status" in body


def test_submit_task():
    """Test submitting a task via POST /submit-task endpoint."""
    task = {"operation": "reverse", "data": "To be reversed"}

    fake_redis = FakeRedis()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    with TestClient(app) as client:
        resp = client.post("/submit-task", json=task)
        assert resp.status_code == 201

        body = resp.json()
        assert "task_id" in body
        assert isinstance(body["task_id"], str)
        assert "status" in body
        assert body["status"] == "Queued"

        # check if the value was saved on the fake_redis
        data = asyncio.run(fake_redis.get(body["task_id"]))
        if data:
            data_json = json.loads(data)
            assert data_json["status"] == "Queued"

    app.dependency_overrides.clear()


def test_submit_incorrect_task():
    """Test submitting a task with incorrect data format via POST /submit-task endpoint"""
    task = {"operation": 1, "data": "my data"}
    with TestClient(app) as client:
        resp = client.post("/submit-task", json=task)
        assert not resp.status_code == 201


def test_get_task_status():
    """Test getting the task status via GET /task/{task_id} endpoint"""

    fake_redis = FakeRedis()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    with TestClient(app) as client:
        resp = client.get("/task/999")
        assert resp.status_code == 200

        body = resp.json()
        assert "status" in body
        assert body["status"] == "example"


def test_get_task_non_existent():
    """Test getting a task with a non existing {task_id} via GET /task/{task_id} endpoint"""

    fake_redis = FakeRedis()
    app.dependency_overrides[get_redis] = lambda: fake_redis

    with TestClient(app) as client:
        resp = client.get("/task/1")
        assert resp.status_code == 204
