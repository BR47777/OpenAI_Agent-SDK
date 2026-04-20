# Technology Stack

## Languages & Runtime
- Python 3.x (async/await throughout)
- No frontend — CLI + HTTP API only

## Core Dependencies
| Package | Version | Purpose |
|---|---|---|
| `openai-agents` | >=0.14.0 | OpenAI Agents SDK — SandboxAgent, Runner, function_tool, Shell, Compaction |
| `fastapi` | (transitive) | A2A HTTP server |
| `uvicorn` | (transitive) | ASGI server for FastAPI |
| `httpx` | (transitive) | Async HTTP client for A2A client |
| `pydantic` | (transitive) | Data models (BaseModel, Field) |
| `python-dotenv` | (transitive) | `.env` loading via `load_dotenv()` |
| `pytest` | dev | Test runner |
| `pytest-asyncio` | dev | Async test support (`asyncio_mode = auto`) |

## Environment Configuration
```
OPENAI_API_KEY=<your-openai-api-key>   # Required — set in .env
```
Copy `.env.example` to `.env` and fill in the key.

## Development Commands

### Run the standalone agent (one-shot code review)
```bash
python agent.py
```

### Run the A2A server
```bash
uvicorn a2a.server:app --port 8000
```

### Send a task via the A2A client
```bash
python -m a2a.client "Review all Python files for bugs and security issues."
```

### Run tests
```bash
pytest
```

### Run tests with output
```bash
pytest -v
```

## Test Configuration
- `pytest.ini`: `asyncio_mode = auto`, `testpaths = tests`
- All async tests work without explicit `@pytest.mark.asyncio` decorator
- `conftest.py` provides shared fixtures: `sample_py_file`, `empty_py_file`, `output_dir` (all use `tmp_path`)

## Key SDK Concepts Used
- `SandboxAgent` — agent with sandboxed execution environment
- `Manifest` + `LocalDir` — mounts local directories into the sandbox filesystem
- `Shell()` — capability enabling shell command execution inside sandbox
- `Compaction()` — context window compaction for long-horizon tasks
- `UnixLocalSandboxClient` — local Unix sandbox (swappable for cloud sandboxes)
- `Runner.run()` — executes the agent loop
- `@function_tool` — decorator to register Python functions as agent tools
- `RunConfig` + `SandboxRunConfig` — runtime configuration for the runner
