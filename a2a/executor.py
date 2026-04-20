"""
a2a/executor.py
Executes a Task by running the CodeReviewAgent in a sandbox.
Decoupled from HTTP so it can be tested independently.
"""

from __future__ import annotations
import asyncio
from pathlib import Path

from a2a.types import Task, TaskState, Message
from a2a.task_store import store

from skills.file_inspector import list_python_files, count_lines
from skills.security_scanner import scan_for_security_issues
from skills.report_writer import write_report


def _build_agent(output_dir: Path):
    """Build SandboxAgent — import deferred so tests can mock OPENAI_API_KEY."""
    from agents.sandbox import Manifest, SandboxAgent
    from agents.sandbox.entries import LocalDir

    src = Path("sample_project/src").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    return SandboxAgent(
        name="CodeReviewAgent",
        model="gpt-4o",
        instructions=Path("AGENTS.md").read_text(),
        tools=[list_python_files, count_lines, scan_for_security_issues, write_report],
        default_manifest=Manifest(
            entries={
                "data/src":    LocalDir(src=src),
                "data/output": LocalDir(src=output_dir),
            }
        ),
    )


async def execute_task(task: Task, output_dir: Path) -> None:
    """Run the agent for task.messages[-1].content and update task state."""
    store.update_state(task.id, TaskState.WORKING)
    user_message = task.messages[-1].content if task.messages else "Review all files."

    try:
        from agents import Runner
        from agents.run import RunConfig
        from agents.sandbox import SandboxRunConfig
        from agents.sandbox.sandboxes import UnixLocalSandboxClient

        agent = _build_agent(output_dir)
        result = await Runner.run(
            agent,
            user_message,
            run_config=RunConfig(
                sandbox=SandboxRunConfig(client=UnixLocalSandboxClient()),
            ),
        )

        task.messages.append(Message(role="agent", content=result.final_output))
        store.add_artifact(task.id, "review_report.md", result.final_output, "text/markdown")
        store.update_state(task.id, TaskState.COMPLETED)

    except Exception as exc:
        store.update_state(task.id, TaskState.FAILED, error=str(exc))
        raise
