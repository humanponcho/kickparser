# Fix 2 — Generalise the Addon Keyword List

## Problem

`app.py` contained a hardcoded `addon_keywords` list with campaign-specific titles:

```python
addon_keywords = ['Addon', 'Terrible Means', 'Days by', 'Victory Point', 'Sleeping While',
                  'Acid Box', 'Scrapbook', 'Barking', 'Macbeth', 'Orlando', 'Postcard',
                  'Zine', 'Sketch', 'Digital Bundle', 'Physical bundle', 'print copy']
```

These titles belonged to one specific campaign. Addon columns were already captured as the residual — any column that isn't core or shipping ends up in addons regardless. The variable was both misleading and inert.

---

## Changes Applied

### 1 — Removed the unused `addon_keywords` variable

Deleted the three-line `addon_keywords` definition entirely.

### 2 — Added clarifying comment to the residual logic

```python
# Addons are everything not matched by core or shipping keywords
addon_cols = [col for col in df.columns
              if col not in core_cols and col not in shipping_cols]
```

### 3 — Added column classification expander

Placed immediately after the three `*_cols` lists are built, so users can verify classification for any CSV without touching code:

```python
with st.expander("Column classification (click to inspect)"):
    st.write(f"**Core ({len(core_cols)}):** {', '.join(core_cols) or 'none'}")
    st.write(f"**Shipping ({len(shipping_cols)}):** {', '.join(shipping_cols) or 'none'}")
    st.write(f"**Addons ({len(addon_cols)}):** {', '.join(addon_cols) or 'none'}")
```

Step 4 (sidebar keyword overrides) was skipped — not needed for the current use case.

---

## Verification

1. Run: `streamlit run app.py`
2. Upload any Kickstarter CSV.
3. Open the "Column classification" expander and confirm all columns are classified sensibly.
4. Download the addons CSV and confirm it contains the right columns with clean names.
