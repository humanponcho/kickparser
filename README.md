# Kickstarter Backer Parser

A simple, powerful Streamlit web app that intelligently splits large Kickstarter backer exports into organized files and provides fulfillment insights.

## Features

- **Smart Auto-Detection** of Core, Addon, and Shipping columns using keyword matching
- **Automatic splitting** into three clean CSVs:
  - `core_backers.csv`
  - `addons.csv` (with cleaned column names)
  - `shipping.csv`
- **Country-based filtering** (sidebar)
- **Fulfillment Dashboard** with key metrics and charts
- **One-click ZIP download** of all files
- Clean, timestamped filenames

## How to Run Locally

### 1. Setup

```bash
# Clone or create project folder
mkdir ks-backers-parser
cd ks-backers-parser

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
streamlit run app.py
```

Open your browser at the URL shown (usually `http://localhost:8501`).

## Project Structure

```
ks-backers-parser/
├── app.py                 # Main Streamlit application
├── requirements.txt
├── README.md
└── output/                # (optional) folder for saved files
```

## Current Capabilities

- Robust column classification even with messy Kickstarter column names
- Handles 200–2000+ backers efficiently
- Fulfillment metrics (physical orders, missing addresses, country breakdown)
- Responsive and user-friendly interface

## Future Enhancements (Nice-to-Haves)

- Addon popularity rankings and charts
- Fulfillment readiness report (with flags)
- Search by backer name/email
- Support for BackerKit / Gamefound exports
- Persistent storage for multiple campaigns
- Export ready-to-print shipping labels

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (public)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect GitHub → select repo → branch: `main` → main file: `app.py`
4. Click **Deploy** — live public URL in ~1 minute

---

Built as an MVP — ready for rapid iteration.
