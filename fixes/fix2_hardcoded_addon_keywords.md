# Fix 2 — Generalise the Addon Keyword List

## Problem

`app.py` lines 32–34 contain a hardcoded `addon_keywords` list with campaign-specific titles:

```python
addon_keywords = ['Addon', 'Terrible Means', 'Days by', 'Victory Point', 'Sleeping While',
                  'Acid Box', 'Scrapbook', 'Barking', 'Macbeth', 'Orlando', 'Postcard',
                  'Zine', 'Sketch', 'Digital Bundle', 'Physical bundle', 'print copy']
```

These titles belong to one specific campaign. The variable name implies it drives addon detection, but in practice **addon columns are already captured as the residual** — any column that isn't core or shipping ends up in addons regardless. The keyword list is therefore both misleading and inert.

The real risk: if a future version of the code ever uses `addon_keywords` to positively select addon columns (rather than deriving them as residuals), columns from other campaigns will be silently missed.

---

## Step-by-Step Fix

### Step 1 — Remove the unused variable

Delete lines 32–34 entirely:

```python
# DELETE these lines
addon_keywords = ['Addon', 'Terrible Means', 'Days by', 'Victory Point', 'Sleeping While',
                  'Acid Box', 'Scrapbook', 'Barking', 'Macbeth', 'Orlando', 'Postcard',
                  'Zine', 'Sketch', 'Digital Bundle', 'Physical bundle', 'print copy']
```

### Step 2 — Add a comment to the residual logic making the intent explicit

Find line 38–39:

```python
addon_cols = [col for col in df.columns
              if col not in core_cols and col not in shipping_cols]
```

Add a one-line comment above it:

```python
# Addons are everything not matched by core or shipping keywords
addon_cols = [col for col in df.columns
              if col not in core_cols and col not in shipping_cols]
```

### Step 3 (optional but recommended) — Show the user which columns landed where

After the three `*_cols` lists are built, add an expander so users can verify the classification for their specific CSV:

```python
with st.expander("Column classification (click to inspect)"):
    st.write(f"**Core ({len(core_cols)}):** {', '.join(core_cols) or 'none'}")
    st.write(f"**Shipping ({len(shipping_cols)}):** {', '.join(shipping_cols) or 'none'}")
    st.write(f"**Addons ({len(addon_cols)}):** {', '.join(addon_cols) or 'none'}")
```

This lets any campaign creator immediately spot a misclassified column without touching code.

### Step 4 (optional) — Make core keywords configurable via the sidebar

If you want power users to adjust classification without editing code, add a sidebar expander:

```python
with st.sidebar.expander("Advanced: Core keyword overrides"):
    extra_core = st.text_input(
        "Extra core keywords (comma-separated)", value=""
    )
    if extra_core:
        core_keywords += [k.strip() for k in extra_core.split(",") if k.strip()]
```

Place this block **before** the `core_cols` list comprehension so the extra keywords are included in classification.

### Step 5 — Verify

1. Run: `streamlit run app.py`
2. Upload any Kickstarter CSV from a different campaign.
3. Open the "Column classification" expander and confirm all columns are classified sensibly.
4. Download the addons CSV and confirm it contains the right columns with clean names.
