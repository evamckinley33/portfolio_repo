import streamlit as st
import pandas as pd

# -----------------------------------
# App Setup (must be first st call)
# -----------------------------------
st.set_page_config(page_title="Fitness Insights", layout="wide")
st.title("🏋️ Fitness Insights Dashboard")

# -----------------------------------
# Session Handling
# -----------------------------------
@st.cache_resource
def get_snowflake_session():
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        pass

    from snowflake.snowpark import Session
    connection_parameters = {
        "account": st.secrets["snowflake"]["account"],
        "user": st.secrets["snowflake"]["user"],
        "password": st.secrets["snowflake"]["password"],
        "role": st.secrets["snowflake"]["role"],
        "warehouse": st.secrets["snowflake"]["warehouse"],
        "database": "FITNESS_APP",
        "schema": "ANALYTICS"
    }
    return Session.builder.configs(connection_parameters).create()

# -----------------------------------
# Upload Section
# -----------------------------------
st.header("Upload Your Fitness Data")

uploaded_file = st.file_uploader("Upload CSV from Garmin, Apple, Whoop, or Fitbit")
user_id = st.text_input("Enter User ID")
device_type = st.selectbox("Device Type", ["Garmin", "Apple Watch", "Whoop", "Fitbit"])

if uploaded_file and user_id:
    df = pd.read_csv(uploaded_file)

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df.head())

    if st.button("Upload to Snowflake"):
        try:
            session = get_snowflake_session()  # ✅ lazy connect
            df["USER_ID"] = user_id
            session.write_pandas(
                df,
                table_name="ACTIVITY",
                schema="RAW",
                auto_create_table=False
            )
            st.success("Data uploaded successfully!")
        except Exception as e:
            st.error(f"Upload failed: {e}")

# -----------------------------------
# Analytics Section
# -----------------------------------
st.header("Your Fitness Insights")

if user_id:
    session = get_snowflake_session()  # ✅ lazy connect

    query = f"""
        SELECT *
        FROM ANALYTICS.ENHANCED_METRICS
        WHERE USER_ID = '{user_id}'
        ORDER BY DATE
    """

    data = session.sql(query).to_pandas()

    if not data.empty:
        data["DATE"] = pd.to_datetime(data["DATE"])

        # -----------------------------------
        # KPI Metrics
        # -----------------------------------
        st.subheader("Key Metrics")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Steps", int(data["STEPS"].mean()))
        col2.metric("Avg Sleep (hrs)", round(data["TOTAL_SLEEP_HOURS"].mean(), 2))
        col3.metric("Avg Recovery", round(data["RECOVERY_SCORE"].mean(), 1))
        col4.metric("Avg Readiness", int(data["READINESS_SCORE"].mean()))

        # -----------------------------------
        # Activity Trends
        # -----------------------------------
        st.subheader("Activity Trends")
        st.line_chart(data.set_index("DATE")[["STEPS", "CALORIES_BURNED"]])

        # -----------------------------------
        # Sleep Analysis
        # -----------------------------------
        st.subheader("Sleep Analysis")

        col1, col2 = st.columns(2)
        with col1:
            st.write("Sleep Duration")
            st.line_chart(data.set_index("DATE")[["TOTAL_SLEEP_HOURS"]])
        with col2:
            st.write("Sleep Debt (7-Day Rolling)")
            st.line_chart(data.set_index("DATE")[["SLEEP_DEBT_7D"]])

        latest_sleep_debt = data["SLEEP_DEBT_7D"].iloc[-1]
        if latest_sleep_debt > 5:
            st.warning("High accumulated sleep debt. Recovery likely impacted.")
        elif latest_sleep_debt > 2:
            st.info("Moderate sleep debt detected.")
        else:
            st.success("Sleep debt is well managed.")

        # -----------------------------------
        # Workout Readiness
        # -----------------------------------
        st.subheader("Workout Readiness")

        latest_readiness = int(data["READINESS_SCORE"].iloc[-1])
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Today's Readiness Score", latest_readiness)
        with col2:
            st.line_chart(data.set_index("DATE")[["READINESS_SCORE"]])

        if latest_readiness > 75:
            st.success("High readiness: optimal for intense training.")
        elif latest_readiness > 50:
            st.info("Moderate readiness: balanced training recommended.")
        else:
            st.error("Low readiness: prioritize recovery or rest.")

        # -----------------------------------
        # HRV + Recovery
        # -----------------------------------
        st.subheader("Recovery & HRV")

        col1, col2 = st.columns(2)
        with col1:
            st.write("HRV Trend")
            st.line_chart(data.set_index("DATE")[["HRV"]])
        with col2:
            st.write("Recovery Score")
            st.line_chart(data.set_index("DATE")[["RECOVERY_SCORE"]])

        # -----------------------------------
        # HRV Anomaly Detection
        # -----------------------------------
        st.subheader("HRV Anomaly Detection")

        anomalies = data[data["HRV_ANOMALY_FLAG"] == 1]
        if not anomalies.empty:
            st.warning(f"{len(anomalies)} low HRV days detected")
            st.dataframe(anomalies[["DATE", "HRV", "HRV_7D_AVG", "HRV_7D_STD"]])
        else:
            st.success("No HRV anomalies detected")

        # -----------------------------------
        # Summary Insights
        # -----------------------------------
        st.subheader("Summary Insights")

        avg_steps = data["STEPS"].mean()
        avg_sleep = data["TOTAL_SLEEP_HOURS"].mean()
        avg_recovery = data["RECOVERY_SCORE"].mean()

        insights = []
        if avg_steps < 8000:
            insights.append("Increase daily activity levels.")
        if avg_sleep < 7:
            insights.append("Sleep duration is below optimal levels.")
        if avg_recovery < 50:
            insights.append("Recovery scores are low.")
        if latest_sleep_debt > 5:
            insights.append("High cumulative sleep debt detected.")
        if latest_readiness < 50:
            insights.append("Low readiness — consider recovery.")
        if len(anomalies) > 0:
            insights.append("HRV anomalies detected (possible stress/fatigue).")

        if insights:
            for i in insights:
                st.write(f"- {i}")
        else:
            st.success("All key health indicators are strong.")

    else:
        st.info("No data found for this user.")

else:
    st.info("Enter a User ID to view insights.")
