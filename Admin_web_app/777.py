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

        # Plot pie chart
        if total_scans > 0:
            fig, ax = plt.subplots()
            ax.pie([healthy_count, infected_count], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
            ax.axis('equal')
            st.pyplot(fig)

            # Display stats
            st.write(f"Total Scans: {total_scans}")
            st.write(f"Infected Scans: {infected_count}")
            st.write(f"Healthy Scans: {healthy_count}")
        else:
            st.write(f"No data available for the selected date(s) in {collection}.")
else:
    st.write("No collections or dates selected.")
