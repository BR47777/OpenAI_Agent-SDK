"""
a2a/task_store.py
In-memory task store. Replace with Redis/DB for production.
"""

from __future__ import annotations
from a2a.types import Task, TaskState
import time


class TaskStore:
    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def create(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def update_state(self, task_id: str, state: TaskState, error: str | None = None) -> Task:
        task = self._tasks[task_id]
        task.state = state
        task.updated_at = time.time()
        if error:
            task.error = error
        return task

    def add_artifact(self, task_id: str, name: str, content: str, mime_type: str = "text/plain"):
        from a2a.types import Artifact
        task = self._tasks[task_id]
        task.artifacts.append(Artifact(name=name, content=content, mime_type=mime_type))
        task.updated_at = time.time()

    def all(self) -> list[Task]:
        return list(self._tasks.values())


# module-level singleton
store = TaskStore()
