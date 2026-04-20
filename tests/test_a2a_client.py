"""tests/test_a2a_client.py"""
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch


# ── get_agent_card ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_agent_card_returns_dict():
    from a2a.client import get_agent_card

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"name": "CodeReviewAgent", "skills": []}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    card = await get_agent_card(mock_client)
    assert card["name"] == "CodeReviewAgent"


@pytest.mark.asyncio
async def test_get_agent_card_calls_correct_url():
    from a2a.client import get_agent_card, BASE_URL

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    await get_agent_card(mock_client)
    mock_client.get.assert_called_once_with(f"{BASE_URL}/.well-known/agent.json")


# ── send_task ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_task_returns_task_dict():
    from a2a.client import send_task

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "jsonrpc": "2.0", "id": 1,
        "result": {"id": "task-abc", "state": "submitted", "messages": [], "artifacts": []}
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_task(mock_client, "Review my code")
    assert result["id"] == "task-abc"
    assert result["state"] == "submitted"


@pytest.mark.asyncio
async def test_send_task_posts_correct_method():
    from a2a.client import send_task

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"result": {"id": "x", "state": "submitted"}}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    await send_task(mock_client, "hello")
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
    assert payload["method"] == "tasks/send"


@pytest.mark.asyncio
async def test_send_task_includes_message_content():
    from a2a.client import send_task

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"result": {"id": "x", "state": "submitted"}}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    await send_task(mock_client, "Check for secrets")
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
    assert payload["params"]["message"]["content"] == "Check for secrets"


# ── get_task ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_task_returns_task():
    from a2a.client import get_task

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "result": {"id": "task-abc", "state": "completed", "messages": [], "artifacts": []}
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await get_task(mock_client, "task-abc")
    assert result["state"] == "completed"


@pytest.mark.asyncio
async def test_get_task_posts_correct_method():
    from a2a.client import get_task

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"result": {"id": "x", "state": "working"}}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    await get_task(mock_client, "task-xyz")
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs.args[1]
    assert payload["method"] == "tasks/get"
    assert payload["params"]["id"] == "task-xyz"
