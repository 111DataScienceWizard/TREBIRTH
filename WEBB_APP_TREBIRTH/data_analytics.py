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
from scipy import signal
from scipy.stats import skew, kurtosis
from preprocess import detrend, fq, stats_radar, columns_reports_unique
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

def stats_filtereddata(df, band):
    stats = {
        "Band": [],
        "STD": [],
        "PTP": [],
        "Mean": [],
        "RMS": [],
        "Skew": [],
        "Kurtosis": []
    }

    for column in df.columns:
        stats["Band"].append(band)
        stats["STD"].append(np.std(df[column]))
        stats["PTP"].append(np.ptp(df[column]))
        stats["Mean"].append(np.mean(df[column]))
        stats["RMS"].append(np.sqrt(np.mean(df[column]**2)))
        stats["Skew"].append(skew(df[column]))
        stats["Kurtosis"].append(kurtosis(df[column]))

    return pd.DataFrame(stats)

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
  
# Set page configuration
st.set_page_config(layout="wide")
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
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# User input for Row No., Tree No., Scan No., and Label
row_number = st.text_input('Enter Row number')
tree_number = st.text_input('Enter Tree number')
scan_number = st.text_input('Enter Scan number', 'All')
bucket_number = st.text_input('Enter Bucket number', 'All')

# Dropdown for InfStat label selection
label_infstat = st.selectbox('Select Label', ['All', 'Infected', 'Healthy'], index=0)

# Dropdown for selecting sheets in Excel
selected_sheets = st.multiselect('Select Sheets', ['Raw Data', 'Detrended Data', 'Normalized Data', 'Detrended & Normalized Data', 'Metadata', 'Time Domain Features', 'Frequency Domain Features', 'Columns Comparison'], default=['Raw Data', 'Metadata'])

# Create a reference to the Firestore collection
query = db.collection('BT_Classic') 

# Apply filters based on user input
if row_number:
    query = query.where('RowNo', '==', int(row_number))
if tree_number:
    query = query.where('TreeNo', '==', int(tree_number))
if scan_number != 'All':
    query = query.where('ScanNo', '==', int(scan_number))
