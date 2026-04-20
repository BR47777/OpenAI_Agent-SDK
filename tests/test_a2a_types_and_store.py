"""tests/test_a2a_types_and_store.py"""
import time
import pytest
from a2a.types import (
    Task, TaskState, Message, Artifact,
    AgentCard, AgentCapabilities, AgentSkill,
    JsonRpcRequest, JsonRpcResponse,
    TaskSendParams, TaskStatusParams,
)
from a2a.task_store import TaskStore


# ── Task model ────────────────────────────────────────────────────────────────

def test_task_default_state():
    t = Task()
    assert t.state == TaskState.SUBMITTED


def test_task_auto_id():
    t1, t2 = Task(), Task()
    assert t1.id != t2.id


def test_task_has_timestamps():
    t = Task()
    assert t.created_at > 0
    assert t.updated_at > 0


def test_task_serialises():
    t = Task(messages=[Message(role="user", content="hello")])
    d = t.model_dump()
    assert d["state"] == "submitted"
    assert d["messages"][0]["content"] == "hello"


# ── Message model ─────────────────────────────────────────────────────────────

def test_message_roles():
    u = Message(role="user", content="hi")
    a = Message(role="agent", content="hello")
    assert u.role == "user"
    assert a.role == "agent"


# ── Artifact model ────────────────────────────────────────────────────────────

def test_artifact_defaults():
    art = Artifact(name="report.md", content="# Report")
    assert art.mime_type == "text/plain"


# ── AgentCard ─────────────────────────────────────────────────────────────────

def test_agent_card_serialises():
    card = AgentCard(
        name="TestAgent",
        description="A test agent",
        url="http://localhost:8000",
        skills=[AgentSkill(id="s1", name="Skill1", description="Does stuff")],
    )
    d = card.model_dump()
    assert d["name"] == "TestAgent"
    assert len(d["skills"]) == 1


def test_agent_card_default_capabilities():
    card = AgentCard(name="A", description="B", url="http://x")
    assert card.capabilities.streaming is False
    assert card.capabilities.push_notifications is False


# ── JSON-RPC models ───────────────────────────────────────────────────────────

def test_jsonrpc_request_defaults():
    r = JsonRpcRequest(method="tasks/send")
    assert r.jsonrpc == "2.0"
    assert r.params == {}


def test_jsonrpc_response_result():
    r = JsonRpcResponse(id=1, result={"state": "completed"})
    assert r.result["state"] == "completed"
    assert r.error is None


def test_jsonrpc_response_error():
    r = JsonRpcResponse(id=1, error={"code": -32601, "message": "Not found"})
    assert r.error["code"] == -32601
    assert r.result is None


# ── TaskStore ─────────────────────────────────────────────────────────────────

def test_store_create_and_get():
    s = TaskStore()
    t = Task()
    s.create(t)
    assert s.get(t.id) is t


def test_store_get_missing_returns_none():
    s = TaskStore()
    assert s.get("nonexistent") is None


def test_store_update_state():
    s = TaskStore()
    t = Task()
    s.create(t)
    s.update_state(t.id, TaskState.WORKING)
    assert s.get(t.id).state == TaskState.WORKING


def test_store_update_state_with_error():
    s = TaskStore()
    t = Task()
    s.create(t)
    s.update_state(t.id, TaskState.FAILED, error="boom")
    assert s.get(t.id).error == "boom"


def test_store_add_artifact():
    s = TaskStore()
    t = Task()
    s.create(t)
    s.add_artifact(t.id, "report.md", "# Report", "text/markdown")
    assert len(s.get(t.id).artifacts) == 1
    assert s.get(t.id).artifacts[0].name == "report.md"


def test_store_updated_at_changes():
    s = TaskStore()
    t = Task()
    s.create(t)
    before = t.updated_at
    time.sleep(0.01)
    s.update_state(t.id, TaskState.COMPLETED)
    assert s.get(t.id).updated_at >= before


def test_store_all():
    s = TaskStore()
    s.create(Task())
    s.create(Task())
    assert len(s.all()) == 2


def test_store_multiple_artifacts():
    s = TaskStore()
    t = Task()
    s.create(t)
    s.add_artifact(t.id, "a.md", "content a")
    s.add_artifact(t.id, "b.md", "content b")
    assert len(s.get(t.id).artifacts) == 2


# ── TaskSendParams / TaskStatusParams ─────────────────────────────────────────

def test_task_send_params_optional_id():
    p = TaskSendParams(message=Message(role="user", content="go"))
    assert p.id is None


def test_task_send_params_with_id():
    p = TaskSendParams(id="abc-123", message=Message(role="user", content="go"))
    assert p.id == "abc-123"


def test_task_status_params():
    p = TaskStatusParams(id="xyz")
    assert p.id == "xyz"
