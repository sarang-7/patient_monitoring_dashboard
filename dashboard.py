import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# DB connection
def get_connection():
    return sqlite3.connect("patient_monitoring.db", check_same_thread=False)

def get_data():
    conn = get_connection()
    query = """
        SELECT patient_id, name, heart_rate, blood_pressure, oxygen_level, temperature, timestamp
        FROM patient_vitals
        ORDER BY timestamp DESC
        LIMIT 200
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Check alerts
def check_alerts(df):
    def check(row):
        if row['heart_rate'] < 60 or row['heart_rate'] > 100:
            return "⚠ Need Attention"
        if row['oxygen_level'] < 95:
            return "⚠ Need Attention"
        if row['temperature'] < 36.5 or row['temperature'] > 37.5:
            return "⚠ Need Attention"
        return "✅ Normal"
    df["Alert"] = df.apply(check, axis=1)
    return df

# Highlight abnormal values
def highlight_abnormal(val, col):
    if col == "heart_rate" and (val < 60 or val > 100):
        return "background-color: #ffdddd"
    if col == "oxygen_level" and val < 95:
        return "background-color: #ffdddd"
    if col == "temperature" and (val < 36.5 or val > 37.5):
        return "background-color: #ffdddd"
    return ""

# Streamlit app
st.set_page_config(page_title="🏥 Patient Monitoring Dashboard", layout="wide")
st.title("🏥 Real-Time Patient Monitoring")

# Auto-refresh every 5 sec
st_autorefresh(interval=5000, key="refresh")

df = get_data()
df = check_alerts(df)

# Show latest vitals (one row per patient)
latest = df.groupby("name").first().reset_index()
styled_table = latest.style.applymap(
    lambda v: highlight_abnormal(v, "heart_rate"), subset=["heart_rate"]
).applymap(
    lambda v: highlight_abnormal(v, "oxygen_level"), subset=["oxygen_level"]
).applymap(
    lambda v: highlight_abnormal(v, "temperature"), subset=["temperature"]
)

st.subheader("📋 Latest Vitals")
st.dataframe(styled_table, use_container_width=True)

# Patient trend charts
st.subheader("📊 Patient Trends")

patients = df["name"].unique()

# Use session_state to remember last choice
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = patients[0]  # default

selected = st.selectbox(
    "Select Patient",
    patients,
    index=list(patients).index(st.session_state.selected_patient) if st.session_state.selected_patient in patients else 0,
    key="patient_dropdown"
)

# Save selection
st.session_state.selected_patient = selected

# Filter data
patient_data = df[df["name"] == selected].sort_values("timestamp")

col1, col2, col3 = st.columns(3)
with col1:
    st.plotly_chart(px.line(patient_data, x="timestamp", y="heart_rate", title="❤️ Heart Rate"), use_container_width=True)
with col2:
    st.plotly_chart(px.line(patient_data, x="timestamp", y="oxygen_level", title="🫁 Oxygen Level"), use_container_width=True)
with col3:
    st.plotly_chart(px.line(patient_data, x="timestamp", y="temperature", title="🌡 Temperature"), use_container_width=True)
