import re
import pandas as pd

CORE_KEYWORDS = [
    'Backer Number', 'Backer UID', 'Backer Name', 'Email', 'Reward Title',
    'Pledge Amount', 'Pledged At', 'Late Pledge', 'Fulfillment Status',
    'Pledged Status', 'Notes', 'Billing',
]
SHIPPING_KEYWORDS = ['Shipping']

PII_KEYWORDS = ['Name', 'Email', 'UID', 'Billing', 'Address', 'City', 'State', 'Zip', 'Postcode', 'Phone', 'Notes']

LABEL_COLUMNS = [
    'Shipping Name',
    'Shipping Address 1',
    'Shipping City',
    'Shipping State',
    'Shipping Postal Code',
    'Shipping Country Code',
]


def clean_column_name(col: str) -> str:
    col = re.sub(r'\[Addon: \d+\]\s*', '', col)
    col = col.replace(" by ", " - ").replace("’", "'").replace(" of of ", " of ")
    col = re.sub(r'[^a-zA-Z0-9\s\-]', '', col)
    return re.sub(r'\s+', '_', col.strip())


def dedupe_column_names(cols: list) -> list:
    seen = {}
    result = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            result.append(col)
    return result


def build_label(row) -> str:
    def val(key):
        v = row.get(key, '')
        if v != v:  # NaN check (NaN != NaN)
            return ''
        return str(v or '').strip()

    name     = val('Shipping Name')
    addr1    = val('Shipping Address 1')
    city     = val('Shipping City')
    state    = val('Shipping State')
    postal   = val('Shipping Postal Code')
    country  = val('Shipping Country Code')

    city_state = ', '.join(filter(None, [city, state]))
    city_line  = f"{city_state}  {postal}".strip() if postal else city_state

    return '\n'.join(line for line in [name, addr1, city_line, country] if line)


_ADDON_RE = re.compile(r'^\[Addon: \d+\]')


def build_items_list(row, addon_cols: list) -> str:
    items = []

    reward = str(row.get('Reward Title', '') or '').strip()
    if reward and reward.lower() != 'nan':
        items.append(reward)

    for col in addon_cols:
        if not _ADDON_RE.match(col):
            continue
        v = row.get(col, '')
        if v != v:  # NaN
            continue
        v_str = str(v).strip()
        if not v_str or v_str in ('0', '0.0'):
            continue
        display = clean_column_name(col).replace('_', ' ')
        try:
            qty = int(float(v_str))
            if qty <= 0:
                continue
            items.append(f"{qty}x {display}" if qty > 1 else display)
        except ValueError:
            items.append(display)  # non-numeric reply — show name only

    return '\n'.join(f"- {item}" for item in items)


def strip_pii(df: pd.DataFrame) -> pd.DataFrame:
    safe_cols = [c for c in df.columns if not any(k.lower() in c.lower() for k in PII_KEYWORDS)]
    return df[safe_cols].copy()


def classify_columns(columns: list) -> tuple:
    core = [c for c in columns if any(k in c for k in CORE_KEYWORDS)]
    shipping = [c for c in columns if any(k in c for k in SHIPPING_KEYWORDS)]
    addons = [c for c in columns if c not in core and c not in shipping]
    return core, shipping, addons
