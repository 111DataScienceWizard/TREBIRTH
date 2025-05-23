# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Create a reference to the Firestore collection
query = db.collection('demo_db')

# Dropdown for selecting sheets in Excel
selected_sheets = st.multiselect('Select Sheets', ['Raw Data', 'Detrended Data', 'Normalized Data', 'Detrended & Normalized Data', 'Metadata', 'Time Domain Features', 'Frequency Domain Features', 'Columns Comparison'], default=['Raw Data', 'Metadata'])


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
    metadata_list = []

    # Function to slice data
    def slice_data(data):
        if len(data) > 1000:
            return data[100:-100]
        return data

    for doc in query_results:
        radar_data.append(slice_data(doc.get('RadarRaw', [])))
       
        metadata = doc
        # Convert datetime values to timezone-unaware
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.replace(tzinfo=None)
        metadata_list.append(metadata)

    
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
   

    # Concatenate all DataFrames column-wise
    df_combined = pd.concat([df_radar, axis=1)
    #df_combined = pd.concat([df_radar, df_adxl, df_ax, df_ay, df_az], axis=1)

    filtered_data_df = pd.DataFrame({col: process(coefLPF50Hz, df_combined[col].values) for col in df_combined.columns})

    # Detrend all the columns
    df_combined_detrended = df_combined.apply(detrend)
  
    # Normalize all the columns
    df_combined_normalized = (df_combined_detrended - df_combined_detrended.min()) / (df_combined_detrended.max() - df_combined_detrended.min())

    # Convert list of dictionaries to DataFrame
    df_metadata = pd.DataFrame(metadata_list)

    # Select only the desired columns
    desired_columns = ['timestamp', 'Area', 'Damage visible', 'Infestation', 'Insect type', 'Pest details', 'Report Location', 'Report requested by', 'Scan Duration', 'Scan Location', 'Termatrac device position', 'Termatrac device was', 'Tests were carried out by', 'DeviceName']
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
  

  
          












import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from scipy.stats import skew, kurtosis
from google.cloud import firestore
from google.cloud.firestore import FieldFilter
from datetime import datetime, timedelta
import pytz
import time
import random
from google.api_core.exceptions import ResourceExhausted, RetryError
from collections import defaultdict
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go



# Set page configuration
st.set_page_config(layout="wide")
st.title("Farm Analytics")

db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")


def convert_to_local_time(timestamp, timezone='Asia/Kolkata'):
    local_tz = pytz.timezone(timezone)
    # Convert to UTC and then localize to the given timezone
    return timestamp.astimezone(local_tz)
    
# Fetch the most recent scan data from the "demo_db" collection
def get_recent_scans(db, num_scans=3):
    docs = (
        db.collection('demo_day')
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(num_scans)
        .stream()
    )
    metadata_list = []
    for doc in docs:
        data_dict = doc.to_dict()
        metadata = {
            'RadarRaw': data_dict.get('RadarRaw', []),
            'InfStat': data_dict.get('InfStat', 'Unknown'),
            'timestamp': convert_to_local_time(data_dict.get('timestamp')),
            'DeviceName': data_dict.get('Devicename', 'Unknown')
        }
        metadata_list.append(metadata)
    return metadata_list

# Filter scans by the same device name
def filter_scans_by_device(scans):
    scans_df = pd.DataFrame(scans).sort_values(by='timestamp', ascending=False)
    for device, group in scans_df.groupby('DeviceName'):
        if len(group) >= 2:
            return group.head(2)
    
    return pd.DataFrame()
    
# Preprocess data for each scan
def preprocess_multiple_scans(radar_data_list):
    processed_data_list = []
    for radar_raw in radar_data_list:
        df_radar = pd.DataFrame(radar_raw, columns=['Radar'])
        df_radar.dropna(inplace=True)
        df_radar.fillna(df_radar.mean(), inplace=True)
        processed_data_list.append(df_radar)
    return processed_data_list



# Plot time domain
def plot_time_domain(preprocessed_scans, timestamps, infstats, device_names, sampling_rate=100):
    st.write("## Time Domain")
    fig = go.Figure()

    for i, preprocessed_scan in enumerate(preprocessed_scans):
        device_name_in_parentheses = device_names[i][device_names[i].find('(') + 1:device_names[i].find(')')]
        color = 'green' if infstats[i] == 'Healthy' else 'red'
        time_seconds = np.arange(len(preprocessed_scan)) / sampling_rate
        fig.add_trace(go.Scatter(
            x=time_seconds,
            y=preprocessed_scan['Radar'],
            mode='lines',
            name=f"{device_name_in_parentheses} - {timestamps[i].strftime('%Y-%m-%d %H:%M:%S')}",
            line=dict(color=color)
        ))

    fig.update_layout(
        template='plotly_white',
        xaxis_title="Time (s)",
        yaxis_title="Signal",
        legend_title="Scans",
        font=dict(color="white"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig)



def main():
    # Fetch recent scans
    recent_scans = get_recent_scans(db, num_scans=3)
    
    if recent_scans:
        # Filter scans by device name and pick the 2 most recent ones with the same device name
        filtered_scans = filter_scans_by_device(recent_scans)
        
        if not filtered_scans.empty:
            st.markdown(" Data Analysis of 2 Recent Scans with Same Device")
            
            # Preprocess the scan data
            processed_data_list = preprocess_multiple_scans(filtered_scans['RadarRaw'])
            
            # Extract timestamps and InfStat
            timestamps = filtered_scans['timestamp'].tolist()
            infstats = filtered_scans['InfStat'].tolist()
            device_names = filtered_scans['DeviceName'].tolist()
            
            # Create columns for plots
            col1, col2, col3 = st.columns(3)
            
            # Time domain plot in col1
            with col1:
                plot_time_domain(processed_data_list, timestamps, infstats, device_names)

            # Frequency domain plot in col2
            with col2:
                plot_frequency_domain(processed_data_list, timestamps, infstats, device_names)
            
            # Statistics plot in col3
            with col3:
                stats_dfs = [calculate_statistics(df) for df in processed_data_list]
                plot_multiple_statistics(stats_dfs, timestamps, infstats, device_names)
        else:
            st.warning("No matching scans found with the same device name.")
    else:
        st.error("No recent scan data available.")

if __name__ == "__main__":
    main()

st.write(f"**Farmer Name:** Dananjay Yadav", color='white')
st.write(f"**Farm Location:** Null", color='white')
st.write(f"**Farm Age:** Null", color='white')
st.write(f"**Plot Size:** Null", color='white')



# Function to load the data from the imported variables
def load_collection(collection_name):
    return collection_data[collection_name]
    
# Multiselect for collections (Dropdown 1)
collections = st.multiselect(
    "Select farm(s):", 
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

    # If dates are selected
    if selected_dates:
        healthy_counts = []
        infected_counts = []
        farmer_names_list = [farmer_names.get(collection, 'Unknown Farmer') for collection in collections]

        # Process data for each selected collection
        for collection in collections:
            data = load_collection(collection)
            filtered_data = [entry for entry in data if pd.to_datetime(entry['Date of Scans']).date() in selected_dates]

            # Calculate total healthy and infected scans for the collection
            total_healthy = sum(entry['Total Healthy Scan'] for entry in filtered_data)
            total_infected = sum(entry['Total Infected Scan'] for entry in filtered_data)
            
            healthy_counts.append(total_healthy)
            infected_counts.append(total_infected)
            
        # If data is filtered, generate statistics
        if filtered_data:
            filtered_df = pd.DataFrame(filtered_data)
            total_healthy = filtered_df['Total Healthy Scan'].sum()
            total_infected = filtered_df['Total Infected Scan'].sum()
            
            # Infection and healthy percentage calculations
            total_scans = total_healthy + total_infected
            infection_percentage = (total_infected / total_scans) * 100 if total_scans > 0 else 0
            healthy_percentage = 100 - infection_percentage if total_scans > 0 else 0
            
            # Share data by each device
            if 'Device Name' in filtered_df.columns:
                device_scan_counts = filtered_df.groupby('Device Name')['Total Scan'].sum()
                data_share_text = "".join([f"{device}: {count / device_scan_counts.sum() * 100:.2f}%<br>" for device, count in device_scan_counts.items()])
          
           
        
        
