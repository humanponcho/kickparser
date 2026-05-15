# Fix 3 — Add Input Validation

## Problem

`app.py` calls `pd.read_csv(uploaded_file)` on line 16 with no guards. Three failure modes exist:

1. **Empty file** — `pd.read_csv` returns an empty DataFrame; subsequent code silently produces empty output files with no warning.
2. **Corrupt / non-CSV file** — `pd.read_csv` raises a `pandas.errors.ParserError` shown as a red traceback.
3. **Wrong format** (e.g. a BackerKit export) — parsing succeeds but the content is wrong; the user gets confusing empty splits.

---

## Step-by-Step Fix

### Step 1 — Wrap `pd.read_csv` in a try/except

Replace line 16:

```python
# Before
df = pd.read_csv(uploaded_file)
```

```python
# After
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read the file as a CSV: **{e}**\n\nPlease upload a valid `.csv` export.")
    st.stop()
```

### Step 2 — Check for an empty DataFrame

Add this block immediately after the try/except (before `st.success`):

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

The `< 5` threshold is a loose sanity check — a real Kickstarter export has 30–60 columns. Adjust if needed.

### Step 3 — Check for required columns (coordinates with Fix 1)

If you have also applied Fix 1, this step is already covered. If not, add it here:

```python
REQUIRED_COLUMNS = ['Backer Number', 'Reward Title', 'Shipping Country']
missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing:
    st.error(
        f"Missing expected columns: **{', '.join(missing)}**\n\n"
        "Please use the Kickstarter **Reports → All Rewards** export."
    )
    st.stop()
```

### Step 4 — Show a friendly success message with column count

Now that you know the file is valid, make the success message more informative:

```python
# Replace line 17
st.success(
    f"✅ Loaded **{len(df):,} backers** × **{len(df.columns)} columns** "
    f"from `{uploaded_file.name}`"
)
```

### Step 5 — Guard against an all-filtered-out result

After the country filter is applied (around line 54), add a check so the app doesn't silently produce empty downloads:

```python
if filtered_df.empty:
    st.warning("No backers match the current country filter. Adjust the filter in the sidebar.")
    st.stop()
```

### Step 6 — Verify

Test each failure mode:

| Test | Expected result |
|---|---|
| Upload a `.txt` or `.xlsx` file | Friendly error, no traceback |
| Upload an empty `.csv` (just a header row) | Warning about no rows |
| Upload a CSV with only 2 columns | Warning about wrong format |
| Deselect all countries in the sidebar | Warning about empty filter |
| Upload a valid Kickstarter CSV | Normal flow, success message |

---

## Final Validated Load Block

```python
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read the file as a CSV: **{e}**")
        st.stop()

    if df.empty:
        st.warning("The uploaded file contains no rows.")
        st.stop()

    if len(df.columns) < 5:
        st.warning(f"Only {len(df.columns)} column(s) found — this doesn't look like a Kickstarter export.")
        st.stop()

    REQUIRED_COLUMNS = ['Backer Number', 'Reward Title', 'Shipping Country']
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Missing expected columns: **{', '.join(missing)}**")
        st.stop()

    st.success(f"✅ Loaded **{len(df):,} backers** × **{len(df.columns)} columns** from `{uploaded_file.name}`")
```
