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

import streamlit as st
from google.cloud import firestore

# Initialize Firestore
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Set page configuration
st.set_page_config(layout="wide")
st.title('Farm Analytics - Collection Dates')

# Collection dropdown
collections = ['testing', 'TechDemo', 'Plot1', 'Mr.Arjun', 'M1V6_SS_Testing', 'M1V6_GoldStandard', 
               'DevOps', 'DevMode', 'debugging']
selected_collection = st.selectbox('Select a Collection', collections)

if selected_collection:
    # Retrieve unique dates from the selected collection
    docs = db.collection(selected_collection).stream()
    unique_dates = set()
    
    for doc in docs:
        timestamp = doc.to_dict().get('timestamp')
        if timestamp:
            unique_dates.add(timestamp.date())

    # Convert set to sorted list
    unique_dates = sorted(list(unique_dates))
    
    # Display unique dates
    if unique_dates:
        st.write(f"Unique Dates for Collection '{selected_collection}':")
        for date in unique_dates:
            st.write(date.strftime('%d %B %Y'))
    else:
        st.write(f"No dates found for Collection '{selected_collection}'.")
