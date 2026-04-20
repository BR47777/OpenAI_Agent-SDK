"""
Skill: security_scanner
Lightweight static patterns the agent can invoke to pre-flag security issues
before doing deep LLM analysis. Reduces token usage on obvious findings.
"""

import re
from agents import function_tool

_PATTERNS = {
    "hardcoded_secret": r'(api_key|secret|password|token)\s*=\s*["\'][^"\']{8,}["\']',
    "sql_injection":    r'%\s*\w+|f["\'].*SELECT.*\{',
    "open_without_with": r'(?<!\bwith\b.{0,40})\bopen\s*\(',
}


@function_tool
def scan_for_security_issues(filepath: str) -> list[dict]:
    """Scan a Python file for common security anti-patterns. Returns list of findings."""
    findings = []
    with open(filepath) as f:
        for lineno, line in enumerate(f, 1):
            for issue, pattern in _PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({"line": lineno, "issue": issue, "snippet": line.strip()})
    return findings
