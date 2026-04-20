"""tests/test_a2a_server.py"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from a2a.server import app
from a2a.task_store import store
from a2a.types import Task, TaskState, Message


client = TestClient(app)


# ── Agent Card ────────────────────────────────────────────────────────────────

def test_agent_card_endpoint():
    r = client.get("/.well-known/agent.json")
    assert r.status_code == 200


def test_agent_card_has_name():
    r = client.get("/.well-known/agent.json")
    assert r.json()["name"] == "CodeReviewAgent"


def test_agent_card_has_skills():
    r = client.get("/.well-known/agent.json")
    skills = r.json()["skills"]
    assert len(skills) >= 3
    skill_ids = [s["id"] for s in skills]
    assert "code_review" in skill_ids
    assert "security_scan" in skill_ids
    assert "auto_fix" in skill_ids


def test_agent_card_has_url():
    r = client.get("/.well-known/agent.json")
    assert "url" in r.json()


def test_agent_card_has_capabilities():
    r = client.get("/.well-known/agent.json")
    assert "capabilities" in r.json()


# ── tasks/send ────────────────────────────────────────────────────────────────

def _noop_create_task(coro):
    """Consume the coroutine without scheduling it, suppressing unawaited warnings."""
    coro.close()


def _send_payload(message="Review my code", task_id=None):
    params = {"message": {"role": "user", "content": message}}
    if task_id:
        params["id"] = task_id
    return {"jsonrpc": "2.0", "id": 1, "method": "tasks/send", "params": params}


def test_tasks_send_returns_task():
    with patch("a2a.server.asyncio.create_task", side_effect=_noop_create_task):
        r = client.post("/", json=_send_payload())
    assert r.status_code == 200
    result = r.json()["result"]
    assert "id" in result
    assert result["state"] == "submitted"


def test_tasks_send_stores_message():
    with patch("a2a.server.asyncio.create_task", side_effect=_noop_create_task):
        r = client.post("/", json=_send_payload("Check for SQL injection"))
    result = r.json()["result"]
    assert result["messages"][0]["content"] == "Check for SQL injection"


def test_tasks_send_custom_id():
    with patch("a2a.server.asyncio.create_task", side_effect=_noop_create_task):
        r = client.post("/", json=_send_payload(task_id="my-task-001"))
    assert r.json()["result"]["id"] == "my-task-001"


def test_tasks_send_jsonrpc_envelope():
    with patch("a2a.server.asyncio.create_task", side_effect=_noop_create_task):
        r = client.post("/", json=_send_payload())
    body = r.json()
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == 1
    assert "result" in body


# ── tasks/get ─────────────────────────────────────────────────────────────────

def test_tasks_get_existing():
    t = Task(messages=[Message(role="user", content="hello")])
    store.create(t)
    payload = {"jsonrpc": "2.0", "id": 2, "method": "tasks/get", "params": {"id": t.id}}
    r = client.post("/", json=payload)
    assert r.status_code == 200
    assert r.json()["result"]["id"] == t.id


def test_tasks_get_state_reflects_store():
    t = Task()
    store.create(t)
    store.update_state(t.id, TaskState.COMPLETED)
    payload = {"jsonrpc": "2.0", "id": 3, "method": "tasks/get", "params": {"id": t.id}}
    r = client.post("/", json=payload)
    assert r.json()["result"]["state"] == "completed"


def test_tasks_get_unknown_method():
    payload = {"jsonrpc": "2.0", "id": 9, "method": "tasks/unknown", "params": {}}
    r = client.post("/", json=payload)
    assert r.status_code == 200
    assert "error" in r.json()
    assert r.json()["error"]["code"] == -32601


def test_tasks_get_returns_artifacts():
    t = Task()
    store.create(t)
    store.add_artifact(t.id, "report.md", "# Report content", "text/markdown")
    payload = {"jsonrpc": "2.0", "id": 4, "method": "tasks/get", "params": {"id": t.id}}
    r = client.post("/", json=payload)
    artifacts = r.json()["result"]["artifacts"]
    assert len(artifacts) == 1
    assert artifacts[0]["name"] == "report.md"


# ── JSON-RPC structure ────────────────────────────────────────────────────────

def test_response_always_has_jsonrpc_version():
    with patch("a2a.server.asyncio.create_task", side_effect=_noop_create_task):
        r = client.post("/", json=_send_payload())
    assert r.json()["jsonrpc"] == "2.0"


def test_response_id_echoes_request():
    with patch("a2a.server.asyncio.create_task", side_effect=_noop_create_task):
        r = client.post("/", json={**_send_payload(), "id": 42})
    assert r.json()["id"] == 42
