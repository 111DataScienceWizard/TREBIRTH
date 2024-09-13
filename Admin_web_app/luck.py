import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from scipy.stats import skew, kurtosis 
from google.cloud import firestore
from google.cloud.firestore import FieldFilter
from datetime import datetime, timedelta
import time
import zipfile
import os
import random
from google.api_core.exceptions import ResourceExhausted, RetryError
from collections import defaultdict
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go
from collection_1 import collection_1_data

# Define the collection data mapping
collection_data = {
    'collection_1': collection_1_data
}

# Function to load the data from the imported variables
@st.cache_data
def load_collection(collection_name):
    df = collection_data[collection_name]
    return df

# App title
st.title("Collection Data Viewer")

# Multiselect for collections (Dropdown 1)
collections = st.multiselect(
    "Select collection(s):", 
    options=list(collection_data.keys()), 
    help="You can select one or multiple collections."
)

# Create a placeholder for the second dropdown
if collections:
    # Load data for all selected collections
    all_data = pd.DataFrame()

    for collection in collections:
        df = load_collection(collection)
        all_data = pd.concat([all_data, df])
    
    # Extract unique dates for the selected collections
    all_data['Date of Scans'] = pd.to_datetime(all_data['Date of Scans'])
    unique_dates = all_data['Date of Scans'].dt.date.unique()

    # Multiselect for unique dates (Dropdown 2)
    selected_dates = st.multiselect(
        "Select unique date(s):",
        options=sorted(unique_dates),
        help="Select one or more dates to filter data."
    )

    if selected_dates:
        # Filter the data by the selected dates
        filtered_data = all_data[all_data['Date of Scans'].dt.date.isin(selected_dates)]

        # Display the filtered data
        st.write("Filtered Data:")
        st.dataframe(filtered_data)

        # Print the columns based on the specific selection
        st.write("Filtered Collection Details:")
        st.write(filtered_data[['Device Name', 'Total Scan', 'Total Infected Scan', 'Total Healthy Scan', 
                                'Total Trees', 'Total Infected Trees', 'Total Healthy Trees', 'Date of Scans']])
