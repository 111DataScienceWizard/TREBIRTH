import streamlit as st
from google.cloud import firestore
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title('Farm Analytics')

# Initialize Firestore client
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Collection selection dropdown
collections = ['testing', 'TechDemo', 'Plot1', 'Mr.Arjun', 'M1V6_SS_Testing', 'M1V6_GoldStandard', 'DevOps', 'DevMode', 'debugging']
selected_collections = st.multiselect('Select Collection(s)', collections, default=['testing'])

# Get all timestamps from selected collections
timestamps = []
for collection in selected_collections:
    docs = db.collection(collection).stream()
    for doc in docs:
        data = doc.to_dict()
        timestamps.append(data['timestamp'])

# Remove time components and duplicates, then sort by date
timestamps = sorted(list(set([ts.date() for ts in timestamps])))

# Check if there are multiple dates available
if len(timestamps) > 1:
    # Create a date range slider for multiple dates
    min_date, max_date = min(timestamps), max(timestamps)
    selected_date_range = st.slider('Select Date Range', min_value=min_date, max_value=max_date, value=(min_date, max_date), format="YYYY MMM DD")
else:
    # Only one date available, so use a single-pointer slider
    st.write("Only one date available:")
    selected_date_range = st.slider('Select Date', min_value=timestamps[0], max_value=timestamps[0], value=timestamps[0], format="YYYY MMM DD")

# Filter data by selected date range
filtered_data = []
for collection in selected_collections:
    docs = db.collection(collection).where('timestamp', '>=', datetime.combine(selected_date_range[0], datetime.min.time())).where('timestamp', '<=', datetime.combine(selected_date_range[1], datetime.max.time())).stream()
    for doc in docs:
        filtered_data.append(doc.to_dict())

# Analyze and plot data
if filtered_data:
    # Aggregate data for pie charts
    for collection in selected_collections:
        healthy_count = sum(1 for d in filtered_data if d['InfStat'] == 'Healthy' and d['Collection'] == collection)
        infected_count = sum(1 for d in filtered_data if d['InfStat'] == 'Infected' and d['Collection'] == collection)
        total_scans = healthy_count + infected_count

        # Plot pie chart for the collection
        fig, ax = plt.subplots()
        ax.pie([healthy_count, infected_count], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
        ax.axis('equal')
        st.pyplot(fig)

        # Display stats
        st.write(f"**{collection} Collection Stats:**")
        st.write(f"Total Scans: {total_scans}")
        st.write(f"Infected Scans: {infected_count}")
        st.write(f"Healthy Scans: {healthy_count}")

    # Combined pie chart for all selected collections
    combined_healthy = sum(1 for d in filtered_data if d['InfStat'] == 'Healthy')
    combined_infected = sum(1 for d in filtered_data if d['InfStat'] == 'Infected')

    fig, ax = plt.subplots()
    ax.pie([combined_healthy, combined_infected], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
    ax.axis('equal')
    st.pyplot(fig)

    # Display combined stats
    st.write(f"**Combined Collection Stats:**")
    st.write(f"Total Scans: {len(filtered_data)}")
    st.write(f"Infected Scans: {combined_infected}")
    st.write(f"Healthy Scans: {combined_healthy}")
else:
    st.write("No data found for the selected date range.")
