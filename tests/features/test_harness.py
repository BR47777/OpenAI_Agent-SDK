"""
tests/features/test_harness.py
Feature: Model-Native Harness
Tests: Configurable Memory, Sandbox-Aware Orchestration, RunConfig, Compaction.
"""
from __future__ import annotations
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.capabilities import Shell
from agents.sandbox.capabilities.compaction import Compaction
from agents.sandbox.capabilities.memory import (
    Memory, MemoryLayoutConfig, MemoryReadConfig, MemoryGenerateConfig,
)
from agents.sandbox.entries import LocalDir
from agents.sandbox.sandboxes import UnixLocalSandboxClient


# ── Memory Configuration ──────────────────────────────────────────────────────

def test_memory_layout_defaults():
    layout = MemoryLayoutConfig()
    assert layout.memories_dir == "memories"
    assert layout.sessions_dir == "sessions"


def test_memory_layout_custom():
    layout = MemoryLayoutConfig(memories_dir="agent_mem", sessions_dir="agent_sessions")
    assert layout.memories_dir == "agent_mem"
    assert layout.sessions_dir == "agent_sessions"


def test_memory_read_config_live_update_default():
    cfg = MemoryReadConfig()
    assert cfg.live_update is True


def test_memory_read_config_live_update_disabled():
    cfg = MemoryReadConfig(live_update=False)
    assert cfg.live_update is False


def test_memory_generate_config_defaults():
    cfg = MemoryGenerateConfig()
    assert cfg.max_raw_memories_for_consolidation == 256
    assert "mini" in cfg.phase_one_model


def test_memory_generate_config_custom_prompt():
    cfg = MemoryGenerateConfig(extra_prompt="Focus on security findings.")
    assert "security" in cfg.extra_prompt


def test_memory_generate_config_invalid_max():
    with pytest.raises(ValueError):
        MemoryGenerateConfig(max_raw_memories_for_consolidation=0)


def test_memory_generate_config_max_too_large():
    with pytest.raises(ValueError):
        MemoryGenerateConfig(max_raw_memories_for_consolidation=9999)


def test_memory_requires_read_or_generate():
    with pytest.raises(ValueError):
        Memory(read=None, generate=None)


def test_memory_read_only():
    m = Memory(read=MemoryReadConfig(), generate=None)
    assert m.read is not None
    assert m.generate is None


def test_memory_generate_only():
    m = Memory(read=None, generate=MemoryGenerateConfig())
    assert m.generate is not None
    assert m.read is None


def test_memory_requires_shell_capability():
    m = Memory(read=MemoryReadConfig(live_update=False), generate=None)
    assert "shell" in m.required_capability_types()


def test_memory_live_update_requires_filesystem_and_shell():
    m = Memory(read=MemoryReadConfig(live_update=True), generate=None)
    required = m.required_capability_types()
    assert "shell" in required
    assert "filesystem" in required


# ── Sandbox-Aware Orchestration ───────────────────────────────────────────────

def test_sandbox_run_config_client(tmp_path):
    client = UnixLocalSandboxClient()
    cfg = SandboxRunConfig(client=client)
    assert cfg.client is client


def test_sandbox_run_config_manifest_override(tmp_path):
    manifest = Manifest(entries={"data": LocalDir(src=tmp_path)})
    cfg = SandboxRunConfig(manifest=manifest)
    assert cfg.manifest is manifest


def test_run_config_sandbox_field(tmp_path):
    sandbox_cfg = SandboxRunConfig(client=UnixLocalSandboxClient())
    run_cfg = RunConfig(sandbox=sandbox_cfg)
    assert run_cfg.sandbox is sandbox_cfg


def test_run_config_workflow_name():
    cfg = RunConfig(workflow_name="Code Review Pipeline")
    assert cfg.workflow_name == "Code Review Pipeline"


def test_run_config_tracing_disabled():
    cfg = RunConfig(tracing_disabled=True)
    assert cfg.tracing_disabled is True


def test_run_config_group_id():
    cfg = RunConfig(group_id="session-abc-123")
    assert cfg.group_id == "session-abc-123"


def test_compaction_capability_type():
    c = Compaction()
    assert c.type == "compaction"


def test_agent_with_compaction(tmp_path):
    agent = SandboxAgent(
        name="TestAgent",
        model="gpt-4o-mini",
        instructions="Test",
        capabilities=[Shell(), Compaction()],
        default_manifest=Manifest(entries={"data": LocalDir(src=tmp_path)}),
    )
    types = {type(c).__name__ for c in agent.capabilities}
    assert "Compaction" in types
    assert "Shell" in types


def test_agent_with_memory_capability(tmp_path):
    agent = SandboxAgent(
        name="MemoryAgent",
        model="gpt-4o-mini",
        instructions="Test",
        capabilities=[
            Shell(),
            Memory(
                read=MemoryReadConfig(live_update=False),
                generate=MemoryGenerateConfig(extra_prompt="Track all bugs found."),
            ),
            Compaction(),
        ],
        default_manifest=Manifest(entries={"data": LocalDir(src=tmp_path)}),
    )
    cap_types = {type(c).__name__ for c in agent.capabilities}
    assert "Memory" in cap_types


def test_manifest_multiple_entries(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    out = tmp_path / "out"; out.mkdir()
    mem = tmp_path / "mem"; mem.mkdir()
    manifest = Manifest(entries={
        "data/src":    LocalDir(src=src),
        "data/output": LocalDir(src=out),
        "memories":    LocalDir(src=mem),
    })
    assert len(manifest.entries) == 3
    assert "memories" in manifest.entries
