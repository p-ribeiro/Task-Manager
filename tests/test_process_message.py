import json
import app.consumer as consumer
from app.consumer import process_message

class FakeRedis:
    def __init__(self):
        self.store = {}
        self.calls = []

    def set(self, k, v):
        self.calls.append((k, v))
        self.store[k] = v

class FakeChannel:
    def __init__(self):
        self.acked = []

    def basic_ack(self, delivery_tag=None, **kwargs):
        self.acked.append(delivery_tag)

class FakeMethod:
    def __init__(self, delivery_tag):
        self.delivery_tag = delivery_tag

def test_process_message_ack(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(consumer, "Redis", lambda *a, **k: fake_redis)
    # monkeypatch.setattr(consumer, "time", type("T", (), {"sleep": staticmethod(lambda x: None)))

    channel = FakeChannel()
    method = FakeMethod(123)
    task = {"id": "task1", "operation": "reverse", "data": "abc"}
    body = json.dumps(task).encode()

    process_message(channel, method, None, body)

    # final stored value should be Finished with reversed result
    assert "task1" in fake_redis.store
    stored = json.loads(fake_redis.store["task1"])
    assert stored["status"] == "Finished"
    assert stored["result"] == "cba"
    assert channel.acked == [123]

def test_process_message_no_ack(monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(consumer, "Redis", lambda *a, **k: fake_redis)
    # monkeypatch.setattr(consumer, "time", type("T", (), {"sleep": staticmethod(lambda x: None)}))

    channel = FakeChannel()
    method = None
    task = {"id": "task2", "operation": "uppercase", "data": "abC"}
    body = json.dumps(task)  # string body is also supported

    process_message(channel, method, None, body)

    stored = json.loads(fake_redis.store["task2"])
    assert stored["status"] == "Finished"
    assert stored["result"] == "ABC"
    assert channel.acked == []
