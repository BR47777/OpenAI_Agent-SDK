---
name: code_fixer
description: Apply fixes to Python files and verify them by executing the fixed code.
---

# Skill: Code Fixer

## Writing a Fixed File

Use `tee` to write the corrected file to `data/output/`:

```sh
tee data/output/<filename>.py << 'PYEOF'
# fixed code here
PYEOF
```

## Verifying the Fix

Always run the fixed file immediately after writing it:

```sh
python data/output/<filename>.py
```

A fix is only VERIFIED if the shell exits with code 0 and produces expected output.
If it fails, revise and re-run until it passes.

## Fix Checklist

| Bug Pattern | Correct Fix |
|---|---|
| `open(path)` without `with` | `with open(path) as f:` |
| `sum(x) / len(x)` on empty list | Guard: `if not x: return 0.0` |
| `"SELECT ... %s" % val` | Use parameterized: `("SELECT ... ?", (val,))` |
| `api_key = "sk-..."` hardcoded | `os.environ.get("OPENAI_API_KEY")` |
| `for i in range(len(items))` | `for i, item in enumerate(items)` |
