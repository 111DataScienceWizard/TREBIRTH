import streamlit as st
from google.cloud import firestore
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title('Farm Analytics')

# Firestore client setup
db = firestore.Client.from_service_account_json("path_to_your_service_account_json.json")

# Dropdown for selecting collections
collections = ['testing', 'TechDemo', 'Plot1', 'Mr.Arjun', 'M1V6_SS_Testing', 'M1V6_GoldStandard', 'DevOps', 'DevMode', 'debugging']
selected_collections = st.multiselect('Select Collections', collections)

# Fetch metadata from the selected collections
timestamps = []
for collection in selected_collections:
    docs = db.collection(collection).stream()
    for doc in docs:
        data = doc.to_dict()
        if 'timestamp' in data:
            timestamps.append(data['timestamp'].date())

# Extract unique dates and sort them
unique_dates = sorted(set(timestamps))

# If there are multiple dates, create a date range slider
if len(unique_dates) > 1:
    selected_date_range = st.slider('Select Date Range', min_value=unique_dates[0], max_value=unique_dates[-1], value=(unique_dates[0], unique_dates[-1]), format="YYYY MMM DD")
else:
    st.write("Only one date available.")
    selected_date_range = st.slider('Select Date', min_value=unique_dates[0], max_value=unique_dates[0], value=unique_dates[0], format="YYYY MMM DD")

# Filter data based on the selected date range
filtered_data = []
for collection in selected_collections:
    docs = db.collection(collection).where('timestamp', '>=', datetime.combine(selected_date_range[0], datetime.min.time())).where('timestamp', '<=', datetime.combine(selected_date_range[1], datetime.max.time())).stream()
    for doc in docs:
        filtered_data.append(doc.to_dict())

# Prepare data for pie charts
inf_status_data = {'Healthy': 0, 'Infected': 0}
collection_data = {}
for doc in filtered_data:
    inf_status = doc.get('InfStat')
    inf_status_data[inf_status] += 1
    collection_name = doc.get('collection')
    if collection_name not in collection_data:
        collection_data[collection_name] = {'Healthy': 0, 'Infected': 0}
    collection_data[collection_name][inf_status] += 1

# Plot pie charts for each selected collection
for collection, data in collection_data.items():
    st.write(f"Collection: {collection}")
    st.write(f"Total Scans: {sum(data.values())}")
    st.write(f"Infected Scans: {data['Infected']}")
    st.write(f"Healthy Scans: {data['Healthy']}")
    st.pyplot(plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', startangle=140))
    plt.axis('equal')

# Plot pie chart for combined data
st.write("Combined Data")
st.write(f"Total Scans: {sum(inf_status_data.values())}")
st.write(f"Infected Scans: {inf_status_data['Infected']}")
st.write(f"Healthy Scans: {inf_status_data['Healthy']}")
st.pyplot(plt.pie(inf_status_data.values(), labels=inf_status_data.keys(), autopct='%1.1f%%', startangle=140))
plt.axis('equal')
