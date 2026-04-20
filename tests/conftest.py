import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def sample_py_file(tmp_path):
    """A temp .py file with known bugs for skill testing."""
    f = tmp_path / "buggy.py"
    f.write_text(
        'import json\n'
        'def load(path):\n'
        '    f = open(path, "r")\n'
        '    return json.load(f)\n'
        'def avg(nums):\n'
        '    return sum(nums) / len(nums)\n'
        'def query(uid):\n'
        '    return "SELECT * FROM users WHERE id = %s" % uid\n'
        'def secret():\n'
        '    api_key = "sk-prod-abc123supersecret"\n'
        '    return api_key\n'
    )
    return f


@pytest.fixture
def empty_py_file(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    return f


@pytest.fixture
def output_dir(tmp_path):
    d = tmp_path / "output"
    d.mkdir()
    return d
