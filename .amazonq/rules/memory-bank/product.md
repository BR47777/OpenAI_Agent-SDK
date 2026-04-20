# Product Overview

## Purpose
A sandboxed AI agent that performs automated Python code review and auto-fixing. It inspects source files, identifies bugs and security issues, applies patches, verifies fixes by executing the code, and produces a structured markdown report.

## Value Proposition
- Automates the full code review lifecycle: triage → scan → fix → verify → report
- Runs in an isolated sandbox so model-generated code never touches host credentials
- Exposes the agent as an A2A-compliant (Google Agent-to-Agent protocol) HTTP service for interoperability with other agents

## Key Features
- **Automated bug detection**: logic bugs, ZeroDivisionError, off-by-one, non-idiomatic patterns
- **Security scanning**: hardcoded secrets, SQL injection, resource leaks (regex pre-scan + LLM deep read)
- **Auto-fix + verification**: applies patches and runs fixed code via shell to confirm correctness
- **Structured reporting**: writes `review_report.md` with severity, line numbers, fix description, and shell verification output
- **Sandboxed execution**: uses `UnixLocalSandboxClient` (swappable for E2B/Modal/Daytona)
- **A2A server**: FastAPI JSON-RPC 2.0 endpoint exposing the agent as a discoverable service

## Target Users
- Developers wanting automated pre-commit or CI code review
- Teams integrating AI agents into multi-agent pipelines via the A2A protocol
- Engineers exploring the OpenAI Agents SDK sandbox capabilities

## Use Cases
1. Run `python agent.py` for a one-shot local code review of `sample_project/src/`
2. Run `uvicorn a2a.server:app` to expose the agent as an A2A HTTP service
3. Use `a2a/client.py` to send tasks to the A2A server and poll for results
4. Extend with new skills by adding `@function_tool` functions in `skills/`
