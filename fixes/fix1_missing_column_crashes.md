# Fix 1 — Guard Against Missing Column Crashes

## Problem

`app.py` assumed several columns always exist in the uploaded CSV. If absent, the app raised an unhandled `KeyError` and showed a red traceback instead of a helpful message.

Affected columns: `Backer Number`, `Reward Title`, `Shipping Country`

---

## Changes Applied

### 1 — Upfront column validation (after line 17)

Added immediately after `st.success(...)`:

```python
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

`st.stop()` halts execution — no `KeyError`, no traceback.

### 2 — Simplified country filter (sidebar)

Removed the `if 'Shipping Country' in df.columns` guard; now unconditional:

```python
countries = sorted(df['Shipping Country'].dropna().unique())
selected_countries = st.sidebar.multiselect(
    "Filter by Country", options=countries,
    default=countries[:5] if len(countries) > 5 else countries
)

filtered_df = df[df['Shipping Country'].isin(selected_countries)].copy() if selected_countries else df.copy()
```

### 3 — Simplified addons/shipping splits

Removed `if 'Backer Number' in filtered_df.columns` ternary branches; now unconditional:

```python
addons_df = filtered_df[['Backer Number'] + addon_cols].copy()
shipping_df = filtered_df[['Backer Number'] + shipping_cols].copy()

addons_df.columns = ['Backer Number'] + [clean_column_name(col) for col in addon_cols]
```

### 4 — Simplified fulfillment dashboard metrics

Removed redundant `if 'Reward Title'` and `if 'Shipping Country'` guards in the dashboard; now unconditional:

```python
physical = len(filtered_df[~filtered_df['Reward Title'].str.contains("Digital", na=False)])
st.metric("Physical Orders", physical)

st.metric("Countries", filtered_df['Shipping Country'].nunique())

st.subheader("Top Shipping Countries")
st.bar_chart(filtered_df['Shipping Country'].value_counts().head(10))
```

---

## Verification

1. Run the app: `streamlit run app.py`
2. Upload a CSV missing one of the required columns — expect a red `st.error` banner with the column name, no traceback.
3. Upload a valid CSV — everything should work as before.
