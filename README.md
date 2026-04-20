# OpenAI Agent SDK — Code Review & Auto-Fix Agent

An AI-powered code review agent built on the **OpenAI Agents SDK (≥0.14.0)** that inspects Python source files, detects bugs and security vulnerabilities, applies fixes, verifies them by executing the code, and produces a structured markdown report — all inside an isolated sandbox.

Exposes the agent as an **A2A (Agent-to-Agent) protocol** HTTP service for multi-agent interoperability.

https://openai.com/index/the-next-evolution-of-the-agents-sdk/
---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Skills](#skills)
- [AGENTS.md — Custom Instructions](#agentsmd--custom-instructions)
- [A2A Protocol](#a2a-protocol)
- [Running Tests](#running-tests)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Extending](#extending)

---

## Features

| Feature | Description |
|---|---|
| **Automated bug detection** | Logic bugs, ZeroDivisionError, off-by-one, non-idiomatic patterns |
| **Security scanning** | Hardcoded secrets, SQL injection, resource leaks (grep pre-scan + LLM deep read) |
| **Shell code execution** | Runs fixed code inside sandbox to verify correctness |
| **SDK-native Skills** | Modular SKILL.md files mounted at `.agents/` inside the sandbox |
| **AGENTS.md instructions** | Custom agent workflow defined in a native instruction file |
| **Structured reporting** | Writes `review_report.md` with severity, line numbers, fix description, verification output |
| **Sandboxed execution** | Uses `UnixLocalSandboxClient` — model-generated code never touches host credentials |
| **A2A server** | FastAPI JSON-RPC 2.0 endpoint exposing the agent as a discoverable HTTP service |
| **A2A client** | Async HTTP client that sends tasks and polls for results |
| **91 tests** | Full pytest suite covering all modules — skills, A2A protocol, agent wiring |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        agent.py (Orchestrator)                      │
│                                                                     │
│   ┌─────────────┐     ┌────────────────────────────────────────┐    │
│   │  AGENTS.md  │────▶│       SandboxAgent (gpt-4o-mini)       │    │
│   │ (workflow)  │     │                                        │    │
│   └─────────────┘     │  ┌──────────┐ ┌───────┐ ┌──────────┐  │    │
│                        │  │  Skills  │ │ Shell │ │Compaction│  │    │
│   ┌─────────────┐     │  │──────────│ │───────│ │──────────│  │    │
│   │  Manifest   │────▶│  │file_insp │ │exec_  │ │context   │  │    │
│   │  data/src   │     │  │sec_scan  │ │command│ │window    │  │    │
│   │  data/output│     │  │code_fix  │ │tool   │ │mgmt      │  │    │
│   └─────────────┘     │  │rpt_write │ └───────┘ └──────────┘  │    │
│                        │  └──────────┘                         │    │
│                        └────────────────────────────────────────┘    │
│                                      │                               │
│                   ┌──────────────────▼──────────────────┐           │
│                   │       UnixLocalSandboxClient         │           │
│                   │   .agents/  data/src/  data/output/  │           │
│                   └─────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘

a2a/server.py (A2A HTTP Service)
    ├── GET  /.well-known/agent.json  →  AgentCard (discovery)
    └── POST /  (JSON-RPC 2.0)
            ├── tasks/send  →  create Task, fire execute_task() background
            └── tasks/get   →  return Task state + artifacts
```

---

## Project Structure

```
OpenAI_Agent-SDK/
│
├── agent.py                        # Standalone entry point
├── AGENTS.md                       # Native agent instruction file
├── ARCHITECTURE.md                 # Detailed architecture documentation
├── requirements.txt                # openai-agents>=0.14.0
├── pytest.ini                      # asyncio_mode = auto, testpaths = tests
├── .env                            # OPENAI_API_KEY (gitignored)
├── .env.example                    # Safe template to copy
│
├── skills/                         # Skill definitions
│   ├── file_inspector.py           # @function_tool: list_python_files, count_lines
│   ├── security_scanner.py         # @function_tool: scan_for_security_issues
│   ├── report_writer.py            # @function_tool: write_report
│   └── skill_docs/                 # SDK-native Skill SKILL.md files
│       ├── file_inspector.md       # Mounted at .agents/file_inspector/SKILL.md
│       ├── security_scanner.md     # Mounted at .agents/security_scanner/SKILL.md
│       ├── code_fixer.md           # Mounted at .agents/code_fixer/SKILL.md
│       └── report_writer.md        # Mounted at .agents/report_writer/SKILL.md
│
├── a2a/                            # Agent-to-Agent protocol layer
│   ├── __init__.py
│   ├── types.py                    # Pydantic models: Task, Message, AgentCard, JSON-RPC
│   ├── task_store.py               # In-memory task registry + module singleton
│   ├── executor.py                 # Decoupled agent execution logic
│   ├── server.py                   # FastAPI A2A server
│   └── client.py                   # Async HTTP client with polling
│
├── sample_project/
│   ├── src/
│   │   └── data_processor.py       # Intentionally buggy Python file (review target)
│   └── output/                     # Agent writes fixed files + review_report.md here
│
└── tests/
    ├── conftest.py                  # Shared fixtures
    ├── test_skill_file_inspector.py # 10 tests
    ├── test_skill_security_scanner.py # 12 tests
    ├── test_skill_report_writer.py  # 7 tests
    ├── test_a2a_types_and_store.py  # 22 tests
    ├── test_a2a_server.py           # 17 tests
    ├── test_a2a_executor.py         # 6 tests
    └── test_agent_wiring.py         # 12 tests
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/BR47777/OpenAI_Agent-SDK.git
cd OpenAI_Agent-SDK
pip install -r requirements.txt
pip install fastapi uvicorn httpx pytest pytest-asyncio
```

### 2. Set API Key

```bash
cp .env.example .env
# Edit .env and set your key:
# OPENAI_API_KEY=sk-...
```

### 3. Run the Agent (one-shot code review)

```bash
python agent.py
```

The agent will:
1. Read skills from `.agents/` inside the sandbox
2. Discover and scan `sample_project/src/data_processor.py`
3. Identify all 5 bugs via grep + LLM analysis
4. Write fixed files to `sample_project/output/`
5. Verify each fix by running `python data/output/<file>`
6. Print an executive summary

### 4. Run the A2A Server

```bash
uvicorn a2a.server:app --port 8000
```

### 5. Send a Task via the A2A Client

```bash
python -m a2a.client "Review all Python files for bugs and security issues."
```

---

## Skills

Skills are modular instruction files the agent reads inside the sandbox. They are mounted at `.agents/<name>/SKILL.md` via the SDK `Skills` capability.

| Skill | File | Description |
|---|---|---|
| `file_inspector` | `skills/skill_docs/file_inspector.md` | Discover and measure Python source files |
| `security_scanner` | `skills/skill_docs/security_scanner.md` | Grep patterns for secrets, SQLi, resource leaks |
| `code_fixer` | `skills/skill_docs/code_fixer.md` | Write fixed files with `tee`, verify with `python` |
| `report_writer` | `skills/skill_docs/report_writer.md` | Write structured markdown report |

### How Skills Work

```python
from agents.sandbox.capabilities import Skills
from agents.sandbox.capabilities.skills import Skill

skill = Skill(
    name="security_scanner",
    description="Detect hardcoded secrets, SQL injection, and resource leaks.",
    content=Path("skills/skill_docs/security_scanner.md").read_text(),
)

agent = SandboxAgent(
    capabilities=[Skills(skills=[skill]), Shell(), Compaction()],
    ...
)
```

Inside the sandbox the agent sees:
```
.agents/
└── security_scanner/
    └── SKILL.md   ← the agent reads this for step-by-step instructions
```

---

## AGENTS.md — Custom Instructions

`AGENTS.md` is the native agent instruction file consumed by the harness. It defines the agent's full workflow, workspace layout, and rules — separate from code.

```markdown
# Code Review Agent

## Workspace Layout
- data/src/     — input Python source files
- data/output/  — write fixed files and report here
- .agents/      — your skills library

## Workflow
Step 1 — Triage       → follow .agents/file_inspector/SKILL.md
Step 2 — Security     → follow .agents/security_scanner/SKILL.md
Step 3 — Deep Analysis → read each file fully with cat
Step 4 — Fix & Verify  → follow .agents/code_fixer/SKILL.md
Step 5 — Report        → follow .agents/report_writer/SKILL.md
```

---

## A2A Protocol

The agent is exposed as an **A2A-compliant** (Google Agent-to-Agent protocol) HTTP service.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/.well-known/agent.json` | Agent discovery — returns `AgentCard` |
| `POST` | `/` | JSON-RPC 2.0 dispatcher |

### JSON-RPC Methods

**`tasks/send`** — Submit a new task:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tasks/send",
  "params": {
    "message": { "role": "user", "content": "Review all Python files." }
  }
}
```

**`tasks/get`** — Poll task status:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tasks/get",
  "params": { "id": "<task-id>" }
}
```

### Task Lifecycle

```
SUBMITTED → WORKING → COMPLETED
                    → FAILED
                    → CANCELLED
```

### AgentCard (Discovery)

```json
{
  "name": "CodeReviewAgent",
  "description": "Inspects Python source files, identifies bugs and security issues...",
  "url": "http://localhost:8000",
  "version": "1.0.0",
  "skills": [
    { "id": "code_review",   "name": "Code Review" },
    { "id": "security_scan", "name": "Security Scan" },
    { "id": "auto_fix",      "name": "Auto Fix" }
  ]
}
```

---

## Running Tests

```bash
# Run all 91 tests
pytest

# Run with verbose output
pytest -v

# Run a specific module
pytest tests/test_a2a_server.py -v
pytest tests/test_skill_security_scanner.py -v
```

### Test Coverage

| Test File | Tests | What It Covers |
|---|---|---|
| `test_skill_file_inspector.py` | 10 | File discovery, line counting |
| `test_skill_security_scanner.py` | 12 | Regex patterns, false positives |
| `test_skill_report_writer.py` | 7 | File writing, overwrite, nested dirs |
| `test_a2a_types_and_store.py` | 22 | Pydantic models, TaskStore CRUD |
| `test_a2a_server.py` | 17 | AgentCard, tasks/send, tasks/get, JSON-RPC |
| `test_a2a_executor.py` | 6 | State transitions, error handling |
| `test_agent_wiring.py` | 12 | Skills, capabilities, manifest, instructions |
| **Total** | **91** | |

---

## Configuration

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key — set in `.env` |

### `.env` setup

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=sk-...
```

The key is loaded automatically via `python-dotenv` at startup in both `agent.py` and `a2a/server.py`.

---

## How It Works

### Agent Loop

```
Runner.run()
    │
    ├─ SDK injects Skills instructions into system prompt
    │     (.agents/file_inspector, security_scanner, code_fixer, report_writer)
    │
    ├─ Step 1: find data/src -name '*.py'          [Shell]
    ├─ Step 2: cat data/src/data_processor.py      [Shell]
    ├─ Step 3: grep patterns for security issues   [Shell]
    ├─ Step 4: [LLM] deep analysis of all bugs
    ├─ Step 5: tee data/output/data_processor.py   [Shell — write fix]
    ├─ Step 6: python data/output/data_processor.py [Shell — verify]
    ├─ Step 7: tee data/output/review_report.md    [Shell — write report]
    └─ Step 8: final_output → executive summary
```

### Sandbox Security Model

```
┌──────────────────────────────────────┐
│  Harness (agent.py)                  │  ← OPENAI_API_KEY lives here only
│  State / Task store                  │  ← survives sandbox crash
└──────────────┬───────────────────────┘
               │  Manifest mount
┌──────────────▼───────────────────────┐
│  UnixLocalSandboxClient              │  ← isolated compute
│  .agents/   data/src/  data/output/  │  ← scoped filesystem
│  exec_command tool (Shell)           │  ← model-generated code runs here
└──────────────────────────────────────┘
```

Credentials never enter the sandbox. The harness manages state externally.

### Bugs in `sample_project/src/data_processor.py`

The sample file contains 5 intentional bugs for the agent to find and fix:

| Line | Severity | Bug | Fix |
|---|---|---|---|
| 9 | MEDIUM | `open()` without context manager (resource leak) | `with open(...) as f:` |
| 13 | MEDIUM | `ZeroDivisionError` on empty list | `if not numbers: return 0.0` |
| 17 | HIGH | SQL injection via `%` string formatting | Parameterized query tuple |
| 22 | CRITICAL | Hardcoded API secret | `os.environ.get("OPENAI_API_KEY")` |
| 27 | LOW | `range(len(items))` anti-pattern | `enumerate(items)` |

---

## Extending

### Add a New Skill

1. Create `skills/skill_docs/my_skill.md` with YAML frontmatter:
```markdown
---
name: my_skill
description: What this skill does.
---
# Skill: My Skill
...shell commands and instructions...
```

2. Load it in `agent.py`:
```python
_load_skill("my_skill")   # add to the Skills list
```

### Swap the Sandbox

Replace `UnixLocalSandboxClient` with any supported provider:

```python
# E2B
from agents.sandbox.sandboxes import E2BSandboxClient
client = E2BSandboxClient(api_key="...")

# Modal
from agents.sandbox.sandboxes import ModalSandboxClient
client = ModalSandboxClient()

# Daytona / Cloudflare / Vercel / Blaxel / Runloop
```

### Mount Cloud Storage

```python
from agents.sandbox.entries import S3Dir

Manifest(entries={
    "data/src": S3Dir(bucket="my-bucket", prefix="src/"),
})
```

---

## Tech Stack

| Package | Purpose |
|---|---|
| `openai-agents>=0.14.0` | SandboxAgent, Runner, Skills, Shell, Compaction |
| `fastapi` | A2A HTTP server |
| `uvicorn` | ASGI server |
| `httpx` | Async HTTP client |
| `pydantic` | Data models |
| `python-dotenv` | `.env` loading |
| `pytest` + `pytest-asyncio` | Test runner |

---

## License

MIT
