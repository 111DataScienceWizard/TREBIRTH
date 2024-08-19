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


ef exponential_backoff(retries):
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

# Initialize Firestore
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Set page configuration
st.set_page_config(layout="wide")
st.title('Farm Analytics')

# Collection dropdown
collections = ['testing', 'TechDemo', 'Plot1', 'Mr.Arjun', 'M1V6_SS_Testing', 'M1V6_GoldStandard', 
               'DevOps', 'DevMode', 'debugging']
selected_collections = st.multiselect('Select Collections', collections, default=['testing', 'debugging'])

# Retrieve unique dates from all collections in batches to avoid timeout
def get_unique_dates(collection):
    unique_dates = set()
    try:
        docs = db.collection(collection).stream()
        for doc in docs:
            timestamp = doc.to_dict().get('timestamp')
            if timestamp:
                unique_dates.add(timestamp.date())
    except Exception as e:
        st.error(f"Error fetching data from collection {collection}: {e}")
    return unique_dates

all_dates = set()
for collection in collections:
    all_dates.update(get_unique_dates(collection))

# Convert set to sorted list
all_dates = sorted(list(all_dates))

# Dropdown for unique dates
selected_dates = st.multiselect('Select Dates', all_dates, default=[])

# Filter data based on selected collections and dates
filtered_data = []

def filter_data(collection, selected_dates):
    try:
        docs = db.collection(collection).stream()
        for doc in docs:
            data = doc.to_dict()
            timestamp = data.get('timestamp')
            if timestamp and (timestamp.date() in selected_dates or not selected_dates):
                filtered_data.append(data)
    except Exception as e:
        st.error(f"Error fetching data from collection {collection}: {e}")

for collection in selected_collections:
    filter_data(collection, selected_dates)

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
