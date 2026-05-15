# Fix 4 — Add a Test Suite

## Problem

There is zero test coverage. The two most critical pieces of logic — `clean_column_name()` and the column classification — are completely untested. A one-line change could silently break the CSV splits for all users.

---

## Step-by-Step Fix

### Step 1 — Install pytest

```bash
pip install pytest
```

Add it to `requirements.txt`:

```
streamlit>=1.38.0
pandas>=2.2.0
pytest>=8.0.0
```

### Step 2 — Extract testable logic from `app.py`

`clean_column_name()` and the column classification lists are currently defined inside the `if uploaded_file` block, which makes them impossible to import. Move them to a separate module.

Create a new file `parser_logic.py` in the project root:

```python
import re

CORE_KEYWORDS = [
    'Backer Number', 'Backer UID', 'Backer Name', 'Email', 'Reward Title',
    'Pledge Amount', 'Pledged At', 'Late Pledge', 'Fulfillment Status',
    'Pledged Status', 'Notes', 'Billing',
]
SHIPPING_KEYWORDS = ['Shipping']


def clean_column_name(col: str) -> str:
    col = re.sub(r'\[Addon: \d+\]\s*', '', col)
    col = col.replace(" by ", " - ").replace("’", "'").replace(" of of ", " of ")
    col = re.sub(r'[^a-zA-Z0-9\s\-]', '', col)
    return re.sub(r'\s+', '_', col.strip())


def classify_columns(columns: list[str]) -> tuple[list[str], list[str], list[str]]:
    core = [c for c in columns if any(k in c for k in CORE_KEYWORDS)]
    shipping = [c for c in columns if any(k in c for k in SHIPPING_KEYWORDS)]
    addons = [c for c in columns if c not in core and c not in shipping]
    return core, shipping, addons
```

### Step 3 — Update `app.py` to import from the new module

At the top of `app.py`, replace the inline definitions with an import:

```python
# Add this import
from parser_logic import clean_column_name, classify_columns, CORE_KEYWORDS, SHIPPING_KEYWORDS
```

Remove the `def clean_column_name(...)` function and the three keyword lists from inside the `if uploaded_file` block, and replace the classification lines with:

```python
core_cols, shipping_cols, addon_cols = classify_columns(df.columns.tolist())
```

### Step 4 — Create the test file

Create `tests/test_parser_logic.py`:

```python
import pandas as pd
import pytest
from parser_logic import clean_column_name, classify_columns


# --- clean_column_name ---

class TestCleanColumnName:
    def test_strips_addon_prefix(self):
        assert clean_column_name("[Addon: 3] T-Shirt") == "T-Shirt"

    def test_strips_addon_prefix_with_space(self):
        assert clean_column_name("[Addon: 12]  Extra Copy") == "Extra_Copy"

    def test_replaces_spaces_with_underscores(self):
        assert clean_column_name("Backer Name") == "Backer_Name"

    def test_removes_special_characters(self):
        assert clean_column_name("Col!@#Name") == "ColName"

    def test_replaces_by_with_dash(self):
        assert clean_column_name("Art by Artist") == "Art_-_Artist"

    def test_normalises_curly_apostrophe(self):
        result = clean_column_name("Don’t Miss It")
        assert "'" in result or "Dont" in result  # apostrophe normalised or removed

    def test_collapses_multiple_spaces(self):
        assert clean_column_name("Too  Many   Spaces") == "Too_Many_Spaces"

    def test_strips_leading_trailing_whitespace(self):
        assert clean_column_name("  padded  ") == "padded"

    def test_plain_column_unchanged_structure(self):
        result = clean_column_name("Email")
        assert result == "Email"


# --- classify_columns ---

class TestClassifyColumns:
    def _make_columns(self):
        return [
            'Backer Number', 'Backer UID', 'Backer Name', 'Email',
            'Reward Title', 'Pledge Amount', 'Pledged At', 'Fulfillment Status',
            'Shipping Country', 'Shipping Address 1', 'Shipping City',
            '[Addon: 1] T-Shirt', '[Addon: 2] Poster',
        ]

    def test_core_columns_detected(self):
        core, _, _ = classify_columns(self._make_columns())
        assert 'Backer Number' in core
        assert 'Email' in core
        assert 'Reward Title' in core

    def test_shipping_columns_detected(self):
        _, shipping, _ = classify_columns(self._make_columns())
        assert 'Shipping Country' in shipping
        assert 'Shipping Address 1' in shipping

    def test_addon_columns_are_residual(self):
        _, _, addons = classify_columns(self._make_columns())
        assert '[Addon: 1] T-Shirt' in addons
        assert '[Addon: 2] Poster' in addons

    def test_no_column_appears_in_two_groups(self):
        cols = self._make_columns()
        core, shipping, addons = classify_columns(cols)
        all_classified = core + shipping + addons
        assert len(all_classified) == len(set(all_classified)), "Duplicate column in classification"

    def test_all_columns_classified(self):
        cols = self._make_columns()
        core, shipping, addons = classify_columns(cols)
        assert sorted(core + shipping + addons) == sorted(cols)

    def test_empty_columns_returns_empty_lists(self):
        core, shipping, addons = classify_columns([])
        assert core == shipping == addons == []

    def test_all_shipping_columns(self):
        cols = ['Shipping Name', 'Shipping Country', 'Shipping City']
        core, shipping, addons = classify_columns(cols)
        assert len(shipping) == 3
        assert core == []
        assert addons == []
```

### Step 5 — Create a `tests/__init__.py` (empty)

```bash
mkdir -p tests && touch tests/__init__.py
```

### Step 6 — Run the tests

```bash
pytest tests/ -v
```

Expected output:

```
tests/test_parser_logic.py::TestCleanColumnName::test_strips_addon_prefix PASSED
tests/test_parser_logic.py::TestCleanColumnName::test_replaces_spaces_with_underscores PASSED
...
16 passed in 0.12s
```

### Step 7 — Add a CI check (optional)

Create `.github/workflows/test.yml` to run tests automatically on every push:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

---

## File Summary

| New file | Purpose |
|---|---|
| `parser_logic.py` | Extracted, importable business logic |
| `tests/__init__.py` | Makes `tests/` a Python package |
| `tests/test_parser_logic.py` | 16 unit tests covering clean/classify |
| `.github/workflows/test.yml` | (optional) CI on push |
