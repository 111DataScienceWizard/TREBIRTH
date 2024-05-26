import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import time
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
                     coefLPF44Hz, coefLPF45Hz, coefLPF46Hz, coefLPF47Hz, coefLPF48Hz, coefLPF49Hz, 
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

# Dropdown for InfStat label selection
label_infstat = st.selectbox('Select Label', ['All', 'Infected', 'Healthy'], index=0)

# Dropdown for selecting sheets in Excel
selected_sheets = st.multiselect('Select Sheets', ['Raw Data', 'Detrended Data', 'Normalized Data', 'Detrended & Normalized Data', 'Metadata', 'Time Domain Features', 'Frequency Domain Features', 'Columns Comparison'], default=['Raw Data', 'Metadata'])

# Create a reference to the Google post.
query = db.collection('DevOps')

# Filter based on user input
if row_number != 'All':
    query = query.where('RowNo', '==', int(row_number))
if tree_number != 'All':
    query = query.where('TreeNo', '==', int(tree_number))
if scan_number != 'All':
    query = query.where('ScanNo', '==', int(scan_number))
if label_infstat != 'All':
    query = query.where('InfStat', '==', label_infstat)

# Get documents based on the query
try:
    query_results = get_firestore_data(query)
except Exception as e:
    st.error(f"Failed to retrieve data: {e}")
    st.stop()

if len(query_results) == 0:
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
        radar_data.append(doc.to_dict().get('RadarRaw', []))
        adxl_data.append(doc.to_dict().get('ADXLRaw', []))
        ax_data.append(doc.to_dict().get('Ax', []))
        ay_data.append(doc.to_dict().get('Ay', []))
        az_data.append(doc.to_dict().get('Az', []))
        metadata = doc.to_dict()
        # Convert datetime values to timezone-unaware
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.replace(tzinfo=None)
        metadata_list.append(metadata)

    num_scans = max(len(radar_data[0]))

    # Create DataFrames for each data type
    radar_columns = [f'Radar {i+1}' for i in range(num_scans)]
    adxl_columns = [f'ADXL {i+1}' for i in range(num_scans)]
    ax_columns = [f'Ax {i+1}' for i in range(num_scans)]
    ay_columns = [f'Ay {i+1}' for i in range(num_scans)]
    az_columns = [f'Az {i+1}' for i in range(num_scans)]

    df_radar = pd.DataFrame(radar_data).transpose()
    df_radar.columns = radar_columns

    df_adxl = pd.DataFrame(adxl_data).transpose()
    df_adxl.columns = adxl_columns

    df_ax = pd.DataFrame(ax_data).transpose()
    df_ax.columns = ax_columns

    df_ay = pd.DataFrame(ay_data).transpose()
    df_ay.columns = ay_columns

    df_az = pd.DataFrame(az_data).transpose()
    df_az.columns = az_columns

    # Concatenate the DataFrames column-wise
    df_combined = pd.concat([df_radar, df_adxl, df_ax, df_ay, df_az], axis=1)

    # Slice the DataFrame to the desired range
    df_combined = df_combined[100:1800]

    # Drop null values from the combined dataframe
    df_combined.dropna(inplace=True)

    # Impute missing values (if any)
    df_combined.fillna(df_combined.mean(), inplace=True)

    # Detrend all the columns
    df_combined_detrended = df_combined.apply(detrend)

    # Normalize all the columns
    df_combined_normalized = (df_combined_detrended - df_combined_detrended.min()) / (df_combined_detrended.max() - df_combined_detrended.min())

    # Convert list of dictionaries to DataFrame
    df_metadata = pd.DataFrame(metadata_list)

    # Select only the desired columns
    desired_columns = ['TreeSec', 'TreeNo', 'InfStat', 'TreeID', 'RowNo', 'ScanNo', 'timestamp']
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
    radar_columns = [f'Radar {i}' for i in range(30)]  # Assuming there are 10 scans
    adxl_columns = [f'ADXL {i}' for i in range(30)]  # Assuming there are 10 scans

    # Dictionary to hold the filtered data columns for Radar and ADXL
    filtered_radar_columns = {}
    filtered_adxl_columns = {}

    # Add data for each scan to the filtered columns dictionary
    for i in range(10):  # Assuming there are 10 scans
        filtered_radar_columns[f'Radar {i}'] = df_combined_detrended[f'Radar {i}']
        filtered_adxl_columns[f'ADXL {i}'] = df_combined_detrended[f'ADXL {i}']

    # Apply the process function on each column
    if filter_type == 'Band Pass Filter (BPF)':
        filtered_radar_data_low = pd.DataFrame({col: process(filter_coef_low, data.values) for col, data in filtered_radar_columns.items()})
        filtered_radar_data = pd.DataFrame({col: process(filter_coef_high, data.values) for col, data in filtered_radar_data_low.items()})
        filtered_adxl_data_low = pd.DataFrame({col: process(filter_coef_low, data.values) for col, data in filtered_adxl_columns.items()})
        filtered_adxl_data = pd.DataFrame({col: process(filter_coef_high, data.values) for col, data in filtered_adxl_data_low.items()})
    else:
        filtered_radar_data = pd.DataFrame({col: process(filter_coef, data.values) for col, data in filtered_radar_columns.items()})
        filtered_adxl_data = pd.DataFrame({col: process(filter_coef, data.values) for col, data in filtered_adxl_columns.items()})

