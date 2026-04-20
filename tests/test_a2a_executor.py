"""tests/test_a2a_executor.py"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from a2a.types import Task, TaskState, Message
from a2a.task_store import TaskStore


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_task(content="Review my code"):
    return Task(messages=[Message(role="user", content=content)])


# ── execute_task state transitions ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_task_sets_working_then_completed(tmp_path):
    from a2a import task_store as ts_module
    local_store = TaskStore()

    task = make_task()
    local_store.create(task)

    mock_result = MagicMock()
    mock_result.final_output = "Found 3 bugs. All fixed."

    with patch("a2a.task_store.store", local_store), \
         patch("a2a.executor.store", local_store), \
         patch("a2a.executor._build_agent", return_value=MagicMock()), \
         patch("agents.Runner.run", new=AsyncMock(return_value=mock_result)):

        from a2a.executor import execute_task
        await execute_task(task, tmp_path)

    assert local_store.get(task.id).state == TaskState.COMPLETED


@pytest.mark.asyncio
async def test_execute_task_appends_agent_message(tmp_path):
    local_store = TaskStore()
    task = make_task("Check security")
    local_store.create(task)

    mock_result = MagicMock()
    mock_result.final_output = "Security scan complete."

    with patch("a2a.task_store.store", local_store), \
         patch("a2a.executor.store", local_store), \
         patch("a2a.executor._build_agent", return_value=MagicMock()), \
         patch("agents.Runner.run", new=AsyncMock(return_value=mock_result)):

        from a2a.executor import execute_task
        await execute_task(task, tmp_path)

    messages = local_store.get(task.id).messages
    agent_msgs = [m for m in messages if m.role == "agent"]
    assert len(agent_msgs) == 1
    assert agent_msgs[0].content == "Security scan complete."


@pytest.mark.asyncio
async def test_execute_task_adds_artifact(tmp_path):
    local_store = TaskStore()
    task = make_task()
    local_store.create(task)

    mock_result = MagicMock()
    mock_result.final_output = "Done."

    with patch("a2a.task_store.store", local_store), \
         patch("a2a.executor.store", local_store), \
         patch("a2a.executor._build_agent", return_value=MagicMock()), \
         patch("agents.Runner.run", new=AsyncMock(return_value=mock_result)):

        from a2a.executor import execute_task
        await execute_task(task, tmp_path)

    artifacts = local_store.get(task.id).artifacts
    assert len(artifacts) == 1
    assert artifacts[0].name == "review_report.md"


@pytest.mark.asyncio
async def test_execute_task_sets_failed_on_exception(tmp_path):
    local_store = TaskStore()
    task = make_task()
    local_store.create(task)

    with patch("a2a.task_store.store", local_store), \
         patch("a2a.executor.store", local_store), \
         patch("a2a.executor._build_agent", return_value=MagicMock()), \
         patch("agents.Runner.run", new=AsyncMock(side_effect=RuntimeError("API error"))):

        from a2a.executor import execute_task
        with pytest.raises(RuntimeError):
            await execute_task(task, tmp_path)

    assert local_store.get(task.id).state == TaskState.FAILED


@pytest.mark.asyncio
async def test_execute_task_stores_error_message(tmp_path):
    local_store = TaskStore()
    task = make_task()
    local_store.create(task)

    with patch("a2a.task_store.store", local_store), \
         patch("a2a.executor.store", local_store), \
         patch("a2a.executor._build_agent", return_value=MagicMock()), \
         patch("agents.Runner.run", new=AsyncMock(side_effect=RuntimeError("timeout"))):

        from a2a.executor import execute_task
        with pytest.raises(RuntimeError):
            await execute_task(task, tmp_path)

    assert "timeout" in local_store.get(task.id).error


@pytest.mark.asyncio
async def test_execute_task_uses_last_message(tmp_path):
    local_store = TaskStore()
    task = Task(messages=[
        Message(role="user", content="first"),
        Message(role="user", content="second"),
    ])
    local_store.create(task)

    captured = {}
    async def mock_run(agent, message, run_config):
        captured["message"] = message
        r = MagicMock()
        r.final_output = "ok"
        return r

    with patch("a2a.task_store.store", local_store), \
         patch("a2a.executor.store", local_store), \
         patch("a2a.executor._build_agent", return_value=MagicMock()), \
         patch("agents.Runner.run", new=mock_run):

        from a2a.executor import execute_task
        await execute_task(task, tmp_path)

    assert captured["message"] == "second"
