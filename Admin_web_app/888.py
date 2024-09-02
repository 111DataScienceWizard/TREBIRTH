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

# Initialize Firestore client
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

st.set_page_config(layout="wide")
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

# Create the main layout
st.markdown('<h1 style="text-align: center;">Farm Analytics</h1>', unsafe_allow_html=True)
selected_options = st.multiselect('Select Collection(s) with Dates', dropdown_options)

# Initialize storage for analytics
selected_collections = {}
total_healthy = 0
total_infected = 0
collection_scan_counts = {}
device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

if selected_options:
    for option in selected_options:
        collection, date_str = option.split(' - ')
        if date_str == "No Dates":
            date_str = None
        if collection not in selected_collections:
            selected_collections[collection] = []
        selected_collections[collection].append(date_str)

    # Fetch data and analyze
    for collection, dates in selected_collections.items():
        if "No Dates" in dates or not dates[0]:
            docs = db.collection(collection).stream()
        else:
            docs = []
            for date_str in dates:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                start_datetime = datetime.combine(date_obj, datetime.min.time())
                end_datetime = datetime.combine(date_obj, datetime.max.time())
                docs.extend(db.collection(collection)
                            .where('timestamp', '>=', start_datetime)
                            .where('timestamp', '<=', end_datetime)
                            .stream())

        healthy_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Healthy')
        infected_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Infected')
        total_scans = healthy_count + infected_count

        # Accumulate counts for charts
        total_healthy += healthy_count
        total_infected += infected_count
        collection_scan_counts[collection] = total_scans

    # Plot combined healthy vs infected scans
    if total_healthy + total_infected > 0:
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.pie([total_healthy, total_infected], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
        ax.axis('equal')
        st.write("**Combined Healthy vs Infected Scans Across Selected Collections**")
        st.pyplot(fig)

    # Pie chart showing data share by each collection
    if collection_scan_counts:
        total_scans_all_collections = sum(collection_scan_counts.values())
        if total_scans_all_collections > 0:
            scan_shares = [count / total_scans_all_collections * 100 for count in collection_scan_counts.values()]
            fig, ax = plt.subplots(figsize=(2, 2))
            ax.pie(scan_shares, labels=collection_scan_counts.keys(), autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.write("**Data Share by Each Collection**")
            st.pyplot(fig)

    # Bar chart showing collections with most infected scans
    if total_infected > 0:
        sorted_collections = sorted(collection_scan_counts.items(), key=lambda item: item[1], reverse=True)
        collections = [item[0] for item in sorted_collections]
        infected_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Infected') for collection in collections]

        fig, ax = plt.subplots(figsize=(2, 2))
        ax.barh(collections, infected_counts, color='#FF0000')
        ax.set_xlabel('Number of Infected Scans')
        ax.set_ylabel('Collection')
        ax.set_title('Infected Scans by Collection (Most to Least)')
        st.write("**Infected Scans by Collection**")
        st.pyplot(fig)

    # Vertical bar chart for device scan counts
    device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

    for collection, dates in selected_collections.items():
        for date_str in dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = datetime.combine(date_obj, datetime.max.time())

            docs = db.collection(collection) \
                     .where('timestamp', '>=', start_datetime) \
                     .where('timestamp', '<=', end_datetime) \
                     .stream()
            for doc in docs:
                doc_data = doc.to_dict()
                device_name = doc_data.get('DeviceName:')
                if not device_name:
                    continue

                date_key = doc_data['timestamp'].date().strftime('%Y-%m-%d')
                inf_stat = doc_data.get('InfStat', 'Unknown')

                if inf_stat == 'Healthy':
                    device_data[device_name][date_key]['Healthy'] += 1
                elif inf_stat == 'Infected':
                    device_data[device_name][date_key]['Infected'] += 1

    if device_data:
        fig, ax = plt.subplots(figsize=(6, 4))
        width = 2
        colors = plt.cm.get_cmap('tab10', len(device_data) * 2)
        bars = []
        legend_labels = []

        for i, (device_name, dates) in enumerate(device_data.items()):
            date_list = sorted(dates.keys())
            healthy_scans = [dates[date]['Healthy'] for date in date_list]
            infected_scans = [dates[date]['Infected'] for date in date_list]

            bars1 = ax.bar([datetime.strptime(date, '%Y-%m-%d') for date in date_list], healthy_scans, width=width, 
                           label=f"{device_name} - Healthy", color=colors(i * 2))
            bars2 = ax.bar([datetime.strptime(date, '%Y-%m-%d') for date in date_list], infected_scans, width=width, 
                           bottom=healthy_scans, label=f"{device_name} - Infected", color=colors(i * 2 + 1))

            bars.append(bars1)
            bars.append(bars2)
            legend_labels.append(f"{device_name} - Healthy")
            legend_labels.append(f"{device_name} - Infected")

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Scans')
        ax.set_title('Device Scan Counts Over Time')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., labels=legend_labels)

        st.write("**Device Scan Counts Over Time**")
        st.pyplot(fig)

    # Display individual collection plots
    if selected_options:
        for i, (collection, dates) in enumerate(selected_collections.items()):
            if "No Dates" in dates or not dates[0]:
                docs = db.collection(collection).stream()
            else:
                docs = []
                for date_str in dates:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    start_datetime = datetime.combine(date_obj, datetime.min.time())
                    end_datetime = datetime.combine(date_obj, datetime.max.time())
                    docs.extend(db.collection(collection)
                                .where('timestamp', '>=', start_datetime)
                                .where('timestamp', '<=', end_datetime)
                                .stream())

            healthy_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Healthy')
            infected_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Infected')
            total_scans = healthy_count + infected_count
            farmer_image = farmer_images.get(collection, 'default_image.png')

            # Individual Pie Chart
            fig, ax = plt.subplots(figsize=(2, 2))
            ax.pie([healthy_count, infected_count], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
            ax.axis('equal')

            # Individual Bar Chart
            dates = sorted(device_data.keys())
            healthy_scans = [device_data[date]['Healthy'] for date in dates]
            infected_scans = [device_data[date]['Infected'] for date in dates]
            
            fig_bar, ax_bar = plt.subplots(figsize=(3, 2))
            x = range(len(dates))
            ax_bar.bar(x, healthy_scans, width=0.4, label='Healthy', color='g', align='center')
            ax_bar.bar(x, infected_scans, width=0.4, label='Infected', color='r', align='edge')
            ax_bar.set_xticks(x)
            ax_bar.set_xticklabels(dates)
            ax_bar.set_xlabel('Date')
            ax_bar.set_ylabel('Number of Scans')
            ax_bar.set_title(f'{collection} Scans by Date')

            # Layout in rectangular box
            st.write(f"**{collection}**")
            col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
            with col1:
                st.image(farmer_image, caption=f'Farmer {collection}')
            with col2:
                st.write(f"Total Scans: {total_scans}")
                st.write(f"Healthy Scans: {healthy_count}")
                st.write(f"Infected Scans: {infected_count}")
            with col3:
                st.pyplot(fig)
            with col4:
                st.pyplot(fig_bar)

    else:
        st.write("**Please select a collection from the dropdown menu to view data.**")
