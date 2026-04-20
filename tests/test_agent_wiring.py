"""tests/test_agent_wiring.py
Verifies the SandboxAgent is correctly wired with Skills, Shell, Compaction
and the correct manifest — without making any real API calls.
"""
from pathlib import Path
from agents.sandbox import Manifest, SandboxAgent
from agents.sandbox.entries import LocalDir
from agents.sandbox.capabilities import Shell, Skills
from agents.sandbox.capabilities.compaction import Compaction
from agents.sandbox.capabilities.skills import Skill


SKILL_NAMES = ["file_inspector", "security_scanner", "code_fixer", "report_writer"]


def _load_skill(name: str) -> Skill:
    content = (Path("skills/skill_docs") / f"{name}.md").read_text()
    desc = next(
        (l.split(":", 1)[1].strip() for l in content.splitlines() if l.startswith("description:")),
        "No description."
    )
    return Skill(name=name, description=desc, content=content)


def _build_agent(src, output):
    return SandboxAgent(
        name="CodeReviewAgent",
        model="gpt-4o",
        instructions=Path("AGENTS.md").read_text(),
        capabilities=[
            Skills(skills=[_load_skill(n) for n in SKILL_NAMES]),
            Shell(),
            Compaction(),
        ],
        default_manifest=Manifest(
            entries={
                "data/src":    LocalDir(src=src),
                "data/output": LocalDir(src=output),
            }
        ),
    )


def test_agent_name(tmp_path):
    assert _build_agent(tmp_path, tmp_path).name == "CodeReviewAgent"


def test_agent_model(tmp_path):
    assert _build_agent(tmp_path, tmp_path).model == "gpt-4o"


def test_agent_has_three_capabilities(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    assert len(agent.capabilities) == 3


def test_agent_capability_types(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    types = {type(c).__name__ for c in agent.capabilities}
    assert types == {"Skills", "Shell", "Compaction"}


def test_agent_skills_count(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    skills_cap = next(c for c in agent.capabilities if isinstance(c, Skills))
    assert len(skills_cap.skills) == 4


def test_agent_skill_names(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    skills_cap = next(c for c in agent.capabilities if isinstance(c, Skills))
    names = {s.name for s in skills_cap.skills}
    assert names == set(SKILL_NAMES)


def test_agent_skill_descriptions_non_empty(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    skills_cap = next(c for c in agent.capabilities if isinstance(c, Skills))
    for skill in skills_cap.skills:
        assert skill.description and skill.description != "No description."


def test_agent_skill_content_non_empty(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    skills_cap = next(c for c in agent.capabilities if isinstance(c, Skills))
    for skill in skills_cap.skills:
        assert len(skill.content) > 50


def test_agent_manifest_entries(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    keys = set(agent.default_manifest.entries.keys())
    assert "data/src" in keys
    assert "data/output" in keys


def test_agent_instructions_references_skills(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    assert ".agents/" in agent.instructions


def test_agent_instructions_references_agents_md(tmp_path):
    agent = _build_agent(tmp_path, tmp_path)
    assert "AGENTS.md" in agent.instructions or "Workflow" in agent.instructions


def test_agent_manifest_src_points_to_correct_dir(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    out = tmp_path / "out"; out.mkdir()
    agent = _build_agent(src, out)
    assert agent.default_manifest.entries["data/src"].src == src
