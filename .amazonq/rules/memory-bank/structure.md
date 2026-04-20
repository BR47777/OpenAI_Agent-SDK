# Project Structure

## Directory Layout

```
OpenAI_Agent-SDK/
├── agent.py                  # Standalone entry point — wires SandboxAgent and runs one-shot review
├── AGENTS.md                 # Native agent instruction file (workflow, workspace layout, report format)
├── ARCHITECTURE.md           # Architecture documentation
├── requirements.txt          # Single dependency: openai-agents>=0.14.0
├── pytest.ini                # Test configuration
├── .env / .env.example       # OPENAI_API_KEY environment config
│
├── a2a/                      # Agent-to-Agent (A2A) protocol layer
│   ├── __init__.py
│   ├── types.py              # Pydantic data models (Task, Message, AgentCard, JSON-RPC envelopes)
│   ├── task_store.py         # In-memory task store with module-level singleton `store`
│   ├── executor.py           # Decoupled agent execution logic (builds SandboxAgent, runs task)
│   ├── server.py             # FastAPI A2A server (GET /.well-known/agent.json, POST / JSON-RPC)
│   └── client.py             # Async HTTP client — sends tasks and polls for completion
│
├── skills/                   # Modular @function_tool skills registered with the agent
│   ├── file_inspector.py     # list_python_files, count_lines
│   ├── security_scanner.py   # scan_for_security_issues (regex pre-scan)
│   └── report_writer.py      # write_report (persists markdown to output dir)
│
├── sample_project/           # Input/output workspace mounted into the sandbox
│   ├── src/
│   │   └── data_processor.py # Intentionally buggy Python file (the review target)
│   └── output/               # Agent writes fixed files and review_report.md here
│
└── tests/                    # pytest test suite
    ├── conftest.py
    ├── test_a2a_client.py
    ├── test_a2a_executor.py
    ├── test_a2a_server.py
    ├── test_a2a_types_and_store.py
    ├── test_agent_wiring.py
    ├── test_skill_file_inspector.py
    ├── test_skill_report_writer.py
    └── test_skill_security_scanner.py
```

## Core Components and Relationships

```
agent.py (standalone)
    └── SandboxAgent (gpt-4o) + Shell + Compaction capabilities
            └── Manifest → LocalDir(sample_project/src), LocalDir(sample_project/output)
            └── Runner.run() → UnixLocalSandboxClient

a2a/server.py (A2A HTTP service)
    ├── GET /.well-known/agent.json → AgentCard (discovery)
    └── POST / (JSON-RPC 2.0)
            ├── tasks/send → creates Task in store, fires execute_task() as background task
            └── tasks/get  → returns Task state from store

a2a/executor.py
    └── execute_task(task, output_dir)
            ├── _build_agent() → same SandboxAgent as agent.py
            └── updates task state: SUBMITTED → WORKING → COMPLETED | FAILED

a2a/task_store.py
    └── TaskStore (in-memory dict) + module singleton `store`

skills/ (registered via @function_tool)
    ├── list_python_files, count_lines  (file_inspector.py)
    ├── scan_for_security_issues        (security_scanner.py)
    └── write_report                    (report_writer.py)
```

## Architectural Patterns

- **Sandbox isolation**: credentials stay in the harness; model-generated code runs in `UnixLocalSandboxClient`
- **Decoupled executor**: `a2a/executor.py` separates agent execution from HTTP concerns, enabling independent testing
- **Fire-and-forget + polling**: `tasks/send` returns immediately; clients poll `tasks/get` for status
- **Module-level singleton**: `store = TaskStore()` in `task_store.py` shared across the server process
- **Deferred imports in executor**: SDK imports inside `_build_agent()` so tests can mock `OPENAI_API_KEY` before import
- **Swappable sandbox**: `UnixLocalSandboxClient` can be replaced with E2B/Modal/Daytona without changing agent logic
