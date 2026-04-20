"""
tests/features/test_integrations.py
Feature: Standardized Integrations
Tests: MCP server wiring, Skills capability, AGENTS.md custom instructions.
"""
from __future__ import annotations
import pytest
from pathlib import Path

from agents import Agent
from agents.mcp import MCPServerStdio, MCPServerSse, MCPServerStdioParams, MCPServerSseParams
from agents.sandbox import Manifest, SandboxAgent
from agents.sandbox.capabilities import Shell, Skills
from agents.sandbox.capabilities.compaction import Compaction
from agents.sandbox.capabilities.skills import Skill
from agents.sandbox.entries import LocalDir


SKILL_NAMES = ["file_inspector", "security_scanner", "code_fixer", "report_writer"]


def _load_skill(name: str) -> Skill:
    content = (Path("skills/skill_docs") / f"{name}.md").read_text()
    desc = next(
        (l.split(":", 1)[1].strip() for l in content.splitlines() if l.startswith("description:")),
        "No description."
    )
    return Skill(name=name, description=desc, content=content)


# ── MCP Server Wiring ─────────────────────────────────────────────────────────

def test_mcp_stdio_params_command():
    params = MCPServerStdioParams(command="python3", args=["-m", "my_mcp_server"])
    assert params["command"] == "python3"
    assert "-m" in params["args"]


def test_mcp_stdio_params_env():
    params = MCPServerStdioParams(command="node", args=["server.js"], env={"PORT": "8080"})
    assert params["env"]["PORT"] == "8080"


def test_mcp_sse_params_url():
    params = MCPServerSseParams(url="http://localhost:9000/sse")
    assert "localhost" in params["url"]


def test_mcp_server_stdio_instantiates():
    server = MCPServerStdio(
        params=MCPServerStdioParams(command="echo", args=["hello"]),
        name="test-mcp",
        cache_tools_list=True,
    )
    assert server.name == "test-mcp"


def test_mcp_server_stdio_cache_tools():
    server = MCPServerStdio(
        params=MCPServerStdioParams(command="echo", args=[]),
        cache_tools_list=True,
    )
    assert server.cache_tools_list is True


def test_mcp_server_stdio_no_cache():
    server = MCPServerStdio(
        params=MCPServerStdioParams(command="echo", args=[]),
        cache_tools_list=False,
    )
    assert server.cache_tools_list is False


def test_agent_accepts_mcp_servers():
    """Agent.mcp_servers field accepts a list of MCP server instances."""
    server = MCPServerStdio(
        params=MCPServerStdioParams(command="echo", args=[]),
        name="code-tools",
    )
    agent = Agent(
        name="MCPAgent",
        model="gpt-4o-mini",
        instructions="Use MCP tools.",
        mcp_servers=[server],
    )
    assert len(agent.mcp_servers) == 1
    assert agent.mcp_servers[0].name == "code-tools"


def test_agent_accepts_multiple_mcp_servers():
    s1 = MCPServerStdio(params=MCPServerStdioParams(command="echo", args=[]), name="s1")
    s2 = MCPServerStdio(params=MCPServerStdioParams(command="echo", args=[]), name="s2")
    agent = Agent(name="A", model="gpt-4o-mini", instructions="x", mcp_servers=[s1, s2])
    assert len(agent.mcp_servers) == 2


# ── Skills Capability ─────────────────────────────────────────────────────────

def test_skill_loads_from_file():
    skill = _load_skill("file_inspector")
    assert skill.name == "file_inspector"
    assert len(skill.content) > 50


def test_skill_description_parsed_from_frontmatter():
    skill = _load_skill("security_scanner")
    assert skill.description != "No description."
    assert len(skill.description) > 10


def test_skill_content_contains_shell_commands():
    skill = _load_skill("security_scanner")
    assert "grep" in skill.content


def test_skill_code_fixer_contains_tee():
    skill = _load_skill("code_fixer")
    assert "tee" in skill.content


