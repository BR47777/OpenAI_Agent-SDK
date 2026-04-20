"""
Skill: report_writer
Lets the agent persist structured findings to the output directory.
"""

import os
from agents import function_tool


@function_tool
def write_report(output_path: str, content: str) -> str:
    """Write the review report markdown to output_path. Returns confirmation."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
    return f"Report written to {output_path} ({len(content)} chars)"
