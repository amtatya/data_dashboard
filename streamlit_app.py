import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="KoboToolbox Dashboard",
    layout="wide",
)


st.title("📊KoboToolbox Dashboard")
st.write("Real-time monitoring, interactive charts, filters, and auto-refresh.")
start_button = st.button("🚀 Start Live Dashboard", use_container_width=True, key="start_live_dashboard")

# ---------------------------------------------------------
# USER INPUTS
# ---------------------------------------------------------
api_token = "4fefa33dcfbd11038b91e03c4da752db845fb790"
form_id = "aF3hzEPTJkYZqMQk37NCpd"

refresh_rate = st.slider("⏱ Auto-Refresh (seconds)", 10, 300, 30)
st.write(f"Dashboard will automatically update every {refresh_rate} seconds.")

placeholder = st.empty()  # placeholder for live refresh UI

# ---------------------------------------------------------
# FUNCTION TO FETCH DATA
# ---------------------------------------------------------
def get_kobo_data(api_token, form_id):
    url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_id}/data/"

    headers = {
        "Authorization": f"Token {api_token}"
    }

    response = requests.get(url, headers=headers)

    print("STATUS:", response.status_code)
    print("RAW:", response.text[:500])  # DEBUG

    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code}")

    try:
        data = response.json()
    except Exception as e:
        print("JSON ERROR:", e)
        print("Full response:", response.text)
        raise e

    df = pd.json_normalize(data.get("results", []))
    return df

# ---------------------------------------------------------
# LIVE AUTO-UPDATE LOOP
# ---------------------------------------------------------
if api_token and form_id and start_button:

    while True:
        with placeholder.container():

            st.info("🔄 Fetching latest data from KoboToolbox...")

            df = get_kobo_data(api_token, form_id)

            if df is None:
                st.error("❌ Failed to fetch data. Check token or form ID.")
                break
            if df.empty:
                st.info("No submissions found for this form.")
                st.stop()

            # --------------------------------------------
            # METRICS
            # --------------------------------------------
            st.subheader("📌 Summary Metrics")

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Submissions", len(df))
            col2.metric("Columns Available", df.shape[1])
            col3.metric("Last Update", pd.Timestamp.now().strftime("%H:%M:%S"))

            # --------------------------------------------
            # FILTERS
            # --------------------------------------------
            st.subheader("🔍 Data Filters")

            column_filter = st.selectbox("Choose column to filter:", df.columns, key="filter_col")
            unique_vals = df[column_filter].dropna().unique()

            selected_filter = st.multiselect(
                "Select values to include:", unique_vals
            )

            filtered_df = df
            if selected_filter:
                filtered_df = df[df[column_filter].isin(selected_filter)]

            # --------------------------------------------
            # DATA TABLE
            # --------------------------------------------
            st.subheader("📄 Live Data Table")
            st.dataframe(filtered_df, height=350)

            # --------------------------------------------
            # INTERACTIVE CHARTS (Plotly)
            # --------------------------------------------
            st.subheader("📈 Interactive Visualization")

            selected_chart_col = st.selectbox("Choose a column to visualize:", df.columns, key="chart_col")

            try:
                fig = px.bar(
                    filtered_df[selected_chart_col].value_counts(),
                    title=f"Distribution of {selected_chart_col}",
                )
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.warning("⚠ Cannot plot this column.")

            # --------------------------------------------
            # DOWNLOAD SECTION
            # --------------------------------------------
            st.subheader("⬇ Download Data")

            # CSV
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="kobo_data.csv", use_container_width=True, key="csv_down")

            
        time.sleep(refresh_rate)
