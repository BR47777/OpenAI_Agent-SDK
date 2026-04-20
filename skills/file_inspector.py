"""
Skill: file_inspector
Gives the agent structured access to read and list files in the workspace.
Used during the initial triage phase of code review.
"""

from agents import function_tool


@function_tool
def list_python_files(directory: str) -> list[str]:
    """List all .py files recursively under a directory."""
    import os
    results = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                results.append(os.path.join(root, f))
    return results


@function_tool
def count_lines(filepath: str) -> dict:
    """Return line count and blank line count for a file."""
    with open(filepath) as f:
        lines = f.readlines()
    return {
        "total": len(lines),
        "blank": sum(1 for l in lines if l.strip() == ""),
        "code": sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
    }
