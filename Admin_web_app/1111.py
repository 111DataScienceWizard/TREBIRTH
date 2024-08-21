import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import time
import zipfile
import os
import random
import matplotlib.dates as mdates
from google.api_core.exceptions import ResourceExhausted, RetryError
from collections import defaultdict

def exponential_backoff(retries):
    base_delay = 1
    max_delay = 60
    delay = base_delay * (2 ** retries) + random.uniform(0, 1)
    return min(delay, max_delay)

def get_firestore_data(query):
    retries = 0
    max_retries = 10
    while retries < max_retries:
        try:
            results = query.stream()
            return list(results)
        except ResourceExhausted as e:
            st.warning(f"Quota exceeded, retrying... (attempt {retries + 1})")
            time.sleep(exponential_backoff(retries))
            retries += 1
        except RetryError as e:
            st.warning(f"Retry error: {e}, retrying... (attempt {retries + 1})")
            time.sleep(exponential_backoff(retries))
            retries += 1
        except Exception as e:
            st.error(f"An error occurred: {e}")
            break
    raise Exception("Max retries exceeded")

# Initialize Firestore client
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

st.set_page_config(layout="wide")
st.title('Farm Analytics')

# Collection dates mapping (using original date format)
collection_dates = {
    'TechDemo': ['2024-02-28', '2024-02-29'],
    'Plot1': [],  # No dates
    'M1V6_SS_Testing': ['2024-06-08', '2024-06-10', '2024-06-11', '2024-06-12', '2024-06-13', '2024-06-14', 
                        '2024-06-15', '2024-06-18', '2024-06-19', '2024-06-20', '2024-06-21'],
    'Mr.Arjun': ['2024-03-04', '2024-03-05'],
    'M1V6_GoldStandad': ['2024-06-25', '2024-06-26', '2024-06-28', '2024-06-29', '2024-07-01', '2024-07-03', 
                         '2024-07-06', '2024-07-08'],
    'DevOps': ['2024-03-11', '2024-03-12', '2024-03-13', '2024-03-14', '2024-03-15', '2024-03-16', 
               '2024-06-04', '2024-06-05'],
    'DevMode': ['2024-02-22', '2024-02-23', '2024-02-24', '2024-02-25', '2024-02-26', '2024-02-28'],
    'debugging': ['2024-06-10', '2024-06-13', '2024-06-14']
}

# Generate dropdown options with collection names only
dropdown_options = sorted(collection_dates.keys())

# Multi-select dropdown for collection names
#selected_collections = st.multiselect('Select Collection(s)', dropdown_options)
selected_collections = st.multiselect('Select Collection(s)', dropdown_options, default=['TechDemo', 'debugging'])

# Process selected options to retrieve data and plot
if selected_collections:
    total_healthy = 0
    total_infected = 0
    collection_scan_counts = {}
    device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

    # Fetch data and plot pie charts
    for collection in selected_collections:
        st.write(f"**{collection} Collection**")

        # Print unique dates of the selected collection
        unique_dates = collection_dates.get(collection, [])
        if unique_dates:
            st.write(f"Unique Dates: {', '.join(unique_dates)}")
        else:
            st.write("No dates available for this collection.")

        # Retrieve all data for the selected collection
        docs = db.collection(collection).stream()

        # Process and analyze the retrieved documents
        healthy_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Healthy')
        infected_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Infected')
        total_scans = healthy_count + infected_count

        total_healthy += healthy_count
        total_infected += infected_count
        collection_scan_counts[collection] = total_scans

        # Process data for line chart
        for doc in docs:
            data = doc.to_dict()
            device_name = data['DeviceName']
            timestamp = data['timestamp']
            inf_stat = data['InfStat']

            # Aggregate data by device and date
            date_only = timestamp.date()
            device_data[device_name][date_only][inf_stat] += 1

    # Plot line chart for device scan counts
    if device_data:
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = plt.cm.get_cmap('tab10', len(device_data) * 2)

        for i, (device, dates) in enumerate(device_data.items()):
            date_list = sorted(dates.keys())
            healthy_scans = [dates[date]['Healthy'] for date in date_list]
            infected_scans = [dates[date]['Infected'] for date in date_list]

            ax.plot(date_list, healthy_scans, label=f"{device} - Healthy", color=colors(i * 2))
            ax.plot(date_list, infected_scans, label=f"{device} - Infected", color=colors(i * 2 + 1))

        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Scans')
        ax.set_title('Device Scan Counts Over Time')
        ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()

        st.write("**Device Scan Counts Over Time**")
        st.pyplot(fig)

    # Pie chart showing data shared by each plot
    if collection_scan_counts:
        total_scans_all_collections = sum(collection_scan_counts.values())

        if total_scans_all_collections > 0:
            scan_shares = [count / total_scans_all_collections * 100 for count in collection_scan_counts.values()]
            fig, ax = plt.subplots()
            ax.pie(scan_shares, labels=collection_scan_counts.keys(), autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.write("**Data Shared by Each Plot**")
            st.pyplot(fig)
        else:
            st.write("No scan data available to display.")
       

    # Pie chart for the overall distribution of healthy and infected scans
    if total_healthy + total_infected > 0:
        labels = ['Healthy', 'Infected']
        sizes = [total_healthy, total_infected]
        colors = ['#00FF00', '#FF0000']

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.write("**Overall Healthy vs Infected Scans**")
        st.pyplot(fig)

    # Bar chart showing collections with most infected scans
    if total_infected > 0:
        sorted_collections = sorted(collection_scan_counts.items(), key=lambda item: item[1], reverse=True)
        collections = [item[0] for item in sorted_collections]
        infected_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Infected') for collection in collections]

        fig, ax = plt.subplots()
        ax.barh(collections, infected_counts, color='#FF0000')
        ax.set_xlabel('Number of Infected Scans')
        ax.set_ylabel('Collection')
        ax.set_title('Infected Scans by Collection (Most to Least)')
        st.write("**Infected Scans by Collection**")
        st.pyplot(fig)
else:
    st.write("No collections selected.")
