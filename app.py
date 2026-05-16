import streamlit as st
import pandas as pd
import zipfile
import io
from datetime import datetime
from parser_logic import clean_column_name, classify_columns, dedupe_column_names

st.set_page_config(page_title="KS Backer Parser", layout="wide")
st.title("🎯 Kickstarter Backer CSV Parser")
st.markdown("**Smart splitting + Fulfillment tools**")

# ====================== FILE UPLOAD ======================
uploaded_file = st.file_uploader("Upload your raw Kickstarter backers CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read the file as a CSV: **{e}**\n\nPlease upload a valid `.csv` export.")
        st.stop()

    if df.empty:
        st.warning("The uploaded file contains no rows. Please check your export and try again.")
        st.stop()

    if len(df.columns) < 5:
        st.warning(
            f"Only {len(df.columns)} column(s) found. "
            "This doesn't look like a Kickstarter 'All Rewards' export. "
            "Please re-export from **Reports → All Rewards**."
        )
        st.stop()

    REQUIRED_COLUMNS = ['Backer Number', 'Reward Title', 'Shipping Country']
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(
            f"The uploaded CSV is missing expected columns: **{', '.join(missing)}**\n\n"
            "Please export from Kickstarter using **Reports → All Rewards** "
            "and upload that file."
        )
        st.stop()

    st.success(
        f"✅ Loaded **{len(df):,} backers** × **{len(df.columns)} columns** "
        f"from `{uploaded_file.name}`"
    )

    # ====================== ROBUST AUTO COLUMN DETECTION ======================
    core_cols, shipping_cols, addon_cols = classify_columns(df.columns.tolist())

    with st.expander("Column classification (click to inspect)"):
        st.write(f"**Core ({len(core_cols)}):** {', '.join(core_cols) or 'none'}")
        st.write(f"**Shipping ({len(shipping_cols)}):** {', '.join(shipping_cols) or 'none'}")
        st.write(f"**Addons ({len(addon_cols)}):** {', '.join(addon_cols) or 'none'}")

    # ====================== SIDEBAR FILTERS ======================
    st.sidebar.header("🔍 Filters")

    countries = sorted(df['Shipping Country'].dropna().unique())
    selected_countries = st.sidebar.multiselect(
        "Filter by Country", options=countries,
        default=countries[:5] if len(countries) > 5 else countries
    )

    filtered_df = df[df['Shipping Country'].isin(selected_countries)].copy() if selected_countries else df.copy()

    if filtered_df.empty:
        st.warning("No backers match the current country filter. Adjust the filter in the sidebar.")
        st.stop()

    st.sidebar.metric("Filtered Backers", len(filtered_df))

    # ====================== CREATE SPLITS ======================
    core_df = filtered_df[core_cols].copy()
    addons_df = filtered_df[['Backer Number'] + addon_cols].copy()
    shipping_df = filtered_df[['Backer Number'] + shipping_cols].copy()

    addons_df.columns = ['Backer Number'] + dedupe_column_names([clean_column_name(col) for col in addon_cols])

    # ====================== FULFILLMENT DASHBOARD ======================
    st.header("📦 Fulfillment Dashboard")
    dash1, dash2, dash3, dash4 = st.columns(4)

    with dash1:
        st.metric("Total Filtered Backers", len(filtered_df))
    with dash2:
        physical = len(filtered_df[~filtered_df['Reward Title'].str.contains("Digital", na=False)])
        st.metric("Physical Orders", physical)
    with dash3:
        addr_col = next((c for c in shipping_df.columns if 'Address' in c), None)
        if addr_col:
            missing_addr = shipping_df[addr_col].isna().sum() + (shipping_df[addr_col] == "").sum()
            st.metric("Missing Address", int(missing_addr))
        else:
            st.metric("Missing Address", "N/A")
    with dash4:
        st.metric("Countries", filtered_df['Shipping Country'].nunique())

    st.subheader("Top Shipping Countries")
    st.bar_chart(filtered_df['Shipping Country'].value_counts().head(10))

    # ====================== TABS ======================
    tab1, tab2, tab3, tab4 = st.tabs(["Core Backers", "Addons", "Shipping", "Raw Data"])
    with tab1:
        st.dataframe(core_df.head(15), use_container_width=True)
    with tab2:
        st.dataframe(addons_df.head(15), use_container_width=True)
    with tab3:
        st.dataframe(shipping_df.head(15), use_container_width=True)
    with tab4:
        st.dataframe(filtered_df.head(10), use_container_width=True)

    # ====================== DOWNLOADS ======================
    st.header("📥 Download Split Files")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"core_backers_{timestamp}.csv", core_df.to_csv(index=False))
        z.writestr(f"addons_{timestamp}.csv", addons_df.to_csv(index=False))
        z.writestr(f"shipping_{timestamp}.csv", shipping_df.to_csv(index=False))

    zip_buffer.seek(0)

    st.download_button(
        label="📦 Download All Three Files (ZIP)",
        data=zip_buffer,
        file_name=f"ks_backers_split_{timestamp}.zip",
        mime="application/zip"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("Core Backers CSV", core_df.to_csv(index=False),
                           f"core_backers_{timestamp}.csv", "text/csv")
    with col2:
        st.download_button("Addons CSV", addons_df.to_csv(index=False),
                           f"addons_{timestamp}.csv", "text/csv")
    with col3:
        st.download_button("Shipping CSV", shipping_df.to_csv(index=False),
                           f"shipping_{timestamp}.csv", "text/csv")

else:
    st.info("👆 Upload your Kickstarter 'All Rewards' CSV to start")
    st.markdown("**Tip**: This app auto-detects columns using keywords and includes fulfillment insights.")

st.caption("Kickstarter Backer Parser v1.0 • Auto-detection + Fulfillment tools")
