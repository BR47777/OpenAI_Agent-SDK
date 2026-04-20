"""
Code Review & Auto-Fix Agent
Demonstrates: Skills capability, AGENTS.md custom instructions, Shell code execution.

Usage:
    python agent.py
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from agents import Runner
from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.capabilities import Shell, Skills
from agents.sandbox.capabilities.compaction import Compaction
from agents.sandbox.capabilities.skills import Skill
from agents.sandbox.entries import LocalDir
from agents.sandbox.sandboxes import UnixLocalSandboxClient


def _load_skill(name: str) -> Skill:
    """Load a Skill from its SKILL.md file in skills/skill_docs/."""
    content = (Path("skills/skill_docs") / f"{name}.md").read_text()
    return Skill(name=name, description=_parse_description(content), content=content)


def _parse_description(md: str) -> str:
    """Extract the description from YAML frontmatter."""
    for line in md.splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip()
    return "No description."


TASK = """
Read AGENTS.md for your full workflow instructions, then begin the code review.
Your skills are available under .agents/ — read each SKILL.md before executing its steps.
"""


async def main() -> None:
    src    = Path("sample_project/src").resolve()
    output = Path("sample_project/output").resolve()
    output.mkdir(exist_ok=True)

    # Load all four SDK-native Skills from their SKILL.md files
    skills = Skills(skills=[
        _load_skill("file_inspector"),
        _load_skill("security_scanner"),
        _load_skill("code_fixer"),
        _load_skill("report_writer"),
    ])

    agent = SandboxAgent(
        name="CodeReviewAgent",
        model="gpt-4o-mini",
        instructions=Path("AGENTS.md").read_text(),   # custom instructions via AGENTS.md
        capabilities=[
            skills,          # Skills: mounts .agents/<name>/SKILL.md inside sandbox
            Shell(),         # Shell: exec_command tool for code execution
            Compaction(),    # Compaction: context window management for long tasks
        ],
        default_manifest=Manifest(
            entries={
                "data/src":    LocalDir(src=src),
                "data/output": LocalDir(src=output),
            }
        ),
    )

    print(f"Agent: {agent.name}")
    print(f"Capabilities: {[type(c).__name__ for c in agent.capabilities]}")
    print(f"Skills mounted: {[s.name for s in skills.skills]}")
    print("Running...\n")

    result = await Runner.run(
        agent,
        TASK,
        run_config=RunConfig(
            sandbox=SandboxRunConfig(client=UnixLocalSandboxClient()),
        ),
    )

    print("\n" + "=" * 60)
    print("EXECUTIVE SUMMARY")
    print("=" * 60)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
