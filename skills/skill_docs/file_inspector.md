---
name: file_inspector
description: Discover and measure Python source files in the workspace.
---

# Skill: File Inspector

Use this skill to triage the workspace before deep analysis.

## Steps

1. List all Python files:
   ```sh
   find data/src -name '*.py' | sort
   ```

2. Count lines per file:
   ```sh
   wc -l data/src/**/*.py
   ```

3. Read a file:
   ```sh
   cat data/src/<filename>.py
   ```

## Output
Report the file list and line counts before proceeding to analysis.
