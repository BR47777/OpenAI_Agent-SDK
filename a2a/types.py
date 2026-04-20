"""
a2a/types.py
A2A Protocol data models — Task, Message, AgentCard, TaskState.
Follows the Google A2A spec: https://google.github.io/A2A
"""

from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid
import time


class TaskState(str, Enum):
    SUBMITTED  = "submitted"
    WORKING    = "working"
    COMPLETED  = "completed"
    FAILED     = "failed"
    CANCELLED  = "cancelled"


class Message(BaseModel):
    role: str                        # "user" | "agent"
    content: str


class Artifact(BaseModel):
    name: str
    mime_type: str = "text/plain"
    content: str


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: TaskState = TaskState.SUBMITTED
    messages: list[Message] = []
    artifacts: list[Artifact] = []
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    error: str | None = None


class TaskSendParams(BaseModel):
    id: str | None = None
    message: Message


class TaskStatusParams(BaseModel):
    id: str


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    input_modes: list[str] = ["text"]
    output_modes: list[str] = ["text"]


class AgentCapabilities(BaseModel):
    streaming: bool = False
    push_notifications: bool = False


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: AgentCapabilities = AgentCapabilities()
    skills: list[AgentSkill] = []
    default_input_modes: list[str] = ["text"]
    default_output_modes: list[str] = ["text"]


# JSON-RPC envelope helpers
class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Any = None
    method: str
    params: dict = {}


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Any = None
    result: Any = None
    error: Any = None