filtered_data = pd.concat([filtered_radar_data, filtered_adxl_data], axis=1)

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
    st.download_button("Download Filtered Data", filtered_excel_data, file_name=f"Filtered_{filter_type.replace(' ', '_')}_{frequency if filter_type != 'Band Pass Filter (BPF)' else f'{low_freq}to{high_freq}'}Hz.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-filtered-excel')

# Define functions for plotting time and frequency domain graphs
def plot_time_domain(data, column, sampling_rate=100):
    fig, ax = plt.subplots()
    time_seconds = np.arange(len(data)) / sampling_rate  # Assuming 100 signals per second
    ax.plot(time_seconds, data)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Signal')
    ax.set_title(f'{column} - Time Domain Plot')
    return fig

def plot_frequency_domain(data, column):
    frequencies, powers = fq(pd.DataFrame(data))
    powers_db = 10 * np.log10(powers[0])  # Convert power to dB scale
    fig, ax = plt.subplots()
    ax.plot(frequencies[0], powers_db)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power Spectrum (dB)')
    ax.set_title(f'{column} - Frequency Domain Plot')
    return fig

selected_domain = st.selectbox('Select Domain to Plot', ['Time Domain', 'Frequency Domain'])


# Loop through each Radar column and plot the selected domain
for column, data in filtered_radar_columns.items():
    if selected_domain == 'Time Domain':
        fig = plot_time_domain(data, column)
        st.pyplot(fig)
        plot_buffer = BytesIO()
        fig.savefig(plot_buffer, format='png')
        plot_buffer.seek(0)
        st.download_button(label=f'Download {column} Time Domain Plot', data=plot_buffer, file_name=f'{column}_time_domain_plot.png', mime='image/png')
    elif selected_domain == 'Frequency Domain':
        fig = plot_frequency_domain(data, column)
        st.pyplot(fig)
        plot_buffer = BytesIO()
        fig.savefig(plot_buffer, format='png')
        plot_buffer.seek(0)
        st.download_button(label=f'Download {column} Frequency Domain Plot', data=plot_buffer, file_name=f'{column}_frequency_domain_plot.png', mime='image/png')

# Loop through each ADXL column and plot the selected domain
for column, data in filtered_adxl_columns.items():
    if selected_domain == 'Time Domain':
        fig = plot_time_domain(data, column)
        st.pyplot(fig)
        plot_buffer = BytesIO()
        fig.savefig(plot_buffer, format='png')
        plot_buffer.seek(0)
        st.download_button(label=f'Download {column} Time Domain Plot', data=plot_buffer, file_name=f'{column}_time_domain_plot.png', mime='image/png')
    elif selected_domain == 'Frequency Domain':
        fig = plot_frequency_domain(data, column)
        st.pyplot(fig)
        plot_buffer = BytesIO()
        fig.savefig(plot_buffer, format='png')
        plot_buffer.seek(0)
        st.download_button(label=f'Download {column} Frequency Domain Plot', data=plot_buffer, file_name=f'{column}_frequency_domain_plot.png', mime='image/png')
