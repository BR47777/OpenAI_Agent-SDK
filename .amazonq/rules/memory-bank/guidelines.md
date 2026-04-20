# Development Guidelines

## Code Quality Standards

### Module Docstrings
Every module starts with a triple-quoted docstring describing its purpose, key exports, and usage:
```python
"""
a2a/server.py
A2A-compliant FastAPI server exposing the CodeReviewAgent.

Endpoints:
  GET  /.well-known/agent.json   → AgentCard
  POST /                         → JSON-RPC 2.0 (tasks/send, tasks/get)

Run:
  uvicorn a2a.server:app --port 8000
"""
```

### Future Annotations
All modules use `from __future__ import annotations` for forward-reference support in type hints.

### Import Order
1. `from __future__ import annotations`
2. Standard library
3. Third-party (pydantic, fastapi, httpx, agents)
4. Local (`a2a.*`)

### Type Hints
Full type annotations on all function signatures and class attributes:
```python
def get(self, task_id: str) -> Task | None:
def update_state(self, task_id: str, state: TaskState, error: str | None = None) -> Task:
```
Use `X | None` union syntax (not `Optional[X]`).

### Naming Conventions
- Classes: `PascalCase` (TaskStore, AgentCard, JsonRpcRequest)
- Functions/methods: `snake_case`
- Private methods/attributes: `_leading_underscore` (_tasks, _build_agent, _tasks_send)
- Constants: `UPPER_SNAKE_CASE` (BASE_URL, POLL_INTERVAL, AGENT_CARD, TASK)
- Enum values: `UPPER_CASE` (TaskState.SUBMITTED, TaskState.WORKING)

### Inline Comments
Used sparingly to annotate intent, not mechanics:
```python
role: str   # "user" | "agent"
# module-level singleton
store = TaskStore()
# Fire-and-forget — client polls tasks/get for status
asyncio.create_task(execute_task(task, output_dir))
```

---

## Structural Conventions

### Pydantic Models (a2a/types.py)
All data models extend `BaseModel`. Use `Field(default_factory=...)` for dynamic defaults:
```python
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = Field(default_factory=time.time)
    error: str | None = None
```
Serialize with `.model_dump()` — never manual dict construction.

### Enums
State enums inherit from both `str` and `Enum` for JSON serialization compatibility:
```python
class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING   = "working"
```

### Skills — @function_tool Pattern
All agent tools are decorated with `@function_tool` from the `agents` package. Each skill lives in its own file under `skills/`:
```python
from agents import function_tool

@function_tool
def scan_for_security_issues(filepath: str) -> list[dict]:
    """Scan a Python file for common security anti-patterns. Returns list of findings."""
    ...
```
- One docstring per tool — this becomes the tool description the LLM sees
- Return plain Python types (list, dict, str) — not Pydantic models

### Deferred Imports for Testability
SDK imports that require environment variables (e.g. `OPENAI_API_KEY`) are deferred inside functions so tests can patch before import:
```python
def _build_agent(output_dir: Path):
    """Build SandboxAgent — import deferred so tests can mock OPENAI_API_KEY."""
    from agents.sandbox import Manifest, SandboxAgent
    from agents.sandbox.entries import LocalDir
    ...
```

### Module-Level Singleton
Shared state is exposed as a module-level singleton, not passed as a parameter:
```python
# task_store.py
store = TaskStore()

# server.py / executor.py
from a2a.task_store import store
```

### Section Separators
Use `# ── Section Name ──────...` comment banners to visually separate logical sections within a file:
```python
# ── Agent Card ────────────────────────────────────────────────────────────────
# ── JSON-RPC dispatcher ───────────────────────────────────────────────────────
# ── Method handlers ───────────────────────────────────────────────────────────
```

---

## Testing Patterns

### Test File Structure
- One test file per module: `test_a2a_client.py`, `test_a2a_server.py`, etc.
- Tests grouped by function under `# ── function_name ──` section banners
- All async tests use `@pytest.mark.asyncio` (redundant with `asyncio_mode = auto` but kept for clarity)

### Mocking HTTP Clients
Use `AsyncMock` for async HTTP clients; always mock `raise_for_status` separately:
```python
mock_response = MagicMock()
mock_response.raise_for_status = MagicMock()
mock_response.json.return_value = {"name": "CodeReviewAgent"}

mock_client = AsyncMock()
mock_client.get = AsyncMock(return_value=mock_response)
```

### Patching the Store in Executor Tests
Create a local `TaskStore()` instance and patch both `a2a.task_store.store` and `a2a.executor.store`:
```python
local_store = TaskStore()
with patch("a2a.task_store.store", local_store), \
     patch("a2a.executor.store", local_store), \
     patch("a2a.executor._build_agent", return_value=MagicMock()), \
     patch("agents.Runner.run", new=AsyncMock(return_value=mock_result)):
    await execute_task(task, tmp_path)
```

### FastAPI Testing
Use `fastapi.testclient.TestClient` (synchronous) for server tests. Patch `asyncio.create_task` to prevent background tasks from running:
```python
client = TestClient(app)

def _noop_create_task(coro):
    coro.close()  # suppress unawaited coroutine warning

with patch("a2a.server.asyncio.create_task", side_effect=_noop_create_task):
    r = client.post("/", json=payload)
```

### Helper Factories in Tests
Use small factory functions instead of repeating setup:
```python
def make_task(content="Review my code"):
    return Task(messages=[Message(role="user", content=content)])

def _send_payload(message="Review my code", task_id=None):
    ...
```

### conftest.py Fixtures
Shared fixtures use `tmp_path` (pytest built-in) for isolation:
```python
@pytest.fixture
def sample_py_file(tmp_path):
    f = tmp_path / "buggy.py"
    f.write_text(...)
    return f
```

---

## Async Patterns

- Entry points use `asyncio.run(main())` pattern
- `async def main()` wraps all top-level async logic
- Background tasks use `asyncio.create_task()` for fire-and-forget (server returns immediately, client polls)
- `async with httpx.AsyncClient(timeout=30) as client:` for HTTP client lifecycle

---

## A2A Protocol Conventions

### JSON-RPC 2.0 Envelope
Always include `jsonrpc`, `id`, `method`, `params` in requests; `jsonrpc`, `id`, `result`/`error` in responses:
```python
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tasks/send",
    "params": {"message": {"role": "user", "content": message}},
}
```

### Agent Discovery
Expose `GET /.well-known/agent.json` returning a serialized `AgentCard` via `.model_dump()`.

### Task Lifecycle
`SUBMITTED → WORKING → COMPLETED | FAILED | CANCELLED`
Always call `store.update_state(task.id, TaskState.WORKING)` at the start of execution and update to terminal state in both success and exception paths.

---

## Security Practices

- Never hardcode API keys — load via `load_dotenv()` + environment variables
- Credentials stay in the harness process; never passed into the sandbox
- `sample_project/src/data_processor.py` intentionally contains bad patterns (resource leak, SQL injection, hardcoded secret) — these are review targets, not patterns to follow
