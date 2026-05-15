# Fix 1 — Guard Against Missing Column Crashes

## Problem

`app.py` assumes several columns always exist in the uploaded CSV. If they are absent the app raises an unhandled `KeyError` and shows a red traceback to the user instead of a helpful message.

Affected lines and their assumptions:

| Line | Assumed column |
|---|---|
| 60–61 | `Backer Number` |
| 75–76 | `Reward Title` |
| 81–84 | A column whose name contains `"Address"` (soft, but silent `None`) |
| 45, 54, 88–89, 93–95 | `Shipping Country` |

---

## Step-by-Step Fix

### Step 1 — Define the columns you require

At the top of the `if uploaded_file is not None:` block (after line 16), add a list of the columns that must exist for the app to work correctly.

```python
REQUIRED_COLUMNS = ['Backer Number', 'Reward Title', 'Shipping Country']
```

### Step 2 — Check for missing columns immediately after loading

Right after the `st.success(...)` line (line 17), add a validation block that stops processing if any required column is absent.

```python
missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing:
    st.error(
        f"The uploaded CSV is missing expected columns: **{', '.join(missing)}**\n\n"
        "Please export from Kickstarter using **Reports → All Rewards** "
        "and upload that file."
    )
    st.stop()
```

`st.stop()` halts execution for the current run so no further code runs — no `KeyError`, no traceback.

### Step 3 — Guard the addons/shipping split (lines 60–61)

The current code has an inline `if 'Backer Number' in filtered_df.columns` guard, but after Step 2 that column is guaranteed to exist. Remove the conditional and simplify:

```python
# Before (lines 60–61)
addons_df = filtered_df[['Backer Number'] + addon_cols].copy() if 'Backer Number' in filtered_df.columns else filtered_df[addon_cols].copy()
shipping_df = filtered_df[['Backer Number'] + shipping_cols].copy() if 'Backer Number' in filtered_df.columns else filtered_df[shipping_cols].copy()
```

```python
# After
addons_df = filtered_df[['Backer Number'] + addon_cols].copy()
shipping_df = filtered_df[['Backer Number'] + shipping_cols].copy()
```

Similarly simplify lines 63–66:

```python
# Before (lines 63–66)
if 'Backer Number' in filtered_df.columns:
    addons_df.columns = ['Backer Number'] + [clean_column_name(col) for col in addon_cols]
else:
    addons_df.columns = [clean_column_name(col) for col in addon_cols]
```

```python
# After
addons_df.columns = ['Backer Number'] + [clean_column_name(col) for col in addon_cols]
```

### Step 4 — Guard the country filter (lines 44–54)

The `Shipping Country` check is already wrapped in `if 'Shipping Country' in df.columns`, but after Step 2 it is guaranteed. Simplify the sidebar block:

```python
# Before (lines 44–54)
selected_countries = None
if 'Shipping Country' in df.columns:
    countries = sorted(df['Shipping Country'].dropna().unique())
    selected_countries = st.sidebar.multiselect(...)

filtered_df = df.copy()
if selected_countries:
    filtered_df = filtered_df[filtered_df['Shipping Country'].isin(selected_countries)]
```

```python
# After
countries = sorted(df['Shipping Country'].dropna().unique())
selected_countries = st.sidebar.multiselect(
    "Filter by Country", options=countries,
    default=countries[:5] if len(countries) > 5 else countries
)

filtered_df = df[df['Shipping Country'].isin(selected_countries)].copy() if selected_countries else df.copy()
```

### Step 5 — Verify

1. Run the app: `streamlit run app.py`
2. Upload a CSV that is missing one of the required columns (e.g. delete the `Backer Number` header in a test file).
3. You should see a red `st.error` banner with the missing column name — no traceback.
4. Upload a valid CSV. Everything should work as before.

---

## Final State of Changed Section (top of `if uploaded_file` block)

```python
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success(f"✅ Loaded **{len(df):,} backers** × **{len(df.columns)} columns**")

    REQUIRED_COLUMNS = ['Backer Number', 'Reward Title', 'Shipping Country']
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(
            f"The uploaded CSV is missing expected columns: **{', '.join(missing)}**\n\n"
            "Please export from Kickstarter using **Reports → All Rewards** "
            "and upload that file."
        )
        st.stop()
```
