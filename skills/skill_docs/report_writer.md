---
name: report_writer
description: Write a structured markdown code review report to data/output/review_report.md.
---

# Skill: Report Writer

## Report Structure

Write the report using `tee`:

```sh
tee data/output/review_report.md << 'MDEOF'
# Code Review Report

## File: <filename>

### Issues Found
| # | Severity | Line | Issue | Description |
|---|---|---|---|---|
| 1 | CRITICAL | 22 | Hardcoded secret | api_key assigned literal string |
| 2 | HIGH | 17 | SQL injection | Query built with % formatting |
| 3 | MEDIUM | 9 | Resource leak | open() without context manager |
| 4 | MEDIUM | 13 | ZeroDivisionError | No guard for empty list |
| 5 | LOW | 27 | Non-idiomatic | range(len(x)) instead of enumerate |

### Fixes Applied
- **Line 9**: Wrapped `open()` in `with` statement
- **Line 13**: Added `if not numbers: return 0.0` guard
- **Line 17**: Replaced `%` formatting with parameterized tuple
- **Line 22**: Replaced literal with `os.environ.get("OPENAI_API_KEY")`
- **Line 27**: Replaced `range(len(items))` with `enumerate(items)`

### Verification
```
$ python data/output/data_processor.py
20.0
[2, 4, 6]
```
Exit code: 0 ✅
MDEOF
```

## Rules
- Every issue must have a line number
- Every fix must have a verification result (exit code + output)
- Mark unverifiable fixes as ⚠️ UNVERIFIED
