"""tests/test_skill_file_inspector.py"""
import os
from pathlib import Path


def _list_python_files(directory):
    results = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                results.append(os.path.join(root, f))
    return results


def _count_lines(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    return {
        "total": len(lines),
        "blank": sum(1 for l in lines if l.strip() == ""),
        "code":  sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
    }


# ── list_python_files ─────────────────────────────────────────────────────────

def test_list_finds_py_files(tmp_path):
    (tmp_path / "a.py").write_text("x=1")
    (tmp_path / "b.py").write_text("y=2")
    result = _list_python_files(str(tmp_path))
    assert len(result) == 2
    assert all(f.endswith(".py") for f in result)


def test_list_ignores_non_py(tmp_path):
    (tmp_path / "a.py").write_text("x=1")
    (tmp_path / "b.txt").write_text("hello")
    (tmp_path / "c.md").write_text("# doc")
    result = _list_python_files(str(tmp_path))
    assert len(result) == 1


def test_list_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "a.py").write_text("x=1")
    (sub / "b.py").write_text("y=2")
    result = _list_python_files(str(tmp_path))
    assert len(result) == 2


def test_list_empty_directory(tmp_path):
    result = _list_python_files(str(tmp_path))
    assert result == []


def test_list_returns_full_paths(tmp_path):
    (tmp_path / "a.py").write_text("x=1")
    result = _list_python_files(str(tmp_path))
    assert os.path.isabs(result[0]) or result[0].startswith(str(tmp_path))


# ── count_lines ───────────────────────────────────────────────────────────────

def test_count_lines_basic(sample_py_file):
    stats = _count_lines(str(sample_py_file))
    assert stats["total"] > 0
    assert stats["code"] > 0
    assert stats["blank"] >= 0


def test_count_lines_empty(empty_py_file):
    stats = _count_lines(str(empty_py_file))
    assert stats["total"] == 0
    assert stats["code"] == 0
    assert stats["blank"] == 0


def test_count_lines_only_comments(tmp_path):
    f = tmp_path / "comments.py"
    f.write_text("# line 1\n# line 2\n")
    stats = _count_lines(str(f))
    assert stats["total"] == 2
    assert stats["code"] == 0


def test_count_lines_with_blanks(tmp_path):
    f = tmp_path / "blanks.py"
    f.write_text("x = 1\n\ny = 2\n\n")
    stats = _count_lines(str(f))
    assert stats["total"] == 4
    assert stats["blank"] == 2
    assert stats["code"] == 2


def test_count_lines_total_equals_code_plus_blank_plus_comments(tmp_path):
    f = tmp_path / "mixed.py"
    f.write_text("# comment\nx = 1\n\ny = 2\n")
    stats = _count_lines(str(f))
    comment_lines = 1
    assert stats["total"] == stats["code"] + stats["blank"] + comment_lines
