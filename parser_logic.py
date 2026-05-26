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


def detect_format(df: pd.DataFrame) -> str:
    if 'Buyer first name' in df.columns and 'Number' in df.columns:
        return 'bigcartel'
    return 'kickstarter'


def _parse_bigcartel_items_str(items_str: str) -> list:
    """Return list of (name, qty) tuples from packed Big Cartel items string."""
    if not items_str or str(items_str).lower() == 'nan':
        return []
    result = []
    for item in str(items_str).split(';'):
        item = item.strip()
        if not item:
            continue
        parts = {}
        for p in item.split('|'):
            if ':' in p:
                k, v = p.split(':', 1)
                parts[k.strip()] = v.strip()
        name = parts.get('product_name', '').strip()
        if not name:
            continue
        try:
            qty = int(float(parts.get('quantity', '1')))
        except (ValueError, TypeError):
            qty = 1
        result.append((name, qty))
    return result


def parse_bigcartel_items(items_str: str) -> str:
    parsed = _parse_bigcartel_items_str(items_str)
    lines = [f"{qty}x {name}" if qty > 1 else name for name, qty in parsed]
    return '\n'.join(f"- {line}" for line in lines)


def _bigcartel_first_product(items_str: str) -> str:
    parsed = _parse_bigcartel_items_str(items_str)
    return parsed[0][0] if parsed else ''


def normalise_bigcartel(df: pd.DataFrame) -> pd.DataFrame:
    def safe(col):
        return df[col].fillna('').astype(str).str.strip()

    addr1 = safe('Shipping address 1')
    addr2 = safe('Shipping address 2')
    combined_addr1 = addr1.where(addr2 == '', addr1 + ', ' + addr2)

    full_name = (safe('Buyer first name') + ' ' + safe('Buyer last name')).str.strip()

    def concat_full_address(row):
        parts = [
            str(row.get('Shipping address 1', '') or '').strip(),
            str(row.get('Shipping address 2', '') or '').strip(),
            str(row.get('Shipping city', '') or '').strip(),
            str(row.get('Shipping state', '') or '').strip(),
            str(row.get('Shipping zip', '') or '').strip(),
            str(row.get('Shipping country', '') or '').strip(),
        ]
        return ', '.join(p for p in parts if p)

    out = pd.DataFrame()
    out['Backer Number']      = safe('Number')
    out['Backer Name']        = full_name
    out['Email']              = safe('Buyer email')
    out['Reward Title']       = df['Items'].apply(_bigcartel_first_product)
    out['Pledge Amount']      = df['Total price']
    out['Pledged At']         = safe('Date')
    out['Fulfillment Status'] = safe('Shipping status')
    out['Shipping Name']      = full_name
    out['Shipping Address 1'] = combined_addr1
    out['Shipping City']      = safe('Shipping city')
    out['Shipping State']     = safe('Shipping state')
    out['Shipping Postal Code'] = safe('Shipping zip')
    out['Shipping Country']   = safe('Shipping country')
    out['Shipping Country Code'] = safe('Shipping country')
    out['Shipping Full Address'] = df.apply(concat_full_address, axis=1)
    out['Items']              = df['Items'].apply(parse_bigcartel_items)
    out['Item Count']         = df['Item count']
    out['Total Shipping']     = df['Total shipping']
    out['Discount Code']      = safe('Discount code')
    return out


def classify_columns(columns: list) -> tuple:
    core = [c for c in columns if any(k in c for k in CORE_KEYWORDS)]
    shipping = [c for c in columns if any(k in c for k in SHIPPING_KEYWORDS)]
    addons = [c for c in columns if c not in core and c not in shipping]
    return core, shipping, addons
