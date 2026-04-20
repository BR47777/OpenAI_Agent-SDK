"""
tests/features/test_sandbox_execution.py
Feature: Native Sandbox Execution
Tests: Manifest abstraction, LocalDir mounts, portable workspaces, UnixLocalSandboxClient.
"""
from __future__ import annotations
import pytest
from pathlib import Path

from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.capabilities import Shell
from agents.sandbox.capabilities.compaction import Compaction
from agents.sandbox.entries import LocalDir
from agents.sandbox.sandboxes import UnixLocalSandboxClient


# ── Manifest Abstraction ──────────────────────────────────────────────────────

def test_manifest_empty():
    m = Manifest()
    assert m.entries == {}


def test_manifest_single_entry(tmp_path):
    m = Manifest(entries={"data/src": LocalDir(src=tmp_path)})
    assert "data/src" in m.entries


def test_manifest_localdir_src_path(tmp_path):
    entry = LocalDir(src=tmp_path)
    assert entry.src == tmp_path


def test_manifest_multiple_mounts(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    out = tmp_path / "out"; out.mkdir()
    m = Manifest(entries={
        "data/src":    LocalDir(src=src),
        "data/output": LocalDir(src=out),
    })
    assert len(m.entries) == 2
    assert "data/src" in m.entries
    assert "data/output" in m.entries


def test_manifest_entry_is_localdir(tmp_path):
    m = Manifest(entries={"data": LocalDir(src=tmp_path)})
    assert isinstance(m.entries["data"], LocalDir)


def test_manifest_copy_is_independent(tmp_path):
    m1 = Manifest(entries={"data": LocalDir(src=tmp_path)})
    m2 = m1.model_copy(deep=True)
    m2.entries["extra"] = LocalDir(src=tmp_path)
    assert "extra" not in m1.entries


def test_manifest_default_root():
    m = Manifest()
    assert m.root is not None


# ── Portable Workspaces ───────────────────────────────────────────────────────

def test_unix_local_sandbox_client_instantiates():
    assert UnixLocalSandboxClient() is not None


def test_unix_local_sandbox_backend_id():
    assert UnixLocalSandboxClient().backend_id == "unix_local"


def test_unix_local_sandbox_supports_default_options():
    assert UnixLocalSandboxClient().supports_default_options is True


@pytest.mark.asyncio
async def test_sandbox_creates_isolated_workspace(tmp_path):
    """Each sandbox session gets its own temp directory."""
    client = UnixLocalSandboxClient()
    manifest = Manifest(entries={"data/src": LocalDir(src=tmp_path)})
    s1 = await client.create(manifest=manifest)
    s2 = await client.create(manifest=manifest)
    assert s1 is not s2
    await client.delete(s1)
    await client.delete(s2)


@pytest.mark.asyncio
async def test_sandbox_mounts_files(tmp_path):
    """Files from LocalDir are accessible inside the sandbox after apply_manifest."""
    client = UnixLocalSandboxClient()
    src = tmp_path / "src"; src.mkdir()
    (src / "data_processor.py").write_text('print("mounted")')
    manifest = Manifest(entries={"data/src": LocalDir(src=src)})

    session = await client.create(manifest=manifest)
    await session.apply_manifest()
    result = await session.exec("cat data/src/data_processor.py")
    assert b"mounted" in result.stdout
    await client.delete(session)


@pytest.mark.asyncio
async def test_sandbox_shell_executes_python(tmp_path):
    """Shell can run Python inside the sandbox."""
    client = UnixLocalSandboxClient()
    session = await client.create(manifest=Manifest())
    result = await session.exec('python3 -c "print(2 + 2)"')
    assert b"4" in result.stdout
    assert result.exit_code == 0
    await client.delete(session)


@pytest.mark.asyncio
async def test_sandbox_exec_exit_code_zero_on_success(tmp_path):
    client = UnixLocalSandboxClient()
    session = await client.create(manifest=Manifest())
    result = await session.exec("echo ok")
    assert result.exit_code == 0
    await client.delete(session)


@pytest.mark.asyncio
async def test_sandbox_exec_exit_code_nonzero_on_failure(tmp_path):
    client = UnixLocalSandboxClient()
    session = await client.create(manifest=Manifest())
    result = await session.exec("exit 1", shell=True)
    assert result.exit_code != 0
    await client.delete(session)


@pytest.mark.asyncio
async def test_sandbox_output_dir_writable(tmp_path):
    """Agent can write files to the output directory inside sandbox."""
    client = UnixLocalSandboxClient()
    src = tmp_path / "src"; src.mkdir()
    out = tmp_path / "out"; out.mkdir()
    manifest = Manifest(entries={
        "data/src":    LocalDir(src=src),
        "data/output": LocalDir(src=out),
    })
    session = await client.create(manifest=manifest)
    await session.apply_manifest()
    result = await session.exec("echo 'hello' > data/output/test.txt && cat data/output/test.txt")
    assert b"hello" in result.stdout
    await client.delete(session)


@pytest.mark.asyncio
async def test_sandbox_find_python_files(tmp_path):
    """find command discovers mounted .py files."""
    client = UnixLocalSandboxClient()
    src = tmp_path / "src"; src.mkdir()
    (src / "app.py").write_text("x = 1")
    (src / "utils.py").write_text("y = 2")
    manifest = Manifest(entries={"data/src": LocalDir(src=src)})

    session = await client.create(manifest=manifest)
    await session.apply_manifest()
    result = await session.exec("find data/src -name '*.py' | sort")
    output = result.stdout.decode()
    assert "app.py" in output
    assert "utils.py" in output
    await client.delete(session)


@pytest.mark.asyncio
async def test_sandbox_python_script_runs_correctly(tmp_path):
    """A Python script mounted in the sandbox executes and produces correct output."""
    client = UnixLocalSandboxClient()
    src = tmp_path / "src"; src.mkdir()
    (src / "calc.py").write_text(
        "nums = [10, 20, 30]\n"
        "print(sum(nums) / len(nums))\n"
    )
    manifest = Manifest(entries={"data/src": LocalDir(src=src)})

    session = await client.create(manifest=manifest)
    await session.apply_manifest()
    result = await session.exec("python3 data/src/calc.py")
    assert b"20.0" in result.stdout
    assert result.exit_code == 0
    await client.delete(session)


# ── SandboxAgent + Manifest wiring ───────────────────────────────────────────

def test_sandbox_agent_default_manifest(tmp_path):
    agent = SandboxAgent(
        name="TestAgent",
        model="gpt-4o-mini",
        instructions="Test",
        capabilities=[Shell(), Compaction()],
        default_manifest=Manifest(entries={"data/src": LocalDir(src=tmp_path)}),
    )
    assert agent.default_manifest is not None
    assert "data/src" in agent.default_manifest.entries


def test_sandbox_agent_manifest_override_at_runtime(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    out = tmp_path / "out"; out.mkdir()
    override = Manifest(entries={
        "data/src":    LocalDir(src=src),
        "data/output": LocalDir(src=out),
    })
    cfg = SandboxRunConfig(client=UnixLocalSandboxClient(), manifest=override)
    assert cfg.manifest is override
    assert "data/output" in cfg.manifest.entries
