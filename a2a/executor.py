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



def _build_agent(output_dir: Path):
    """Build SandboxAgent — import deferred so tests can mock OPENAI_API_KEY."""
    from agents.sandbox import Manifest, SandboxAgent
    from agents.sandbox.entries import LocalDir
    from agents.sandbox.capabilities import Shell, Skills
    from agents.sandbox.capabilities.compaction import Compaction
    from agents.sandbox.capabilities.skills import Skill

    def _load_skill(name: str) -> Skill:
        content = (Path("skills/skill_docs") / f"{name}.md").read_text()
        desc = next(
            (l.split(":", 1)[1].strip() for l in content.splitlines() if l.startswith("description:")),
            "No description."
        )
        return Skill(name=name, description=desc, content=content)

    src = Path("sample_project/src").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    return SandboxAgent(
        name="CodeReviewAgent",
        model="gpt-4o",
        instructions=Path("AGENTS.md").read_text(),
        capabilities=[
            Skills(skills=[_load_skill(n) for n in ("file_inspector", "security_scanner", "code_fixer", "report_writer")]),
            Shell(),
            Compaction(),
        ],
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
