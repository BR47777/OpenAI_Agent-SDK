"""
a2a/server.py
A2A-compliant FastAPI server exposing the CodeReviewAgent.

Endpoints:
  GET  /.well-known/agent.json   → AgentCard
  POST /                         → JSON-RPC 2.0 (tasks/send, tasks/get)

Run:
  uvicorn a2a.server:app --port 8000
"""

from __future__ import annotations
import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from a2a.types import (
    AgentCard, AgentCapabilities, AgentSkill,
    Task, TaskState, Message,
    TaskSendParams, TaskStatusParams,
    JsonRpcRequest, JsonRpcResponse,
)
from a2a.task_store import store

app = FastAPI(title="CodeReview A2A Agent")

# ── Agent Card ────────────────────────────────────────────────────────────────

AGENT_CARD = AgentCard(
    name="CodeReviewAgent",
    description="Inspects Python source files, identifies bugs and security issues, applies fixes, and produces a structured report.",
    url="http://localhost:8000",
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="code_review",
            name="Code Review",
            description="Review Python files for bugs, security issues, and code quality.",
        ),
        AgentSkill(
            id="security_scan",
            name="Security Scan",
            description="Detect hardcoded secrets, SQL injection, and resource leaks.",
        ),
        AgentSkill(
            id="auto_fix",
            name="Auto Fix",
            description="Apply patches to fix identified issues and verify with shell execution.",
        ),
    ],
)


@app.get("/.well-known/agent.json")
async def agent_card():
    return AGENT_CARD.model_dump()


# ── JSON-RPC dispatcher ───────────────────────────────────────────────────────

@app.post("/")
async def jsonrpc(request: Request):
    body = await request.json()
    rpc = JsonRpcRequest(**body)

    if rpc.method == "tasks/send":
        result = await _tasks_send(TaskSendParams(**rpc.params))
    elif rpc.method == "tasks/get":
        result = await _tasks_get(TaskStatusParams(**rpc.params))
    else:
        return JSONResponse(
            JsonRpcResponse(
                id=rpc.id,
                error={"code": -32601, "message": f"Method not found: {rpc.method}"},
            ).model_dump()
        )

    return JSONResponse(JsonRpcResponse(id=rpc.id, result=result).model_dump())


# ── Method handlers ───────────────────────────────────────────────────────────

async def _tasks_send(params: TaskSendParams) -> dict:
    task = Task(
        id=params.id or Task().id,
        messages=[params.message],
    )
    store.create(task)

    output_dir = Path("sample_project/output").resolve()

    # Fire-and-forget — client polls tasks/get for status
    from a2a.executor import execute_task
    asyncio.create_task(execute_task(task, output_dir))

    return task.model_dump()


async def _tasks_get(params: TaskStatusParams) -> dict:
    task = store.get(params.id)
    if not task:
        raise ValueError(f"Task {params.id} not found")
    return task.model_dump()
