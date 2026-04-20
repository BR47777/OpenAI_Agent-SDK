import os
import re

# --- file_inspector logic ---
def list_python_files(directory):
    results = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                results.append(os.path.join(root, f))
    return results

def count_lines(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    return {
        "total": len(lines),
        "blank": sum(1 for l in lines if l.strip() == ""),
        "code":  sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
    }

# --- security_scanner logic ---
PATTERNS = {
    "hardcoded_secret":  r"(api_key|secret|password|token)\s*=\s*[\"'][^\"']{8,}[\"']",
    "sql_injection":     r"%\s*\w+",
    "open_without_with": r"\bopen\s*\(",
}

def scan_for_security_issues(filepath):
    findings = []
    with open(filepath) as f:
        for lineno, line in enumerate(f, 1):
            for issue, pattern in PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({"line": lineno, "issue": issue, "snippet": line.strip()})
    return findings

# --- run tests ---
files = list_python_files("sample_project/src")
print("Files found:", files)

for path in files:
    stats = count_lines(path)
    print(f"\nLine stats for {path}:", stats)

    issues = scan_for_security_issues(path)
    print(f"Security issues in {path}:")
    for i in issues:
        print(f"  Line {i['line']} [{i['issue']}]: {i['snippet']}")
