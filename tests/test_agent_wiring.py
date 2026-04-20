"""tests/test_agent_wiring.py
Verifies the SandboxAgent is correctly wired with tools and manifest
without making any real API calls.
"""
from pathlib import Path
from agents.sandbox import Manifest, SandboxAgent
from agents.sandbox.entries import LocalDir

from skills.file_inspector import list_python_files, count_lines
from skills.security_scanner import scan_for_security_issues
from skills.report_writer import write_report


def _build_agent(src, output):
    return SandboxAgent(
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


def test_agent_name(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    assert agent.name == "CodeReviewAgent"


def test_agent_model(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    assert agent.model == "gpt-4o"


def test_agent_has_four_tools(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    assert len(agent.tools) == 4


def test_agent_tool_names(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    names = {t.name for t in agent.tools}
    assert names == {"list_python_files", "count_lines", "scan_for_security_issues", "write_report"}


def test_agent_manifest_entries(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    keys = set(agent.default_manifest.entries.keys())
    assert "data/src" in keys
    assert "data/output" in keys


def test_agent_instructions_loaded(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    assert "data/src" in agent.instructions
    assert "review_report.md" in agent.instructions


def test_agent_manifest_src_points_to_correct_dir(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    agent = _build_agent(src, out)
    entry = agent.default_manifest.entries["data/src"]
    assert entry.src == src
