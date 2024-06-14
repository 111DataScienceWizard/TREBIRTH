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
import json
from scipy import signal
from scipy.stats import skew, kurtosis
from preprocess import detrend, fq, calculate_statistics, columns_reports_unique, stats_filtereddata
from google.api_core.exceptions import ResourceExhausted, RetryError
from Filters import (coefLPF1Hz, coefLPF2Hz, coefLPF3Hz, coefLPF4Hz, coefLPF5Hz, coefLPF6Hz, coefLPF7Hz, coefLPF8Hz, 
                     coefLPF9Hz, coefLPF10Hz, coefLPF11Hz, coefLPF12Hz, coefLPF13Hz, coefLPF14Hz, coefLPF15Hz, 
                     coefLPF16Hz, coefLPF17Hz, coefLPF18Hz, coefLPF19Hz, coefLPF20Hz, coefLPF21Hz, coefLPF22Hz, 
                     coefLPF23Hz, coefLPF24Hz, coefLPF25Hz, coefLPF26Hz, coefLPF27Hz, coefLPF28Hz, coefLPF29Hz, 
                     coefLPF30Hz, coefLPF31Hz, coefLPF32Hz, coefLPF33Hz, coefLPF34Hz, coefLPF35Hz, coefLPF36Hz, 
                     coefLPF37Hz, coefLPF38Hz, coefLPF39Hz, coefLPF40Hz, coefLPF41Hz, coefLPF42Hz, coefLPF43Hz, 
                     coefLPF44Hz, coefLPF45Hz, coefLPF46Hz, coefLPF47Hz, coefLPF48Hz, coefLPF49Hz, coefLPF50Hz,
                     coefHPF1Hz, coefHPF2Hz, coefHPF3Hz, coefHPF4Hz, coefHPF5Hz, coefHPF6Hz, coefHPF7Hz, coefHPF8Hz, 
                     coefHPF9Hz, coefHPF10Hz, coefHPF11Hz, coefHPF12Hz, coefHPF13Hz, coefHPF14Hz, coefHPF15Hz, 
                     coefHPF16Hz, coefHPF17Hz, coefHPF18Hz, coefHPF19Hz, coefHPF20Hz, coefHPF21Hz, coefHPF22Hz, 
                     coefHPF23Hz, coefHPF24Hz, coefHPF25Hz, coefHPF26Hz, coefHPF27Hz, coefHPF28Hz, coefHPF29Hz, 
                     coefHPF30Hz, coefHPF31Hz, coefHPF32Hz, coefHPF33Hz, coefHPF34Hz, coefHPF35Hz, coefHPF36Hz, 
                     coefHPF37Hz, coefHPF38Hz, coefHPF39Hz, coefHPF40Hz, coefHPF41Hz, coefHPF42Hz, coefHPF43Hz, 
                     coefHPF44Hz, coefHPF45Hz, coefHPF46Hz, coefHPF47Hz, coefHPF48Hz, coefHPF49Hz, coefHPF50Hz)

#st.set_page_config(layout="wide")

# Predefined credentials
VALID_USERNAME = "TREBIRTH"
VALID_PASSWORD = "MUKUND"

# Function to check login credentials
def check_login(username, password):
    return username == VALID_USERNAME and password == VALID_PASSWORD

