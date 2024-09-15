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
from collection_2 import collection_2_data
from collection_3 import collection_3_data
from collection_4 import collection_4_data
from collection_5 import collection_5_data
from collection_6 import collection_6_data
from collection_7 import collection_7_data
from collection_8 import collection_8_data
from collection_9 import collection_9_data
from collection_10 import collection_10_data
from collection_11 import collection_11_data

# Define the collection data mapping
collection_data = {
    'collection_1': collection_1_data,
    'collection_2': collection_2_data,
    'collection_3': collection_3_data,
    'collection_4': collection_4_data,
    'collection_5': collection_5_data,
    'collection_6': collection_6_data,
    'collection_7': collection_7_data,
    'collection_8': collection_8_data,
    'collection_9': collection_9_data,
    'collection_10': collection_10_data,
    'collection_11': collection_11_data
}

# Mapping collections to farmer images
farmer_images = {
    'collection_1': 'Admin_web_app/F1.png',
    'collection_2': 'Admin_web_app/F2.png',
    'collection_3': 'Admin_web_app/F6.png',
    'collection_4': 'Admin_web_app/F4.png',
    'collection_5': 'Admin_web_app/F5.png',
    'collection_6': 'Admin_web_app/F3.png',
    'collection_7': 'Admin_web_app/F7.png',
    'collection_8': 'Admin_web_app/F8.png',
    'collection_9': 'Admin_web_app/F9.png',
    'collection_10': 'Admin_web_app/F10.png',
    'collection_11': 'Admin_web_app/F11.png'
}


farmer_names = {
    'collection_1': 'Dipak Sangamnere',
    'collection_2': 'Ramesh Kapre',
    'collection_3': 'Arvind Khode',
    'collection_4': 'Ravindra Sambherao',
    'collection_5': 'Prabhakr Shirsath',
    'collection_6': 'Arjun Jachak',
    'collection_7': 'Yash More',
    'collection_8': 'Anant More',
    'collection_9': 'Dananjay Yadav',
    'collection_10': 'Kiran Derle',
    'collection_11': 'Nitin Gaidhani'
}

# Farm location mapping
farm_locations = {
    'collection_1': 'Niphad - Kherwadi',
    'collection_2': 'Niphad - Panchkeshwar',
    'collection_3': 'Nashik - Indira Nagar',
    'collection_4': 'Manori - Khurd',
    'collection_5': 'Kundwadi - Niphad',
    'collection_6': 'Pathardi',
    'collection_7': 'Niphad - Pimpalgaon',
    'collection_8': 'Rahuri - Nashik',
    'collection_9': 'Niphad - Kundewadi',
    'collection_10': 'Nashik - Palse',
    'collection_11': 'Nashik - Indira Nagar'
}

# Plot size mapping
plot_sizes = {
    'collection_1': '1 Acre',
    'collection_2': '3 Acre',
    'collection_3': '1 Acre',
    'collection_4': '1.5 Acre',
    'collection_5': '3 Acre',
    'collection_6': '2 Acre',
    'collection_7': '1 Acre',
    'collection_8': '2.5 Acre',
    'collection_9': '2 Acre',
    'collection_10': '3 Acre',
    'collection_11': '2.5 Acre'
}

#How old is the farm
farm_ages = {
    'collection_1': '8 Years',
    'collection_2': '13 Years',
    'collection_3': '6 Years',
    'collection_4': '9 Years',
    'collection_5': '11 Years',
    'collection_6': '8 Years',
    'collection_8': '10 Years',
    'collection_9': '7 Years',
    'collection_10': '4 Years',
    'collection_11': '12 Years'
}

# Function to load the data from the imported variables
def load_collection(collection_name):
    return collection_data[collection_name]

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
    all_data = []
    for collection in collections:
        data = load_collection(collection)
        all_data.extend(data)
    
    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(all_data)
    
    # Convert 'Date of Scans' to datetime
    df['Date of Scans'] = pd.to_datetime(df['Date of Scans']).dt.date
    
    # Extract unique dates for the selected collections
    unique_dates = df['Date of Scans'].unique()
    
    # Multiselect for unique dates (Dropdown 2)
    selected_dates = st.multiselect(
        "Select unique date(s):",
        options=sorted(unique_dates),
        help="Select one or more dates to filter data."
    )

    if selected_dates:
        # Filter the data by the selected dates
        filtered_data = df[df['Date of Scans'].isin(selected_dates)]
        
        # Display the filtered data in the desired format
        st.write("Filtered Data:")
        for date in selected_dates:
            st.write(f"Date: {date}")
            date_data = filtered_data[filtered_data['Date of Scans'] == date]
            for index, row in date_data.iterrows():
                st.write(f"Device Name: {row['Device Name']}")
                st.write(f"Total Scan: {row['Total Scan']}")
                st.write(f"Total Infected Scan: {row['Total Infected Scan']}")
                st.write(f"Total Healthy Scan: {row['Total Healthy Scan']}")
                st.write(f"Total Trees: {row['Total Trees']}")
                st.write(f"Total Infected Trees: {row['Total Infected Trees']}")
                st.write(f"Total Healthy Trees: {row['Total Healthy Trees']}")
                st.write("---")  # Separator for each entry