if bucket_number != 'All':
    query = query.where('BucketID', '==', int(bucket_number))
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
    #adxl_data = []
    ax_data = []
    ay_data = []
    az_data = []
    metadata_list = []

    # Function to slice data
    def slice_data(data):
        if len(data) > 1000:
            return data[100:-100]
        return data

    for doc in query_results:
        radar_data.append(slice_data(doc.get('RadarRaw', [])))
        #adxl_data.append(slice_data(doc.get('ADXLRaw', [])))
        ax_data.append(slice_data(doc.get('Ax', [])))
        ay_data.append(slice_data(doc.get('Ay', [])))
        az_data.append(slice_data(doc.get('Az', [])))
        metadata = doc
        # Convert datetime values to timezone-unaware
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.replace(tzinfo=None)
        metadata_list.append(metadata)

    # Process each scan's data individually and concatenate later
    #def process_data(data_list, prefix):
        #processed_list = []
        #for i, data in enumerate(data_list):
            #df = pd.DataFrame(data).dropna()
            #df.fillna(df.mean(), inplace=True)
            #new_columns = [f'{prefix}{i}']
            #df.columns = new_columns
            #processed_list.append(df)
        #return pd.concat(processed_list, axis=1)

    def process_data(data_list, prefix):
        processed_list = []
        for i, data in enumerate(data_list):
            if not data:  # Skip empty data
                continue
        
            df = pd.DataFrame(data).dropna()
            df.fillna(df.mean(), inplace=True)
        
            if df.empty:
                st.warning(f"No data available for {prefix}{i+1}. Skipping.")
                continue
        
            new_columns = [f'{prefix}{i+1}'] * df.shape[1]  # Ensure new_columns matches the number of DataFrame columns
            if len(new_columns) != df.shape[1]:
                st.warning(f"Column mismatch for {prefix}{i+1}. Expected {df.shape[1]} columns, got {len(new_columns)}.")
                continue
        
            df.columns = new_columns
            processed_list.append(df)
        
        if processed_list:
            return pd.concat(processed_list, axis=1)
        else:
            st.warning("No data processed. Returning empty DataFrame.")
            return pd.DataFrame()  # Return an empty DataFrame if no data was processed

    df_radar = process_data(radar_data, 'Radar ')
    #df_adxl = process_data(adxl_data, 'ADXL ')
    df_ax = process_data(ax_data, 'Ax ')
    df_ay = process_data(ay_data, 'Ay ')
    df_az = process_data(az_data, 'Az ')

    # Concatenate all DataFrames column-wise
    df_combined = pd.concat([df_radar, df_ax, df_ay, df_az], axis=1)
    #df_combined = pd.concat([df_radar, df_adxl, df_ax, df_ay, df_az], axis=1)

    filtered_data_df = pd.DataFrame({col: process(coefLPF50Hz, df_combined[col].values) for col in df_combined.columns})

    # Detrend all the columns
    df_combined_detrended = df_combined.apply(detrend)
  
    # Normalize all the columns
    df_combined_normalized = (df_combined_detrended - df_combined_detrended.min()) / (df_combined_detrended.max() - df_combined_detrended.min())

    # Convert list of dictionaries to DataFrame
    df_metadata = pd.DataFrame(metadata_list)

    # Select only the desired columns
    #desired_columns = ['TreeSec', 'TreeNo', 'InfStat', 'TreeID', 'RowNo', 'ScanNo', 'timestamp']
    desired_columns = ['TreeNo', 'InfStat', 'TreeID', 'RowNo', 'ScanNo', 'timestamp']
    df_metadata_filtered = df_metadata[desired_columns]

    # Construct file name based on user inputs
    file_name_parts = []
    if row_number:
        file_name_parts.append(f'R{row_number}')
    if tree_number:
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
            time_domain_features = stats_radar(df_combined_detrended)
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
    #st.write("Columns in df_combined_detrended:", df_combined_detrended.columns)
  
    # Adding filter selection components
    filter_type = st.selectbox('Select Filter Type', ['Low Pass Filter (LPF)', 'High Pass Filter (HPF)', 'Band Pass Filter (BPF)'])

    if filter_type == 'Band Pass Filter (BPF)':
        low_freq, high_freq = st.slider('Select Frequency Range (Hz)', 1, 50, (5, 10))
    else:
        frequency = st.slider('Select Frequency (Hz)', 1, 50)

    # Map selected filter type and frequency to the corresponding coefficients
    if filter_type == 'Low Pass Filter (LPF)':
        filter_coef = globals()[f'coefLPF{frequency}Hz']
    elif filter_type == 'High Pass Filter (HPF)':
        filter_coef = globals()[f'coefHPF{frequency}Hz']
    elif filter_type == 'Band Pass Filter (BPF)':
        filter_coef_low = globals()[f'coefHPF{low_freq}Hz']
        filter_coef_high = globals()[f'coefLPF{high_freq}Hz']

    # Apply the selected filter only to Radar and ADXL columns
    # List to hold all Radar and ADXL column names
    radar_columns = [f'Radar {i+1}' for i in range(30)]  # Assuming there are 10 scans
    #adxl_columns = [f'ADXL {i}' for i in range(30)]  # Assuming there are 10 scans
    available_radar_columns = [col for col in df_combined_detrended.columns if col.startswith('Radar')]

    # Dictionary to hold the filtered data columns for Radar and ADXL
    filtered_radar_columns = {}
    #filtered_adxl_columns = {}

    # Add data for each scan to the filtered columns dictionary
    for i, radar_col in enumerate(available_radar_columns):
        filtered_radar_columns[f'Radar {i+1}'] = df_combined_detrended[radar_col]
        #filtered_adxl_columns[f'ADXL {i}'] = df_combined_detrended[f'ADXL {i}']

    # Apply the process function on each column
    if filter_type == 'Band Pass Filter (BPF)':
        filtered_radar_data_low = pd.DataFrame({col: process(filter_coef_low, data.values) for col, data in filtered_radar_columns.items()})
        filtered_radar_data = pd.DataFrame({col: process(filter_coef_high, data.values) for col, data in filtered_radar_data_low.items()})
        #filtered_adxl_data_low = pd.DataFrame({col: process(filter_coef_low, data.values) for col, data in filtered_adxl_columns.items()})
        #filtered_adxl_data = pd.DataFrame({col: process(filter_coef_high, data.values) for col, data in filtered_adxl_data_low.items()})
    else:
        filtered_radar_data = pd.DataFrame({col: process(filter_coef, data.values) for col, data in filtered_radar_columns.items()})
        #filtered_adxl_data = pd.DataFrame({col: process(filter_coef, data.values) for col, data in filtered_adxl_columns.items()})

filtered_data = pd.concat([filtered_radar_data], axis=1)
#filtered_data = pd.concat([filtered_radar_data, filtered_adxl_data], axis=1)


# Multi-select box to select desired sheets
selected_sheets = st.multiselect('Select Sheets to Download', ['Filtered Data', 'Time Domain Features', 'Columns Comparison'])

# Add a button to trigger the download
if st.button("Download Selected Sheets"):
    # Prepare the Excel file with selected sheets
    filtered_excel_data = BytesIO()
    with pd.ExcelWriter(filtered_excel_data, engine='xlsxwriter') as writer:
        for sheet_name in selected_sheets:
            # Write each selected sheet to the Excel file
            if sheet_name == 'Filtered Data':
                # Write filtered data to the sheet
                filtered_data.to_excel(writer, sheet_name=sheet_name, index=False)
            elif sheet_name == 'Time Domain Features':
                # Apply the time domain features on the filtered data
                time_domain_features_filtered = stats_radar(filtered_data)
                # Write time domain features data to the sheet
                time_domain_features_filtered.to_excel(writer, sheet_name=sheet_name, index=False)
            elif sheet_name == 'Columns Comparison':
                # Apply the columns comparison on the filtered data
                columns_comparison_filtered = columns_reports_unique(filtered_data)
                # Write column comparison data to the sheet
                columns_comparison_filtered.to_excel(writer, sheet_name=sheet_name, index=False)

    # Set the pointer to the beginning of the file
    filtered_excel_data.seek(0)

    # Trigger the download of the Excel file
    st.download_button("Download Filtered Data", filtered_excel_data, file_name=f"Filtered_{filter_type.replace(' ', '')}{frequency if filter_type != 'Band Pass Filter (BPF)' else f'{low_freq}to{high_freq}'}Hz.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-filtered-excel')
