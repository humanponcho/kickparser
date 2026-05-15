# Fix 5 — Add a Streamlit Config File

## Problem

There is no `.streamlit/config.toml` file. Without it:

- Streamlit Community Cloud uses its own default theme, which may clash with how the app looks locally.
- The server port and base URL path are unconfigured, which can cause issues behind proxies or in containerised deployments.
- Browser tab title and favicon fall back to Streamlit defaults (the page title set in `st.set_page_config` is used, but no favicon is set).
- There is no way to suppress the "Deploy" button shown in the top-right of every Streamlit app when running locally.

---

## Step-by-Step Fix

### Step 1 — Create the config directory

```bash
mkdir -p .streamlit
```

### Step 2 — Create `.streamlit/config.toml`

```toml
[theme]
base = "light"
primaryColor = "#05CE78"        # Kickstarter green
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#111111"
font = "sans serif"

[server]
headless = true                 # required for Cloud / Docker deployments
enableCORS = false
port = 8501

[browser]
gatherUsageStats = false        # opt out of Streamlit telemetry
```

**Key settings explained:**

| Setting | Why it matters |
|---|---|
| `theme.primaryColor` | Sets button and widget accent colour to Kickstarter green |
| `server.headless = true` | Prevents Streamlit from trying to open a browser tab — required on Cloud, CI, and Docker |
| `server.enableCORS = false` | Safe default for a single-origin app; set to `true` only if embedding in an iframe from another domain |
| `browser.gatherUsageStats = false` | Stops Streamlit from sending anonymous usage data |

### Step 3 — Add `.streamlit/` to version control

By default `.streamlit/` may be ignored. Confirm it is tracked:

```bash
git status .streamlit/
```

If it shows as untracked or ignored, add an explicit exception to `.gitignore`:

```
# In .gitignore — add this line if .streamlit is being ignored
!.streamlit/config.toml
```

Then stage and commit:

```bash
git add .streamlit/config.toml
git commit -m "Add Streamlit config with theme and server settings"
```

### Step 4 — (Optional) Add a custom favicon

Place a small `.png` or `.ico` file in the project root, for example `favicon.png`, then update `app.py` line 8:

```python
# Before
st.set_page_config(page_title="KS Backer Parser", layout="wide")

# After
st.set_page_config(
    page_title="KS Backer Parser",
    page_icon="favicon.png",    # path relative to project root
    layout="wide",
)
```

### Step 5 — Verify locally

```bash
streamlit run app.py
```

Open `http://localhost:8501`. You should see:

- The Kickstarter-green accent colour on buttons and the file uploader.
- No "Deploy" prompt in the top-right corner (suppressed by `headless = true`).
- Browser tab titled "KS Backer Parser".

### Step 6 — Verify on Streamlit Community Cloud

1. Push the `.streamlit/config.toml` to GitHub.
2. Redeploy the app on [share.streamlit.io](https://share.streamlit.io) (or it will auto-redeploy if already connected).
3. Confirm the theme is applied on the live URL.

---

## Final Directory Structure After This Fix

```
kickparser/
├── .streamlit/
│   └── config.toml      ← new
├── app.py
├── requirements.txt
├── README.md
└── HOWTO.md
```
