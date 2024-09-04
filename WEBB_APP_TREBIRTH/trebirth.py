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
from preprocess import detrend, fq, calculate_statistics, columns_reports_unique, stats_filtereddata
from google.api_core.exceptions import ResourceExhausted, RetryError
from Filter import (coefLPF1Hz, coefLPF2Hz, coefLPF3Hz, coefLPF4Hz, coefLPF5Hz, coefLPF6Hz, coefLPF7Hz, coefLPF8Hz, 
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
row_number = st.text_input('Enter Row number', 'All')
tree_number = st.text_input('Enter Tree number', 'All')
scan_number = st.text_input('Enter Scan number', 'All')
bucket_number = st.text_input('Enter Bucket number', 'All')

# Dropdown for InfStat label selection
label_infstat = st.selectbox('Select Label', ['All', 'Infected', 'Healthy'], index=0)

# Dropdown for selecting sheets in Excel
selected_sheets = st.multiselect('Select Sheets', ['Raw Data', 'Index Data', 'Detrended Data', 'Normalized Data', 'Detrended & Normalized Data', 'Metadata', 'Time Domain Features', 'Frequency Domain Features', 'Frequency Domain Stats', 'Columns Comparison'], default=['Raw Data', 'Metadata'])

# Create a reference to the Firestore collection
query = db.collection('demo_db')

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
    index_data = []
    # Function to slice data
    def slice_data(data):
        if len(data) > 200:
            return data[55:-55]
        return data

    for doc in query_results:
        radar_data.append(slice_data(doc.get('RadarRaw', [])))
        #adxl_data.append(slice_data(doc.get('ADXLRaw', [])))
        adxl_data.append(slice_data(doc.get('ADXLRaw', [])))
        ax_data.append(slice_data(doc.get('Ax', [])))
        ay_data.append(slice_data(doc.get('Ay', [])))
        az_data.append(slice_data(doc.get('Az', [])))
        metadata = doc
        # Convert datetime values to timezone-unaware
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.replace(tzinfo=None)
        metadata_list.append(metadata)
        
        # Append index data if present
        if all(field in doc for field in ['IndexAx', 'IndexAy', 'IndexAz', 'IndexRadar']):
            index_data.append({
                'IndexAx': doc['IndexAx'],
                'IndexAy': doc['IndexAy'],
                'IndexAz': doc['IndexAz'],
                'IndexRadar': doc['IndexRadar']
            })

    # Function to check and insert missing data packets
    def insert_missing_packets(data_list, index_list, packet_size=5, total_packets=200):
        complete_data_list = []
        for data, index in zip(data_list, index_list):
            df_data = pd.DataFrame(data)
            df_index = pd.Series(index)
            
            # Calculate expected indexes
            expected_indexes = list(range(total_packets))
            
            # Identify missing packets
            missing_indexes = list(set(expected_indexes) - set(df_index))
            
            # Insert NaN rows for missing packets
            for mi in missing_indexes:
                start_pos = mi * packet_size
                end_pos = (mi + 1) * packet_size
                insert_df = pd.DataFrame(np.nan, index=range(start_pos, end_pos), columns=df_data.columns)
                df_data = pd.concat([df_data.iloc[:start_pos], insert_df, df_data.iloc[start_pos:]]).reset_index(drop=True)
            
            # Ensure the final length is correct
            df_data = df_data.iloc[:total_packets * packet_size]
            
            complete_data_list.append(df_data)
        
        return complete_data_list

    # Function to process data and check for missing packets
    def process_and_check_data(data_list, index_list, prefix):
        processed_list = []
        for i, (data, index) in enumerate(zip(data_list, index_list)):
            if len(data) != 999:
                missing_packets = 999 - len(data)
                continue
            else:
                data = insert_missing_packets([data], [index])[0]
            df = pd.DataFrame(data)
            df.fillna(df.median(), inplace=True)
            new_columns = [f'{prefix}{i+1}']
            df.columns = new_columns
            processed_list.append(df)
        return pd.concat(processed_list, axis=1) if processed_list else pd.DataFrame()

    df_radar = process_and_check_data(radar_data, [idx['IndexRadar'] for idx in index_data], 'Radar ')
    df_adxl = process_and_check_data(adxl_data, [idx['IndexAx'] for idx in index_data], 'ADXL ')
    df_ax = process_and_check_data(ax_data, [idx['IndexAx'] for idx in index_data], 'Ax ')
    df_ay = process_and_check_data(ay_data, [idx['IndexAy'] for idx in index_data], 'Ay ')
    df_az = process_and_check_data(az_data, [idx['IndexAz'] for idx in index_data], 'Az ')
    #Process each scan's data individually and concatenate later
    #def process_data(data_list, prefix):
        #processed_list = []
        #for i, data in enumerate(data_list):
            #df = pd.DataFrame(data)
            #df.fillna(df.median(), inplace=True)
            #new_columns = [f'{prefix}{i+1}']
            #df.columns = new_columns
            #processed_list.append(df)
        #return pd.concat(processed_list, axis=1)

    #df_radar = process_data(radar_data, 'Radar ')
    #df_adxl = process_data(adxl_data, 'ADXL ')
    #df_ax = process_data(ax_data, 'Ax ')
    #df_ay = process_data(ay_data, 'Ay ')
    #df_az = process_data(az_data, 'Az ')

    # Concatenate all DataFrames column-wise
    df_combined = pd.concat([df_radar, df_adxl, df_ax, df_ay, df_az], axis=1)

    #filtered_data_df = pd.DataFrame({col: process(coefLPF50Hz, df_combined[col].values) for col in df_combined.columns})

    # Detrend all the columns
    df_combined_detrended = df_combined.apply(detrend)
  
    # Normalize all the columns
    df_combined_normalized = (df_combined_detrended - df_combined_detrended.min()) / (df_combined_detrended.max() - df_combined_detrended.min())

    # Convert list of dictionaries to DataFrame
    df_metadata = pd.DataFrame(metadata_list)

    # Select only the desired columns
    desired_columns = ['DeviceName:', 'TreeSec', 'TreeNo', 'InfStat', 'TreeID', 'RowNo', 'ScanNo', 'timestamp']
    df_metadata_filtered = df_metadata[desired_columns]

    #Convert index data to DataFrame if present
    #if index_data:
        #df_index = pd.DataFrame(index_data)
        #df_index_long = df_index.apply(pd.Series.explode)
      
    #Convert index data to DataFrame if present
   
  
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
            radar_columns = [col for col in df_combined.columns if 'Radar' in col]
            df_radar_data = df_combined[radar_columns]
            #frequencies, powers = fq(df_combined)
            frequencies.to_excel(writer, sheet_name='Frequencies', index=False)
            powers.to_excel(writer, sheet_name='Powers', index=False)
        if 'Frequency Domain Stats' in selected_sheets:
            radar_columns = [col for col in df_combined.columns if 'Radar' in col]
            df_radar_data = df_combined[radar_columns]
            frequencies, powers = fq(df_radar_data)
            frequencies_stats = calculate_statistics(frequencies)
            powers_stats = calculate_statistics(powers)
            frequencies_stats.to_excel(writer, sheet_name='Frequencies Stats', index=False)
            powers_stats.to_excel(writer, sheet_name='Power Stats', index=False)
        if 'Columns Comparison' in selected_sheets:
            columns_comparison = columns_reports_unique(df_combined_detrended)
            columns_comparison.to_excel(writer, sheet_name='Columns Comparison', index=False)
        if 'Index Data' in selected_sheets and index_data:
            df_index_long.to_excel(writer, sheet_name='Index Data', index=False)
          
    excel_data.seek(0)

    # Download button for selected sheets and metadata
    st.download_button("Download Selected Sheets and Metadata", excel_data, file_name=f"{file_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excel')