# Read the credentials from Streamlit secrets
creds = {
    "type": st.secrets["firestore"]["type"],
    "project_id": st.secrets["firestore"]["project_id"],
    "private_key_id": st.secrets["firestore"]["private_key_id"],
    "private_key": st.secrets["firestore"]["private_key"].replace("\\n", "\n"),  # Ensure the newlines are correctly interpreted
    "client_email": st.secrets["firestore"]["client_email"],
    "client_id": st.secrets["firestore"]["client_id"],
    "auth_uri": st.secrets["firestore"]["auth_uri"],
    "token_uri": st.secrets["firestore"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["firestore"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["firestore"]["client_x509_cert_url"]
}

def process(coef, in_signal):
    FILTERTAPS = len(coef)
    values = np.zeros(FILTERTAPS)
    out_signal = []
    gain = 1.0
    k = 0
    for in_value in in_signal:
        values[k] = in_value
        out = np.dot(coef, np.roll(values, k))
        out /= gain
        out_signal.append(out)
        k = (k + 1) % FILTERTAPS
    return out_signal

# Function to show login page
def show_login_page():
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")
    
    if login_button:
        if check_login(username, password):
            st.experimental_set_query_params(logged_in=True)
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")

# Function to show main content
def show_main_page():
    st.title('Data Analytics')
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

    # Authenticate to Firestore with the JSON account key.
    db = firestore.Client.from_service_account_info(creds)
    
    # User input for Row No., Tree No., Scan No., and Label
    row_number = st.text_input('Enter Row number', 'All')
    tree_number = st.text_input('Enter Tree number', 'All')
    scan_number = st.text_input('Enter Scan number', 'All')
    bucket_number = st.text_input('Enter Bucket number', 'All')
    
    # Dropdown for InfStat label selection
    label_infstat = st.selectbox('Select Label', ['All', 'Infected', 'Healthy'], index=0)
    
    # Dropdown for selecting sheets in Excel
    selected_sheets = st.multiselect('Select Sheets', ['Raw Data', 'Detrended Data', 'Normalized Data', 'Detrended & Normalized Data', 'Metadata', 'Time Domain Features', 'Frequency Domain Features', 'Columns Comparison'], default=['Raw Data', 'Metadata'])
    
    # Create a reference to the Firestore collection
    query = db.collection('M1V6_SS_Testing')
    
    # Apply filters based on user input
    if row_number != 'All':
        query = query.where('RowNo', '==', int(row_number))
    if tree_number != 'All':
        query = query.where('TreeNo', '==', int(tree_number))
    if scan_number != 'All':
        query = query.where('ScanNo', '==', int(scan_number))
    if bucket_number != 'All':
        query = query.where('BucketID', '==', str(bucket_number))
    if label_infstat != 'All':
        query = query.where('InfStat', '==', label_infstat)
    
    # Get documents based on the query
    try:
        query_results = [doc.to_dict() for doc in query.stream()]
    except Exception as e:
        st.error(f"Failed to retrieve data: {e}")
        st.stop()
    
    if not query_results:
        st.write("No data found matching the specified criteria.")
    else:
        # Create empty lists to store data
        radar_data = []
        adxl_data = []
        ax_data = []
        ay_data = []
        az_data = []
        metadata_list = []
    
        for doc in query_results:
            radar_data.append(doc.get('RadarRaw', []))
            adxl_data.append(doc.get('ADXLRaw', []))
            ax_data.append(doc.get('Ax', []))
            ay_data.append(doc.get('Ay', []))
            az_data.append(doc.get('Az', []))
            metadata = doc
            # Convert datetime values to timezone-unaware
            for key, value in metadata.items():
                if isinstance(value, datetime):
                    metadata[key] = value.replace(tzinfo=None)
            metadata_list.append(metadata)
    
        # Process each scan's data individually and concatenate later
        def process_data(data_list, prefix):
            processed_list = []
            for i, data in enumerate(data_list):
                df = pd.DataFrame(data).dropna()
                df.fillna(df.mean(), inplace=True)
                new_columns = [f'{prefix}{i+1}']
                df.columns = new_columns
                processed_list.append(df)
            return pd.concat(processed_list, axis=1)
    
        df_radar = process_data(radar_data, 'Radar ')
        df_adxl = process_data(adxl_data, 'ADXL ')
        df_ax = process_data(ax_data, 'Ax ')
        df_ay = process_data(ay_data, 'Ay ')
        df_az = process_data(az_data, 'Az ')
    
        # Concatenate all DataFrames column-wise
        df_combined = pd.concat([df_radar, df_adxl, df_ax, df_ay, df_az], axis=1)
    
        # Detrend all the columns
        df_combined_detrended = df_combined.apply(detrend)
      
        # Normalize all the columns
        df_combined_normalized = (df_combined_detrended - df_combined_detrended.min()) / (df_combined_detrended.max() - df_combined_detrended.min())
    
        # Convert list of dictionaries to DataFrame
        df_metadata = pd.DataFrame(metadata_list)
    
        # Select only the desired columns
        desired_columns = ['DeviceName:', 'TreeSec', 'TreeNo', 'InfStat', 'TreeID', 'RowNo', 'ScanNo', 'timestamp']
        df_metadata_filtered = df_metadata[desired_columns]
    
        # Construct file name based on user inputs
        file_name_parts = []
        if row_number != 'All':
            file_name_parts.append(f'R{row_number}')
        if tree_number != 'All':
            file_name_parts.append(f'T{tree_number}')
        if scan_number != 'All':
            file_name_parts.append(f'S{scan_number}')
    
        # Join file name parts with underscore
        file_name = '_'.join(file_name_parts)
    
        # Convert DataFrame to Excel format
        excel_data = BytesIO()
        with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
            if 'Raw Data' in selected_sheets:
                df_combined.to_excel(writer, sheet_name='Raw Data', index=False)
            if 'Detrended Data' in selected_sheets:
                df_combined_detrended.to_excel(writer, sheet_name='Detrended Data', index=False)
            if 'Normalized Data' in selected_sheets:
                df_combined_normalized.to_excel(writer, sheet_name='Normalized Data', index=False)
            if 'Detrended & Normalized Data' in selected_sheets:
                df_combined_detrended_normalized = (df_combined_detrended - df_combined_detrended.min()) / (df_combined_detrended.max() - df_combined_detrended.min())
                df_combined_detrended_normalized.to_excel(writer, sheet_name='Detrended & Normalized Data', index=False)
            if 'Metadata' in selected_sheets:
                df_metadata_filtered.to_excel(writer, sheet_name='Metadata', index=False)
            if 'Time Domain Features' in selected_sheets:
                time_domain_features = calculate_statistics(df_combined)
                time_domain_features.to_excel(writer, sheet_name='Time Domain Features', index=False)
            if 'Frequency Domain Features' in selected_sheets:
                frequencies, powers = fq(df_combined_detrended)
                frequencies.to_excel(writer, sheet_name='Frequencies', index=False)
                powers.to_excel(writer, sheet_name='Powers', index=False)
            if 'Columns Comparison' in selected_sheets:
                columns_comparison = columns_reports_unique(df_combined_detrended)
                columns_comparison.to_excel(writer, sheet_name='Columns Comparison', index=False)
    
        excel_data.seek(0)
    
        # Download button for selected sheets and metadata
        st.download_button("Download Selected Sheets and Metadata", excel_data, file_name=f"{file_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excel')
        st.write("Columns in df_combined_detrended:", df_combined_detrended.columns)

# Set page configuration
st.set_page_config(layout="wide")

# Check if the user is logged in by looking for the query parameter
query_params = st.experimental_get_query_params()
if "logged_in" in query_params:
    show_main_page()
else:
    show_login_page()
