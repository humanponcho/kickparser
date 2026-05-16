# Fix 4 — Add a Test Suite

## Problem

There was zero test coverage. The two most critical pieces of logic — `clean_column_name()` and the column classification — were completely untested and impossible to import (both were defined inside the `if uploaded_file` block).

---

## Changes Applied

### 1 — Added `pytest` to `requirements.txt`

```
pytest>=8.0.0
```

### 2 — Created `parser_logic.py`

Extracted `clean_column_name`, `classify_columns`, `CORE_KEYWORDS`, and `SHIPPING_KEYWORDS` into a standalone importable module. `classify_columns` returns `(core, shipping, addons)` as a tuple.

### 3 — Updated `app.py`

- Removed `import re` (now only needed inside `parser_logic.py`).
- Added `from parser_logic import clean_column_name, classify_columns`.
- Replaced the inline `def clean_column_name`, keyword lists, and three list comprehensions with a single call:

```python
core_cols, shipping_cols, addon_cols = classify_columns(df.columns.tolist())
```

### 4 — Created `tests/__init__.py` and `tests/test_parser_logic.py`

16 unit tests across two classes:

- `TestCleanColumnName` (9 tests) — addon prefix stripping, space collapsing, special-char removal, apostrophe normalisation, etc.
- `TestClassifyColumns` (7 tests) — core/shipping detection, residual addon logic, no-duplicates invariant, full coverage of columns, empty-input edge case.

### 5 — Created `.github/workflows/test.yml`

Runs `pytest tests/ -v` on every push and pull request via GitHub Actions (Python 3.11, ubuntu-latest).

---

## Verification

```bash
python3 -m venv .venv && .venv/bin/pip install pytest pandas
.venv/bin/python -m pytest tests/ -v
```

Result: **16 passed in 0.02s**
