# Fix 3 — Add Input Validation

## Problem

`app.py` called `pd.read_csv(uploaded_file)` with no guards. Three failure modes existed:

1. **Empty file** — `pd.read_csv` returns an empty DataFrame; subsequent code silently produces empty output files with no warning.
2. **Corrupt / non-CSV file** — `pd.read_csv` raises a `pandas.errors.ParserError` shown as a red traceback.
3. **Wrong format** (e.g. a BackerKit export) — parsing succeeds but the content is wrong; the user gets confusing empty splits.

---

## Changes Applied

### 1 — Wrapped `pd.read_csv` in a try/except

```python
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read the file as a CSV: **{e}**\n\nPlease upload a valid `.csv` export.")
    st.stop()
```

### 2 — Added empty-file and wrong-format checks

```python
if df.empty:
    st.warning("The uploaded file contains no rows. Please check your export and try again.")
    st.stop()

if len(df.columns) < 5:
    st.warning(
        f"Only {len(df.columns)} column(s) found. "
        "This doesn't look like a Kickstarter 'All Rewards' export. "
        "Please re-export from **Reports → All Rewards**."
    )
    st.stop()
```

### 3 — Required-column check (already covered by Fix 1)

No change needed — `REQUIRED_COLUMNS` validation was applied in Fix 1 and remains in place after the new guards above.

### 4 — Updated success message to include filename

```python
st.success(
    f"✅ Loaded **{len(df):,} backers** × **{len(df.columns)} columns** "
    f"from `{uploaded_file.name}`"
)
```

### 5 — Added empty-filter guard after country filter

```python
if filtered_df.empty:
    st.warning("No backers match the current country filter. Adjust the filter in the sidebar.")
    st.stop()
```

---

## Verification

| Test | Expected result |
|---|---|
| Upload a `.txt` or `.xlsx` file | Friendly error, no traceback |
| Upload an empty `.csv` (just a header row) | Warning about no rows |
| Upload a CSV with only 2 columns | Warning about wrong format |
| Deselect all countries in the sidebar | Warning about empty filter |
| Upload a valid Kickstarter CSV | Normal flow, success message with filename |
