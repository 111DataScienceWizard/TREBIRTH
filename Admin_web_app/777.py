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

# Initialize Firestore
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Set page configuration
st.set_page_config(layout="wide")
st.title('Farm Analytics')

# Collection names
collections = ['testing', 'TechDemo', 'Plot1', 'Mr.Arjun', 'M1V6_SS_Testing', 'M1V6_GoldStandard', 
               'DevOps', 'DevMode', 'debugging']

# Retrieve unique dates from all collections and organize them
def get_dates_grouped_by_month_year(collection):
    dates_by_month_year = defaultdict(list)
    try:
        docs = db.collection(collection).stream()
        for doc in docs:
            timestamp = doc.to_dict().get('timestamp')
            if timestamp:
                date = timestamp.date()
                month_year = date.strftime('%b %Y')  # e.g., 'Jul 2024'
                dates_by_month_year[month_year].append(date.day)
    except Exception as e:
        st.error(f"Error fetching data from collection {collection}: {e}")
    return dates_by_month_year

# Organize collections and dates
collections_with_dates = {}

for collection in collections:
    dates_by_month_year = get_dates_grouped_by_month_year(collection)
    if dates_by_month_year:
        # Create the display string
        date_str_list = []
        for month_year in sorted(dates_by_month_year.keys(), reverse=True, key=lambda x: datetime.strptime(x, '%b %Y')):
            days = sorted(dates_by_month_year[month_year], reverse=True)
            day_str = ','.join(map(str, days))
            date_str_list.append(f"({day_str}) {month_year}")
        collection_display_str = f"{collection} - {', '.join(date_str_list)}"
        collections_with_dates[collection_display_str] = collection

# Sort collections by the newest date first
sorted_collections = sorted(collections_with_dates.keys(), reverse=True)

# Dropdown for collection with dates
selected_collection_display = st.selectbox('Select Collection with Dates', sorted_collections)

# Extract the selected collection name
selected_collection = collections_with_dates[selected_collection_display]

# Retrieve the selected dates
selected_dates = get_dates_grouped_by_month_year(selected_collection)

# Convert the selected dates to a set of datetime.date objects
selected_dates_set = set()
for month_year, days in selected_dates.items():
    for day in days:
        date = datetime.strptime(f"{day} {month_year}", "%d %b %Y").date()
        selected_dates_set.add(date)

# Filter data based on the selected collection and dates
filtered_data = []

def filter_data(collection, selected_dates_set):
    try:
        docs = db.collection(collection).stream()
        for doc in docs:
            data = doc.to_dict()
            timestamp = data.get('timestamp')
            if timestamp and (timestamp.date() in selected_dates_set or not selected_dates_set):
                filtered_data.append(data)
    except Exception as e:
        st.error(f"Error fetching data from collection {collection}: {e}")

filter_data(selected_collection, selected_dates_set)

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

