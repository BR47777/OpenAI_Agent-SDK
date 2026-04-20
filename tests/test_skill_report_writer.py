"""tests/test_skill_report_writer.py"""
import os
from pathlib import Path


def _write_report(output_path, content):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
    return f"Report written to {output_path} ({len(content)} chars)"


def test_creates_file(output_dir):
    path = str(output_dir / "report.md")
    _write_report(path, "# Report\nAll good.")
    assert os.path.exists(path)


def test_content_is_correct(output_dir):
    path = str(output_dir / "report.md")
    content = "# Report\n## Issues\n- Bug on line 5"
    _write_report(path, content)
    assert Path(path).read_text() == content


def test_return_message_contains_path(output_dir):
    path = str(output_dir / "report.md")
    msg = _write_report(path, "hello")
    assert str(path) in msg


def test_return_message_contains_char_count(output_dir):
    path = str(output_dir / "report.md")
    content = "hello world"
    msg = _write_report(path, content)
    assert str(len(content)) in msg


def test_overwrites_existing_file(output_dir):
    path = str(output_dir / "report.md")
    _write_report(path, "first")
    _write_report(path, "second")
    assert Path(path).read_text() == "second"


def test_creates_nested_directories(tmp_path):
    path = str(tmp_path / "deep" / "nested" / "report.md")
    _write_report(path, "content")
    assert os.path.exists(path)


def test_empty_content(output_dir):
    path = str(output_dir / "empty.md")
    _write_report(path, "")
    assert Path(path).read_text() == ""
