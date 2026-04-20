"""
Code Review & Auto-Fix Agent
Uses OpenAI Agents SDK sandbox to inspect, fix, run, and report on Python code.

Usage:
    export OPENAI_API_KEY=sk-...
    python agent.py
"""

import asyncio
import tempfile
import shutil
from pathlib import Path

from agents import Runner
from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.entries import LocalDir
from agents.sandbox.sandboxes import UnixLocalSandboxClient

from skills.file_inspector import list_python_files, count_lines
from skills.security_scanner import scan_for_security_issues
from skills.report_writer import write_report

TASK = """
You are reviewing the Python project mounted at data/src/.

Steps:
1. Use list_python_files to discover all .py files under data/src/
2. Use count_lines on each file for a quick size overview
3. Use scan_for_security_issues on each file to pre-flag security patterns
4. Read each file fully and identify ALL bugs (logic, security, style, resource leaks)
5. For each bug: apply a fix using apply_patch, then verify with shell
6. Use write_report to save your full findings to data/output/review_report.md
7. Print a one-paragraph executive summary at the end
"""


async def main() -> None:
    src = Path("sample_project/src").resolve()
    output = Path("sample_project/output").resolve()
    output.mkdir(exist_ok=True)

    agent = SandboxAgent(
        name="CodeReviewAgent",
        model="gpt-4o",
        instructions=Path("AGENTS.md").read_text(),
        tools=[list_python_files, count_lines, scan_for_security_issues, write_report],
        default_manifest=Manifest(
            entries={
                "data/src":    LocalDir(src=src),
                "data/output": LocalDir(src=output),
            }
        ),
    )

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

    report = output / "review_report.md"
    if report.exists():
        print(f"\nFull report saved → {report}")


if __name__ == "__main__":
    asyncio.run(main())
