import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_extras.metric_cards import style_metric_cards
from datetime import datetime

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="KoboToolbox Advanced Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# SIDEBAR SETTINGS
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Kobotoolbox_logo.svg/2560px-Kobotoolbox_logo.svg.png")
    st.title("⚙️ Dashboard Settings")

    api_token = st.text_input("🔑 Kobo API Token", type="password")
    form_id = st.text_input("📄 Form ID")

    refresh_rate = st.slider("⏱ Auto-Refresh Rate", 10, 300, 30)
    st.caption("Dashboard refreshes automatically.")

    st.divider()
    start_dashboard = st.button("🚀 Launch Advanced Dashboard", use_container_width=True)

# Auto-refresh page
st.autorefresh(interval=refresh_rate * 1000, key="data_refresh_key")

# ---------------------------------------------------------
# FETCH DATA FUNCTION
# ---------------------------------------------------------
def fetch_kobo_data(token, form_id):
    url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_id}/data/"

    headers = {"Authorization": f"Token {token}"}

    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            st.error(f"❌ Failed to fetch data — Status: {r.status_code}")
            return None
        data = r.json()
        df = pd.json_normalize(data.get("results", []))
        return df
    
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None


# ---------------------------------------------------------
# START DASHBOARD
# ---------------------------------------------------------
if start_dashboard:

    if not api_token or not form_id:
        st.warning("⚠️ Please enter a valid API Token and Form ID.")
        st.stop()

    df = fetch_kobo_data(api_token, form_id)

    if df is None:
        st.stop()

    if df.empty:
        st.info("📭 No submissions available yet.")
        st.stop()

    st.title("📊 KoboToolbox Advanced Analytics Dashboard")
    st.caption(f"Last updated: **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")

    st.divider()

    # ---------------------------------------------------------
    # SUMMARY METRICS
    # ---------------------------------------------------------
    st.subheader("📌 Summary Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Submissions", len(df))
    c2.metric("Available Fields", df.shape[1])
    c3.metric("Earliest Submission", df["_submission_time"].min() if "_submission_time" in df else "N/A")
    c4.metric("Most Recent Submission", df["_submission_time"].max() if "_submission_time" in df else "N/A")

    style_metric_cards(background_color="#f0f2f6", border_size_px=1)

    st.divider()

    # ---------------------------------------------------------
    # ADVANCED FILTER SECTION
    # ---------------------------------------------------------
    st.subheader("🔍 Advanced Filtering")

    filter_cols = st.multiselect(
        "Select columns to filter:", df.columns, help="Choose any number of columns"
    )

    filtered_df = df.copy()

    for col in filter_cols:
        vals = st.multiselect(f"Filter values for **{col}**:", df[col].dropna().unique())
        if vals:
            filtered_df = filtered_df[filtered_df[col].isin(vals)]

    st.divider()

    # ---------------------------------------------------------
    # DATA TABLE
    # ---------------------------------------------------------
    st.subheader("📄 Live Data Table (Auto-Updated)")
    st.dataframe(filtered_df, use_container_width=True, height=400)

    st.divider()

    # ---------------------------------------------------------
    # ANALYTICS & VISUALIZATIONS
    # ---------------------------------------------------------
    st.subheader("📈 Analytics & Insights")

    chart_col = st.selectbox("Select column to visualize:", df.columns)

    try:
        chart_data = filtered_df[chart_col].value_counts().reset_index()
        chart_data.columns = [chart_col, "Count"]

        fig = px.bar(
            chart_data,
            x=chart_col,
            y="Count",
            title=f"Distribution of {chart_col}",
            text_auto=True,
        )
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("⚠️ Unable to plot this column.")

    st.divider()

    # ---------------------------------------------------------
    # OPTIONAL MAP ANALYSIS
    # ---------------------------------------------------------
    geo_cols = [c for c in df.columns if "lat" in c.lower() or "lon" in c.lower()]
    if len(geo_cols) >= 2:
        st.subheader("🗺️ Geo-Location Map")

        try:
            lat_col = geo_cols[0]
            lon_col = geo_cols[1]

            map_df = filtered_df[[lat_col, lon_col]].dropna()
            st.map(map_df, latitude=lat_col, longitude=lon_col)
        except:
            st.warning("⚠️ Map could not be generated.")

    st.divider()

    # ---------------------------------------------------------
    # DATA EXPORT
    # ---------------------------------------------------------
    st.subheader("⬇ Download Data")

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Filtered CSV",
        data=csv,
        file_name="kobo_filtered_data.csv",
        use_container_width=True,
    )
