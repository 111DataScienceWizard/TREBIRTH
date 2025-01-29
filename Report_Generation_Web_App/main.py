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
query = db.collection('demo_day') 

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
          
           
        
        
