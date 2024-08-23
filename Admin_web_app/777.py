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
from google.api_core.exceptions import ResourceExhausted, RetryError
from collections import defaultdict
import matplotlib.dates as mdates

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
    'Mr.Arjun': ['2024-03-04', '2024-03-05'],
    'DevOps': ['2024-03-11', '2024-03-12', '2024-03-13', '2024-03-14', '2024-03-15', '2024-03-16', 
               '2024-06-04', '2024-06-05'],
    'DevMode': ['2024-02-22', '2024-02-23', '2024-02-24', '2024-02-25', '2024-02-26', '2024-02-28'],
    'debugging': ['2024-06-10', '2024-06-13', '2024-06-14'],
    'testing': ['2024-06-13']
}

# Generate dropdown options with collection names and original date format
dropdown_options = []
for collection, dates in collection_dates.items():
    if dates:
        dropdown_options.extend([f"{collection} - {date}" for date in dates])
    else:
        dropdown_options.append(f"{collection} - No Dates")

# Sort dropdown options by newest to oldest
dropdown_options = sorted(dropdown_options, key=lambda x: datetime.strptime(x.split(' - ')[1], '%Y-%m-%d') if 'No Dates' not in x else datetime.min, reverse=True)

# Multi-select dropdown
selected_options = st.multiselect('Select Collection(s) with Dates', dropdown_options)

# Process selected options to retrieve data and plot
if selected_options:
    selected_collections = {}
    total_healthy = 0
    total_infected = 0
    collection_scan_counts = {}
    device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

    for option in selected_options:
        collection, date_str = option.split(' - ')
        if date_str == "No Dates":
            date_str = None
        if collection not in selected_collections:
            selected_collections[collection] = []
        selected_collections[collection].append(date_str)

    # Fetch data and plot pie charts
    for collection, dates in selected_collections.items():
        if "No Dates" in dates or not dates[0]:
            docs = db.collection(collection).stream()
            st.write(f"**{collection} Collection (All Data)**")
        else:
            st.write(f"**{collection} Collection**")
            docs = []
            for date_str in dates:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                start_datetime = datetime.combine(date_obj, datetime.min.time())
                end_datetime = datetime.combine(date_obj, datetime.max.time())
                docs.extend(db.collection(collection)
                            .where('timestamp', '>=', start_datetime)
                            .where('timestamp', '<=', end_datetime)
                            .stream())

        # Process and analyze the retrieved documents
        healthy_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Healthy')
        infected_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Infected')
        total_scans = healthy_count + infected_count

        # Accumulate counts for combined and data share pie charts
        total_healthy += healthy_count
        total_infected += infected_count
        collection_scan_counts[collection] = total_scans

        # Collect device-specific data for line chart
        for doc in docs:
            data = doc.to_dict()
            device_name = data.get('DeviceName')
            if device_name:
                date_key = data.get('timestamp').date()
                if data.get('InfStat') == 'Healthy':
                    device_data[device_name][date_key]['Healthy'] += 1
                elif data.get('InfStat') == 'Infected':
                    device_data[device_name][date_key]['Infected'] += 1

        # Plot individual pie chart for the collection
        if total_scans > 0:
            fig, ax = plt.subplots(figsize=(3, 3))  # Small plot size
            ax.pie([healthy_count, infected_count], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
            ax.axis('equal')
            st.write(f"**{collection} - Healthy vs Infected**")
            st.pyplot(fig)

    # Create columns for layout
    col1, col2, col3 = st.columns(3)

    # Pie chart for combined data across all selected collections
    if total_healthy + total_infected > 0:
        with col1:
            fig, ax = plt.subplots(figsize=(3, 3))  # Small plot size
            ax.pie([total_healthy, total_infected], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
            ax.axis('equal')
            st.write("**Combined Healthy vs Infected Scans Across Selected Collections**")
            st.pyplot(fig)

    # Pie chart showing data share by each collection
    if collection_scan_counts:
        total_scans_all_collections = sum(collection_scan_counts.values())

        if total_scans_all_collections > 0:
            scan_shares = [count / total_scans_all_collections * 100 for count in collection_scan_counts.values()]
            with col2:
                fig, ax = plt.subplots(figsize=(3, 3))  # Small plot size
                ax.pie(scan_shares, labels=collection_scan_counts.keys(), autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                st.write("**Data Share by Each Collection**")
                st.pyplot(fig)

    # Bar chart showing collections with most infected scans
    if total_infected > 0:
        sorted_collections = sorted(collection_scan_counts.items(), key=lambda item: item[1], reverse=True)
        collections = [item[0] for item in sorted_collections]
        infected_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Infected') for collection in collections]

        with col3:
            fig, ax = plt.subplots(figsize=(3, 3))  # Small plot size
            ax.barh(collections, infected_counts, color='#FF0000')
            ax.set_xlabel('Number of Infected Scans')
            ax.set_ylabel('Collection')
            ax.set_title('Infected Scans by Collection (Most to Least)')
            st.write("**Infected Scans by Collection**")
            st.pyplot(fig)

    # Line chart for device scan counts over time
    device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

    for collection, dates in selected_collections.items():
        for date_str in dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = datetime.combine(date_obj, datetime.max.time())

            try:
                docs = db.collection(collection) \
                         .where('timestamp', '>=', start_datetime) \
                         .where('timestamp', '<=', end_datetime) \
                         .stream()
                for doc in docs:
                    try:
                        doc_data = doc.to_dict()
                        device_name = doc_data.get('DeviceName')
                        if not device_name:
                            continue  # Skip if DeviceName is missing

                        date_key = doc_data['timestamp'].date()
                        inf_stat = doc_data.get('InfStat', 'Unknown')

                        if inf_stat == 'Healthy':
                            device_data[device_name][date_key]['Healthy'] += 1
                        elif inf_stat == 'Infected':
                            device_data[device_name][date_key]['Infected'] += 1
                    except Exception as e:
                        st.warning(f"Skipping document due to error: {str(e)}")
                        continue
            except Exception as e:
                st.error(f"Error fetching data from collection {collection} for date {date_str}: {str(e)}")
                continue

    # Debugging output to ensure data is correct
    st.write("**Device Data for Line Chart**")
    st.write(device_data)

    # Line chart for device scan counts over time
    if device_data:
        fig, ax = plt.subplots(figsize=(10, 6))  # Larger plot size to accommodate multiple lines
        colors = plt.cm.get_cmap('tab10', len(device_data) * 2)

        for i, (device_name, dates) in enumerate(device_data.items()):
            date_list = sorted(dates.keys())
            healthy_scans = [dates[date]['Healthy'] for date in date_list]
            infected_scans = [dates[date]['Infected'] for date in date_list]

            if any(healthy_scans):
                ax.plot(date_list, healthy_scans, label=f"{device_name} - Healthy", color=colors(i * 2))
            if any(infected_scans):
                ax.plot(date_list, infected_scans, label=f"{device_name} - Infected", color=colors(i * 2 + 1))

        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Scans')
        ax.set_title('Device Scan Counts Over Time')
        ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()

        st.write("**Device Scan Counts Over Time**")
        st.pyplot(fig)
    else:
        st.write("No device data available for the selected collections.")
