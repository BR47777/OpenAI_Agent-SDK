# Architecture — Code Review & Auto-Fix Agent

## Overview

A sandboxed AI agent that inspects Python source files, identifies bugs and security issues,
applies patches, verifies fixes by running the code, and produces a structured report.
Built on the OpenAI Agents SDK (≥0.14.0) with native sandbox execution.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        agent.py (Orchestrator)                  │
│                                                                 │
│   ┌─────────────┐     ┌──────────────────────────────────────┐  │
│   │  AGENTS.md  │────▶│         SandboxAgent (gpt-4o)        │  │
│   │ (instructions)    │                                      │  │
│   └─────────────┘     │  ┌────────────┐  ┌────────────────┐  │  │
│                        │  │  Skills    │  │  Built-in Tools│  │  │
│   ┌─────────────┐     │  │────────────│  │────────────────│  │  │
│   │  Manifest   │────▶│  │file_insp.  │  │  apply_patch   │  │  │
│   │  data/src   │     │  │sec_scanner │  │  shell         │  │  │
│   │  data/output│     │  │report_writ.│  │  (MCP-native)  │  │  │
│   └─────────────┘     │  └────────────┘  └────────────────┘  │  │
│                        └──────────────────────────────────────┘  │
│                                    │                             │
│                    ┌───────────────▼──────────────┐             │
│                    │   UnixLocalSandboxClient      │             │
│                    │   (isolated execution env)    │             │
│                    └───────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### `agent.py`
Entry point. Wires together the SandboxAgent, Manifest, skills, and RunConfig.
Runs the agent loop via `Runner.run()` and prints the executive summary.

### `AGENTS.md`
Native agent instruction file consumed by the harness. Defines the agent's
workflow, workspace layout, and report format — separate from code.

### `skills/`
Modular Python tools registered with the agent via `@function_tool`.

| Skill | Purpose |
|---|---|
| `file_inspector.py` | List `.py` files, count lines — triage phase |
| `security_scanner.py` | Regex-based pre-scan for secrets, SQLi, resource leaks |
| `report_writer.py` | Persist structured markdown report to `data/output/` |

### `sample_project/src/`
Input code with intentional bugs:
- Resource leak (`open()` without context manager)
- `ZeroDivisionError` on empty list
- SQL injection via string formatting
- Hardcoded API secret
- Non-idiomatic loop (should use `enumerate`)

### `sample_project/output/`
Agent writes `review_report.md` here after completing the review.

---

## Agent Loop (Long-Horizon Task Flow)

```
Runner.run()
    │
    ├─ 1. list_python_files("data/src/")
    ├─ 2. count_lines(file)
    ├─ 3. scan_for_security_issues(file)
    ├─ 4. [LLM] Deep read + identify all bugs
    ├─ 5. apply_patch  ──▶  shell (verify)   [repeats per bug]
    ├─ 6. write_report("data/output/review_report.md", ...)
    └─ 7. final_output → executive summary
```

---

## Sandbox Architecture

```
┌──────────────────────────────────────────┐
│           Harness (agent.py)             │  ← credentials live here
│           State / Memory                 │  ← survives sandbox crash
└────────────────┬─────────────────────────┘
                 │  Manifest mount
┌────────────────▼─────────────────────────┐
│        UnixLocalSandboxClient            │  ← isolated compute
│        data/src/   data/output/          │  ← scoped filesystem
│        shell + apply_patch tools         │  ← model-generated code runs here
└──────────────────────────────────────────┘
```

Key security property: credentials never enter the sandbox. The harness
manages state externally, so a crashed container does not lose the run.

---

## Extending This Use Case

| Want to... | How |
|---|---|
| Use a cloud sandbox | Replace `UnixLocalSandboxClient` with E2B / Modal / Daytona client |
| Mount S3 data | Add `S3Dir(bucket=..., prefix=...)` to `Manifest.entries` |
| Add more skills | Create `skills/my_skill.py` with `@function_tool`, import in `agent.py` |
| Multi-file projects | `LocalDir` mounts entire directories recursively |
| Parallel subagents | Spawn multiple `Runner.run()` calls with isolated sandbox clients |

---

## Requirements

```
openai-agents>=0.14.0
OPENAI_API_KEY set in environment
```
