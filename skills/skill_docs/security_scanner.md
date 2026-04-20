---
name: security_scanner
description: Detect hardcoded secrets, SQL injection, and resource leaks using grep patterns.
---

# Skill: Security Scanner

Run these shell commands to pre-flag security issues before deep LLM analysis.

## Hardcoded Secrets
```sh
grep -n -E "(api_key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]" data/src/*.py
```

## SQL Injection (string formatting in queries)
```sh
grep -n -E '(%\s*\w+|f".*SELECT)' data/src/*.py
```

## Resource Leaks (open() without context manager)
```sh
grep -n -E '\bopen\s*\(' data/src/*.py
```

## Output
For each match: report the filename, line number, issue type, and the offending line.
Classify severity: hardcoded secrets = CRITICAL, SQL injection = HIGH, resource leak = MEDIUM.