def test_skill_report_writer_contains_markdown_structure():
    skill = _load_skill("report_writer")
    assert "review_report.md" in skill.content


def test_skills_capability_mounts_all_four(tmp_path):
    skills_cap = Skills(skills=[_load_skill(n) for n in SKILL_NAMES])
    assert len(skills_cap.skills) == 4


def test_skills_capability_default_path():
    skills_cap = Skills(skills=[_load_skill("file_inspector")])
    assert skills_cap.skills_path == ".agents"


def test_skills_capability_custom_path():
    skills_cap = Skills(
        skills=[_load_skill("file_inspector")],
        skills_path="custom_agents",
    )
    assert skills_cap.skills_path == "custom_agents"


def test_skills_capability_type():
    skills_cap = Skills(skills=[_load_skill("file_inspector")])
    assert skills_cap.type == "skills"


def test_skills_mounts_into_manifest(tmp_path):
    """Skills.process_manifest adds .agents/<name> entries."""
    skills_cap = Skills(skills=[_load_skill("file_inspector")])
    manifest = Manifest(entries={"data/src": LocalDir(src=tmp_path)})
    updated = skills_cap.process_manifest(manifest)
    skill_paths = [str(k) for k in updated.entries.keys()]
    assert any("file_inspector" in p for p in skill_paths)


def test_skills_all_four_in_manifest(tmp_path):
    skills_cap = Skills(skills=[_load_skill(n) for n in SKILL_NAMES])
    manifest = Manifest(entries={"data/src": LocalDir(src=tmp_path)})
    updated = skills_cap.process_manifest(manifest)
    skill_paths = " ".join(str(k) for k in updated.entries.keys())
    for name in SKILL_NAMES:
        assert name in skill_paths


def test_sandbox_agent_with_skills_and_shell(tmp_path):
    agent = SandboxAgent(
        name="CodeReviewAgent",
        model="gpt-4o-mini",
        instructions=Path("AGENTS.md").read_text(),
        capabilities=[
            Skills(skills=[_load_skill(n) for n in SKILL_NAMES]),
            Shell(),
            Compaction(),
        ],
        default_manifest=Manifest(entries={
            "data/src":    LocalDir(src=tmp_path),
            "data/output": LocalDir(src=tmp_path),
        }),
    )
    cap_types = {type(c).__name__ for c in agent.capabilities}
    assert cap_types == {"Skills", "Shell", "Compaction"}


# ── AGENTS.md Custom Instructions ────────────────────────────────────────────

def test_agents_md_exists():
    assert Path("AGENTS.md").exists()


def test_agents_md_defines_workspace_layout():
    content = Path("AGENTS.md").read_text()
    assert "data/src" in content
    assert "data/output" in content


def test_agents_md_references_skills():
    content = Path("AGENTS.md").read_text()
    assert ".agents/" in content


def test_agents_md_defines_workflow_steps():
    content = Path("AGENTS.md").read_text()
    assert "Step 1" in content
    assert "Step 2" in content
    assert "Step 3" in content
    assert "Step 4" in content
    assert "Step 5" in content


def test_agents_md_references_all_skills():
    content = Path("AGENTS.md").read_text()
    assert "file_inspector" in content
    assert "security_scanner" in content
    assert "code_fixer" in content
    assert "report_writer" in content


def test_agents_md_has_rules_section():
    content = Path("AGENTS.md").read_text()
    assert "Rules" in content


def test_agents_md_loaded_into_agent_instructions(tmp_path):
    instructions = Path("AGENTS.md").read_text()
    agent = SandboxAgent(
        name="TestAgent",
        model="gpt-4o-mini",
        instructions=instructions,
        capabilities=[Shell()],
        default_manifest=Manifest(entries={"data": LocalDir(src=tmp_path)}),
    )
    assert "data/src" in agent.instructions
    assert ".agents/" in agent.instructions
