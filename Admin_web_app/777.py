import streamlit as st
from google.cloud import firestore
from datetime import datetime
import matplotlib.pyplot as plt

# Initialize Firestore
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Set page configuration
st.set_page_config(layout="wide")
st.title('Farm Analytics')

# Collection dropdown
collections = ['testing', 'TechDemo', 'Plot1', 'Mr.Arjun', 'M1V6_SS_Testing', 'M1V6_GoldStandard', 
               'DevOps', 'DevMode', 'debugging']
selected_collections = st.multiselect('Select Collections', collections, default=['testing', 'debugging'])

# Retrieve unique dates from all collections
all_dates = set()

for collection in collections:
    docs = db.collection(collection).stream()
    for doc in docs:
        timestamp = doc.to_dict().get('timestamp')
        if timestamp:
            all_dates.add(timestamp.date())

# Convert set to sorted list
all_dates = sorted(list(all_dates))

# Dropdown for unique dates
selected_dates = st.multiselect('Select Dates', all_dates, default=[])

# Filter data based on selected collections and dates
filtered_data = []

for collection in selected_collections:
    docs = db.collection(collection).stream()
    for doc in docs:
        data = doc.to_dict()
        timestamp = data.get('timestamp')
        if timestamp and (timestamp.date() in selected_dates or not selected_dates):
            filtered_data.append(data)

# Process and display data
if filtered_data:
    healthy_count = sum(1 for data in filtered_data if data['InfStat'] == 'Healthy')
    infected_count = sum(1 for data in filtered_data if data['InfStat'] == 'Infected')
    total_count = len(filtered_data)
    
    st.write(f"Total Scans: {total_count}")
    st.write(f"Healthy Scans: {healthy_count}")
    st.write(f"Infected Scans: {infected_count}")

    # Plot pie chart
    labels = ['Healthy', 'Infected']
    sizes = [healthy_count, infected_count]
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)
    
else:
    st.write("No data found for the selected criteria.")
