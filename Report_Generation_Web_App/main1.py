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
import pytz
import random
from scipy import signal
from scipy.stats import skew, kurtosis
from collections import defaultdict
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go
from preprocess import detrend, fq, stats_radar, columns_reports_unique
from google.api_core.exceptions import ResourceExhausted, RetryError


st.set_page_config(layout="wide")
st.title('Test Analysis Report')
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

db = firestore.Client.from_service_account_json("Report_Generation_Web_App/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

query = db.collection('demo_db') 

def fetch_data():
    db = firestore.Client()
    collection_ref = db.collection("demo_db")
    docs = collection_ref.stream()
    
    locations = set()
    companies = set()
    scans_data = []
    
    for doc in docs:
        data = doc.to_dict()
        if "Report Location" in data and "Tests were carried out by" in data:
            locations.add(data["Report Location"].strip())
            companies.add(data["Tests were carried out by"].strip())
            scans_data.append(data)
    
    return sorted(locations), sorted(companies), scans_data

# Fetch data from Firestore
locations, companies, scans_data = fetch_data()

st.title("Scan Report Viewer")

# Multi-select dropdowns
selected_locations = st.multiselect("Select Report Location:", locations)
selected_companies = st.multiselect("Select Company:", companies)

# Filter and display results
if selected_locations or selected_companies:
    matched_users = set()
    for scan in scans_data:
        if (not selected_locations or scan["Report Location"].strip() in selected_locations) and \
           (not selected_companies or scan["Tests were carried out by"].strip() in selected_companies):
            matched_users.add(scan["Report requested by"].strip())

    if matched_users:
        st.write("### Report requested by:")
        for user in sorted(matched_users):
            st.write(user)
    else:
        st.write("No data found")





