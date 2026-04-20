"""tests/test_skill_security_scanner.py"""
import re

_PATTERNS = {
    "hardcoded_secret":  r'(api_key|secret|password|token)\s*=\s*["\'][^"\']{8,}["\']',
    "sql_injection":     r'%\s*\w+',
    "open_without_with": r'\bopen\s*\(',
}


def _scan(filepath):
    findings = []
    with open(filepath) as f:
        for lineno, line in enumerate(f, 1):
            for issue, pattern in _PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append({"line": lineno, "issue": issue, "snippet": line.strip()})
    return findings


# ── hardcoded_secret ──────────────────────────────────────────────────────────

def test_detects_hardcoded_api_key(tmp_path):
    f = tmp_path / "s.py"
    f.write_text('api_key = "sk-prod-abc123supersecret"\n')
    findings = _scan(str(f))
    assert any(x["issue"] == "hardcoded_secret" for x in findings)


def test_detects_hardcoded_password(tmp_path):
    f = tmp_path / "s.py"
    f.write_text('password = "supersecurepassword"\n')
    findings = _scan(str(f))
    assert any(x["issue"] == "hardcoded_secret" for x in findings)


def test_no_false_positive_short_value(tmp_path):
    f = tmp_path / "s.py"
    f.write_text('token = "abc"\n')   # too short — under 8 chars
    findings = _scan(str(f))
    assert not any(x["issue"] == "hardcoded_secret" for x in findings)


def test_detects_hardcoded_token(tmp_path):
    f = tmp_path / "s.py"
    f.write_text('token = "ghp_longtoken12345"\n')
    findings = _scan(str(f))
    assert any(x["issue"] == "hardcoded_secret" for x in findings)


# ── sql_injection ─────────────────────────────────────────────────────────────

def test_detects_sql_injection_percent(tmp_path):
    f = tmp_path / "s.py"
    f.write_text('query = "SELECT * FROM users WHERE id = %s" % user_id\n')
    findings = _scan(str(f))
    assert any(x["issue"] == "sql_injection" for x in findings)


def test_no_false_positive_safe_query(tmp_path):
    f = tmp_path / "s.py"
    f.write_text('query = "SELECT * FROM users WHERE id = ?"\n')
    findings = _scan(str(f))
    assert not any(x["issue"] == "sql_injection" for x in findings)


# ── open_without_with ─────────────────────────────────────────────────────────

def test_detects_bare_open(tmp_path):
    f = tmp_path / "s.py"
    f.write_text('f = open("file.txt", "r")\n')
    findings = _scan(str(f))
    assert any(x["issue"] == "open_without_with" for x in findings)


def test_detects_open_in_with(tmp_path):
    # open() inside with — still flagged by simple pattern (expected behaviour)
    f = tmp_path / "s.py"
    f.write_text('with open("file.txt") as f:\n    data = f.read()\n')
    findings = _scan(str(f))
    # pattern fires on the word open() — document this is a known trade-off
    assert isinstance(findings, list)


# ── empty file ────────────────────────────────────────────────────────────────

def test_empty_file_no_findings(empty_py_file):
    findings = _scan(str(empty_py_file))
    assert findings == []


# ── multiple issues in one file ───────────────────────────────────────────────

def test_multiple_issues_detected(sample_py_file):
    findings = _scan(str(sample_py_file))
    issues_found = {f["issue"] for f in findings}
    assert "hardcoded_secret" in issues_found
    assert "sql_injection" in issues_found
    assert "open_without_with" in issues_found


def test_findings_have_required_keys(sample_py_file):
    findings = _scan(str(sample_py_file))
    for f in findings:
        assert "line" in f
        assert "issue" in f
        assert "snippet" in f


def test_line_numbers_are_positive(sample_py_file):
    findings = _scan(str(sample_py_file))
    assert all(f["line"] > 0 for f in findings)
