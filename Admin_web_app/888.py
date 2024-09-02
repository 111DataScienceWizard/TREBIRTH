import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
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




import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
import json
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

st.set_page_config(layout="wide")

# Set the background of the entire app
st.markdown("""
    <style>
    .main {
        background-color: black;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title('Farm Analytics')

# Mapping collections to farmer images
farmer_images = {
    'TechDemo': 'Admin_web_app/F1.png',
    'Mr.Arjun': 'Admin_web_app/F2.png',
    'DevOps': 'Admin_web_app/F6.png',
    'DevMode': 'Admin_web_app/F4.png',
    'debugging': 'Admin_web_app/F5.png',
    'testing': 'Admin_web_app/F3.png'
}

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

# Centered layout for dropdown
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
selected_options = st.multiselect('Select Collection(s) with Dates', dropdown_options)
st.markdown("</div>", unsafe_allow_html=True)

if selected_options:
    selected_collections = {}
    total_healthy = 0
    total_infected = 0
    collection_scan_counts = {}

    # Fetch data and plot pie charts
    for option in selected_options:
        collection, date_str = option.split(' - ')
        if date_str == "No Dates":
            date_str = None
        if collection not in selected_collections:
            selected_collections[collection] = []
        selected_collections[collection].append(date_str)

        docs = []
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = datetime.combine(date_obj, datetime.max.time())
            docs = db.collection(collection) \
                     .where('timestamp', '>=', start_datetime) \
                     .where('timestamp', '<=', end_datetime) \
                     .stream()

        healthy_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Healthy')
        infected_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Infected')
        total_scans = healthy_count + infected_count

        total_healthy += healthy_count
        total_infected += infected_count
        collection_scan_counts[collection] = total_scans

    # First row with two pie charts and a horizontal bar chart
    row1_col1, row1_col2, row1_col3 = st.columns([1, 1, 2])

    with row1_col1:
        if total_healthy + total_infected > 0:
            fig, ax = plt.subplots(figsize=(3, 3))
            ax.pie([total_healthy, total_infected], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
            ax.axis('equal')
            st.write("**Combined Healthy vs Infected Scans Across Selected Collections**")
            st.pyplot(fig)

    with row1_col2:
        if collection_scan_counts:
            total_scans_all_collections = sum(collection_scan_counts.values())
            if total_scans_all_collections > 0:
                scan_shares = [count / total_scans_all_collections * 100 for count in collection_scan_counts.values()]
                fig, ax = plt.subplots(figsize=(3, 3))
                ax.pie(scan_shares, labels=collection_scan_counts.keys(), autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                st.write("**Data Share by Each Collection**")
                st.pyplot(fig)

    with row1_col3:
        if total_infected > 0:
            sorted_collections = sorted(collection_scan_counts.items(), key=lambda item: item[1], reverse=True)
            collections = [item[0] for item in sorted_collections]
            infected_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Infected') for collection in collections]

            fig, ax = plt.subplots(figsize=(5, 3))
            ax.barh(collections, infected_counts, color='#FF0000')
            ax.set_xlabel('Number of Infected Scans')
            ax.set_ylabel('Collection')
            ax.set_title('Infected Scans by Collection (Most to Least)')
            st.write("**Infected Scans by Collection**")
            st.pyplot(fig)

    # Second row with comments box and vertical bar chart
    row2_col1, row2_col2 = st.columns([1, 3])

    with row2_col1:
        most_active_device = "Sloth's Katana"
        total_infected_trees = 456

        st.markdown(f"""
            <div style="
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 10px;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                font-family: 'Arial', sans-serif;
                color: #333333;
                width: 100%;  
                margin-top: 20px;
            ">
               <h4 style="color: #007ACC; margin-bottom: 10px;">Comments</h4>
                <hr style="border: none; height: 1px; background-color: #007ACC; margin-bottom: 10px;">
                <p style="font-size: 14px; margin: 5px 0;">
                    <strong>Most Active Device:</strong> {most_active_device}
                </p>
                <p style="font-size: 14px; margin: 5px 0;">
                    <strong>Total Infected Trees Detected by Team TREBIRTH:</strong> {total_infected_trees}
                </p>
            </div>
        """, unsafe_allow_html=True)

    with row2_col2:
        # Vertical bar chart for device scan counts over time
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
                        doc_data = doc.to_dict()
                        device_name = doc_data.get('DeviceName:')
                        if not device_name:
                            continue  # Skip if DeviceName is missing

                        date_key = doc_data['timestamp'].date().strftime('%Y-%m-%d')
                        inf_stat = doc_data.get('InfStat', 'Unknown')

                        if inf_stat == 'Healthy':
                            device_data[device_name][date_key]['Healthy'] += 1
                        elif inf_stat == 'Infected':
                            device_data[device_name][date_key]['Infected'] += 1
                except Exception as e:
                    st.error(f"Error fetching data from collection {collection} for date {date_str}: {str(e)}")

        if device_data:
            fig, ax = plt.subplots(figsize=(6, 4))
            width = 2

            colors = plt.cm.get_cmap('tab10', len(device_data) * 2)
            bars = []
            legend_labels = []

            for i, (device_name, dates) in enumerate(device_data.items()):
                date_keys = sorted(dates.keys())
                healthy_counts = [dates[date_key]['Healthy'] for date_key in date_keys]
                infected_counts = [dates[date_key]['Infected'] for date_key in date_keys]

                # Plot Healthy and Infected counts for each device
                bars.append(ax.bar(date_keys, healthy_counts, width=width, label=f'{device_name} - Healthy', color=colors(i * 2)))
                bars.append(ax.bar(date_keys, infected_counts, width=width, label=f'{device_name} - Infected', color=colors(i * 2 + 1), bottom=healthy_counts))

                legend_labels.extend([f'{device_name} - Healthy', f'{device_name} - Infected'])

        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Scans')
        ax.set_title('Device Scan Counts Over Time')
        ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1), labels=legend_labels)
        st.write("**Device Scan Counts Over Time**")
        st.pyplot(fig)

    # Third row with individual pie charts and bar charts
    st.write("### Individual Collection Analysis")
    for collection, dates in selected_collections.items():
        for date_str in dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d') if date_str else None
            if date_obj:
                start_datetime = datetime.combine(date_obj, datetime.min.time())
                end_datetime = datetime.combine(date_obj, datetime.max.time())
                docs = db.collection(collection) \
                         .where('timestamp', '>=', start_datetime) \
                         .where('timestamp', '<=', end_datetime) \
                         .stream()
            else:
                docs = db.collection(collection).stream()

            healthy_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Healthy')
            infected_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Infected')
            total_scans = healthy_count + infected_count

            row3_col1, row3_col2 = st.columns([1, 2])

            with row3_col1:
                farmer_image = farmer_images.get(collection, 'default.png')
                st.image(farmer_image, width=100)

                st.write(f"**Collection: {collection}**")
                st.write(f"Total Scans: {total_scans}")
                st.write(f"Healthy Scans: {healthy_count}")
                st.write(f"Infected Scans: {infected_count}")

            with row3_col2:
                fig, ax = plt.subplots(figsize=(3, 3))
                ax.pie([healthy_count, infected_count], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
                ax.axis('equal')
                st.pyplot(fig)

                device_scan_counts = defaultdict(lambda: {'Healthy': 0, 'Infected': 0})
                for doc in docs:
                    doc_data = doc.to_dict()
                    device_name = doc_data.get('DeviceName:')
                    if not device_name:
                        continue  # Skip if DeviceName is missing

                    inf_stat = doc_data.get('InfStat', 'Unknown')
                    if inf_stat == 'Healthy':
                        device_scan_counts[device_name]['Healthy'] += 1
                    elif inf_stat == 'Infected':
                        device_scan_counts[device_name]['Infected'] += 1

                if device_scan_counts:
                    fig, ax = plt.subplots(figsize=(4, 3))
                    device_names = list(device_scan_counts.keys())
                    healthy_counts = [device_scan_counts[device_name]['Healthy'] for device_name in device_names]
                    infected_counts = [device_scan_counts[device_name]['Infected'] for device_name in device_names]

                    ax.bar(device_names, healthy_counts, label='Healthy', color='#00FF00')
                    ax.bar(device_names, infected_counts, label='Infected', color='#FF0000', bottom=healthy_counts)
                    ax.set_xlabel('Device Name')
                    ax.set_ylabel('Number of Scans')
                    ax.set_title(f'Scans by Device for {collection}')
                    ax.legend()
                    st.pyplot(fig)
