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


def classify_columns(columns: list) -> tuple:
    core = [c for c in columns if any(k in c for k in CORE_KEYWORDS)]
    shipping = [c for c in columns if any(k in c for k in SHIPPING_KEYWORDS)]
    addons = [c for c in columns if c not in core and c not in shipping]
    return core, shipping, addons
