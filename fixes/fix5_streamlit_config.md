# Fix 5 — Add a Streamlit Config File

## Problem

There was no `.streamlit/config.toml` file. Without it:

- Streamlit Community Cloud used its own default theme, which clashed with how the app looked locally.
- The server was unconfigured for headless/containerised deployments.
- Streamlit telemetry was enabled by default.

---

## Changes Applied

### Created `.streamlit/config.toml`

```toml
[theme]
base = "light"
primaryColor = "#05CE78"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#111111"
font = "sans serif"

[server]
headless = true
enableCORS = false
port = 8501

[browser]
gatherUsageStats = false
```

**Key settings:**

| Setting | Why |
|---|---|
| `primaryColor = "#05CE78"` | Kickstarter green on buttons and widgets |
| `server.headless = true` | Required for Streamlit Community Cloud and Docker — stops Streamlit trying to open a browser |
| `browser.gatherUsageStats = false` | Opts out of anonymous telemetry |

---

## Verification

```bash
streamlit run app.py
```

Open `http://localhost:8501`. Buttons and the file uploader should appear in Kickstarter green. Push to GitHub and redeploy on Streamlit Community Cloud — the theme applies automatically.
