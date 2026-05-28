import streamlit as st
import pandas as pd
import zipfile
import io
from datetime import datetime
from parser_logic import (clean_column_name, classify_columns, dedupe_column_names,
                          build_label, build_items_list, strip_pii,
                          detect_format, normalise_bigcartel, LABEL_COLUMNS)

st.set_page_config(page_title="KS Backer Parser", layout="wide")


# ====================== AUTHENTICATION ======================
def check_password() -> bool:
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🎯 Kickstarter Backer Parser")
    st.markdown("This tool handles personal backer data. Enter the password to continue.")
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("Incorrect password — try again.")
    return False

if not check_password():
    st.stop()


st.title("🎯 Kickstarter Backer CSV Parser")
st.markdown("**Smart splitting + Fulfillment tools**")

# ====================== FILE UPLOAD ======================
uploaded_file = st.file_uploader("Upload a Kickstarter (All Rewards) or Big Cartel (Orders) CSV", type=["csv"])

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
            "Supported formats: Kickstarter 'All Rewards' export and Big Cartel orders export."
        )
        st.stop()

    source_format = detect_format(df)
    if source_format == 'bigcartel':
        df = normalise_bigcartel(df)
        st.info("📦 Big Cartel format detected — normalised automatically.")

    REQUIRED_COLUMNS = ['Backer Number', 'Reward Title', 'Shipping Country']
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(
            f"The uploaded CSV is missing expected columns: **{', '.join(missing)}**\n\n"
            "Supported formats: Kickstarter **Reports → All Rewards** export "
            "and Big Cartel **Orders → Export** CSV."
        )
        st.stop()

    format_label = "Big Cartel" if source_format == 'bigcartel' else "Kickstarter"
    st.success(
        f"✅ Loaded **{len(df):,} orders** × **{len(df.columns)} columns** "
        f"from `{uploaded_file.name}` ({format_label})"
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

    rewards = sorted(df['Reward Title'].dropna().unique())
    selected_rewards = st.sidebar.multiselect(
        "Filter by Reward", options=rewards, default=rewards
    )

    filtered_df = df.copy()
    if selected_countries:
        filtered_df = filtered_df[filtered_df['Shipping Country'].isin(selected_countries)]
    if selected_rewards:
        filtered_df = filtered_df[filtered_df['Reward Title'].isin(selected_rewards)]

    if filtered_df.empty:
        st.warning("No backers match the current filters. Adjust the filters in the sidebar.")
        st.stop()

    st.sidebar.metric("Filtered Backers", len(filtered_df))

    # ====================== CREATE SPLITS ======================
    core_df = filtered_df[core_cols].copy()
    addons_df = filtered_df[['Backer Number'] + addon_cols].copy()
    shipping_df = filtered_df[['Backer Number'] + shipping_cols].copy()

    addons_df.columns = ['Backer Number'] + dedupe_column_names([clean_column_name(col) for col in addon_cols])

    label_source_cols = [c for c in LABEL_COLUMNS if c in filtered_df.columns]
    labels_df = filtered_df[['Backer Number']].copy()
    labels_df['Label'] = filtered_df[label_source_cols].apply(build_label, axis=1)
    if 'Items' in filtered_df.columns:
        labels_df['Items'] = filtered_df['Items']
    else:
        labels_df['Items'] = filtered_df.apply(lambda row: build_items_list(row, addon_cols), axis=1)

    anon_df = strip_pii(filtered_df)

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Addons", "Shipping", "Labels", "Raw Data", "Anonymised"])
    with tab1:
        st.dataframe(addons_df, use_container_width=True)
    with tab2:
        st.dataframe(shipping_df, use_container_width=True)
    with tab3:
        st.dataframe(labels_df, use_container_width=True)
    with tab4:
        st.dataframe(filtered_df, use_container_width=True)
    with tab5:
        st.caption("Names, emails, and addresses removed — safe for statistical analysis.")
        st.dataframe(anon_df, use_container_width=True)

    # ====================== DOWNLOADS ======================
    st.header("📥 Download Split Files")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"core_backers_{timestamp}.csv", core_df.to_csv(index=False))
        z.writestr(f"addons_{timestamp}.csv", addons_df.to_csv(index=False))
        z.writestr(f"shipping_{timestamp}.csv", shipping_df.to_csv(index=False))
        z.writestr(f"labels_{timestamp}.csv", labels_df.to_csv(index=False))
        z.writestr(f"anon_stats_{timestamp}.csv", anon_df.to_csv(index=False))

    zip_buffer.seek(0)

    st.download_button(
        label="📦 Download All Files (ZIP)",
        data=zip_buffer,
        file_name=f"ks_backers_split_{timestamp}.zip",
        mime="application/zip"
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.download_button("Core Backers CSV", core_df.to_csv(index=False),
                           f"core_backers_{timestamp}.csv", "text/csv")
    with col2:
        st.download_button("Addons CSV", addons_df.to_csv(index=False),
                           f"addons_{timestamp}.csv", "text/csv")
    with col3:
        st.download_button("Shipping CSV", shipping_df.to_csv(index=False),
                           f"shipping_{timestamp}.csv", "text/csv")
    with col4:
        st.download_button("Labels CSV", labels_df.to_csv(index=False),
                           f"labels_{timestamp}.csv", "text/csv")
    with col5:
        st.download_button("Anonymised Stats CSV", anon_df.to_csv(index=False),
                           f"anon_stats_{timestamp}.csv", "text/csv")

else:
    st.info("👆 Upload a Kickstarter or Big Cartel CSV to start")
    st.markdown("**Supported formats:** Kickstarter *Reports → All Rewards* · Big Cartel *Orders → Export*")

st.caption("Kickstarter Backer Parser v1.0 • Auto-detection + Fulfillment tools")
