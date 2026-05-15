# Kickstarter Backer Parser — How to Use

A Streamlit web app that splits a raw Kickstarter backer CSV export into three clean, focused files and provides instant fulfillment insights.

---

## Codebase Status

### What Works (v1.0 MVP)

| Feature | Status |
|---|---|
| CSV upload and parsing | ✅ Working |
| Auto-detection of Core / Shipping / Addon columns | ✅ Working |
| Column name cleaning (strips `[Addon: N]` prefixes, normalises special chars) | ✅ Working |
| Splitting into three DataFrames | ✅ Working |
| Country filter in sidebar | ✅ Working |
| Fulfillment dashboard (4 metrics + bar chart) | ✅ Working |
| Tabbed data preview (Core, Addons, Shipping, Raw) | ✅ Working |
| ZIP download of all three CSVs | ✅ Working |
| Individual CSV downloads | ✅ Working |
| Timestamped filenames | ✅ Working |

### Known Issues / Limitations

| Issue | Impact |
|---|---|
| `addon_keywords` contains campaign-specific titles (Macbeth, Orlando, Zine, etc.) | Addon detection is hardcoded for one campaign; other campaigns' add-on columns will fall into the "addon" bucket only because they aren't core/shipping, which actually still works but the keyword list is misleading |
| No error handling for missing expected columns (`Backer Number`, `Shipping Address 1`, `Reward Title`, `Shipping Country`) | App will crash with a `KeyError` if the CSV is missing any of these |
| No input validation or empty-file guard | Uploading an empty or corrupt CSV raises an unhandled exception |
| No test suite | Zero test coverage |
| No Streamlit config file (`/.streamlit/config.toml`) | Fine locally; recommended for Cloud deployment |

### Roadmap (not yet implemented)

- Addon popularity rankings and charts
- Fulfillment readiness report with per-backer flags
- Search/filter by backer name or email
- Support for BackerKit / Gamefound CSV formats
- Persistent storage for multiple campaigns
- Ready-to-print shipping label export

---

## Quick Start (Local)

### Prerequisites

- Python 3.9+
- `pip`

### 1. Clone the repo

```bash
git clone https://github.com/humanponcho/kickparser.git
cd kickparser
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies installed:

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | >=1.38.0 | Web UI framework |
| `pandas` | >=2.2.0 | CSV parsing and data manipulation |

### 4. Run the app

```bash
streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

---

## Using the App

### Step 1 — Upload your CSV

Click **"Upload your raw Kickstarter backers CSV"** and select the file you exported from Kickstarter (the "All Rewards" export, which includes all backer and address columns).

The app immediately shows how many rows (backers) and columns were loaded.

### Step 2 — Filter by country (optional)

The **sidebar** shows a multiselect list of every country in your export. The first five are selected by default. Adjust the selection to focus on a specific fulfilment region; all metrics, previews, and downloads will reflect your filter.

### Step 3 — Read the Fulfillment Dashboard

Four headline metrics are shown at the top:

| Metric | What it shows |
|---|---|
| **Total Filtered Backers** | Rows matching the current country filter |
| **Physical Orders** | Backers whose Reward Title does not contain "Digital" |
| **Missing Address** | Rows where the first shipping address field is blank |
| **Countries** | Number of distinct shipping countries in the filtered set |

Below the metrics, a bar chart shows the top 10 shipping countries.

### Step 4 — Preview the split data

Four tabs let you inspect the three output files and the original data (limited to 10–15 rows for performance):

- **Core Backers** — Backer Number, UID, Name, Email, Reward Title, Pledge Amount, dates, statuses, notes, billing columns
- **Addons** — Everything that isn't core or shipping, with cleaned column names
- **Shipping** — All columns containing "Shipping" (address lines, city, state, post code, country, phone)
- **Raw Data** — The original unmodified CSV

### Step 5 — Download

Three download options are available:

| Button | Output |
|---|---|
| **Download All Three Files (ZIP)** | A single ZIP containing all three CSVs |
| **Core Backers CSV** | `core_backers_YYYYMMDD_HHMM.csv` |
| **Addons CSV** | `addons_YYYYMMDD_HHMM.csv` |
| **Shipping CSV** | `shipping_YYYYMMDD_HHMM.csv` |

All filenames include a timestamp so repeated exports don't overwrite each other.

---

## Column Detection Logic

The app classifies every column in your CSV into one of three buckets using keyword matching:

**Core** — matched if the column name contains any of:
`Backer Number`, `Backer UID`, `Backer Name`, `Email`, `Reward Title`, `Pledge Amount`, `Pledged At`, `Late Pledge`, `Fulfillment Status`, `Pledged Status`, `Notes`, `Billing`

**Shipping** — matched if the column name contains:
`Shipping`

**Addons** — everything else (columns not matched by core or shipping keywords)

Column names in the Addons file are cleaned:
- `[Addon: N]` prefixes are stripped
- Special characters are removed
- Spaces are replaced with underscores

---

## Deploy to Streamlit Community Cloud

1. Push this repo to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in.
3. Click **New app** → connect your GitHub account → select the repo.
4. Set **Branch** to `main` and **Main file path** to `app.py`.
5. Click **Deploy**. A public URL is live within ~1 minute.

No extra configuration is required for the free tier.

---

## Things to Fix Before Production Use

Priority order for making the app robust:

1. **Guard against missing columns** — wrap column lookups in existence checks and show a clear error message to the user if expected columns are absent.
2. **Generalise the addon keyword list** — the current list contains campaign-specific titles; either remove them or make the list configurable via the UI.
3. **Add input validation** — check that the uploaded file is non-empty and is a valid CSV before processing.
4. **Add a Streamlit config file** — create `.streamlit/config.toml` to control theme and server settings for Cloud deployments.
5. **Write tests** — unit tests for `clean_column_name()` and the column classification logic would catch regressions quickly.
