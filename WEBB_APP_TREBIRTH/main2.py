import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter
from io import BytesIO
from datetime import datetime
import numpy as np
from scipy import signal
from scipy.stats import skew, kurtosis
from filters import coefLPF5Hz, coefLPF10Hz, coefLPF15Hz, coefLPF20Hz, coefLPF25Hz, coefLPF30Hz, coefLPF35Hz, coefLPF40Hz, coefLPF45Hz, coefLPF50Hz, coefHPF5Hz, coefHPF10Hz, coefHPF15Hz, coefHPF20Hz, coefHPF25Hz, coefHPF30Hz, coefHPF35Hz, coefHPF40Hz, coefHPF45Hz, coefHPF50Hz    

# Define detrend function
def detrend(dataframe):
    detrended_data = dataframe - dataframe.mean()
    return detrended_data

# Define feature extraction functions
def fq(df):
    frequencies = []
    powers = []

    for i in df:
        f, p = signal.welch(df[i], 100, 'flattop', 1024, scaling='spectrum')
        frequencies.append(f)
        powers.append(p)

    frequencies = pd.DataFrame(frequencies)
    powers = pd.DataFrame(powers)
    return frequencies, powers

def stats_radar(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        std_list, ptp_list, mean_list, rms_list = [], [], [], []

        std_value = np.std(df[column])
        ptp_value = np.ptp(df[column])
        mean_value = np.mean(df[column])
        rms_value = np.sqrt(np.mean(df[column]**2))

        std_list.append(std_value)
        ptp_list.append(ptp_value)
        mean_list.append(mean_value)
        rms_list.append(rms_value)

        column_result_df = pd.DataFrame({
            "STD": std_list,
            "PTP": ptp_list,
            "Mean": mean_list,
            "RMS": rms_list
        })
        result_df = pd.concat([result_df, column_result_df], axis=0)
    return result_df

# Define function to compare columns
def columns_reports_unique(df):
    report = []
    num_columns = len(df.columns)
    for i in range(num_columns):
        for j in range(i + 1, num_columns):  # Start j from i + 1
            column1 = df.columns[i]
            column2 = df.columns[j]
            diff = df[column1] - df[column2]
            mean_diff = np.mean(diff)
            deviation_diff = np.std(diff)
            ptp_diff = np.ptp(diff)
            skewness_diff = skew(diff)
            correlation = df[[column1, column2]].corr().iloc[0, 1]
            report.append({
                'Column 1': column1,
                'Column 2': column2,
                'Mean Difference': mean_diff,
                'Deviation Difference': deviation_diff,
                'PTP Difference': ptp_diff,
                'Skewness Difference': skewness_diff,
                'Correlation': correlation,
            })
    report_df = pd.DataFrame(report)
    return report_df

# Define filtering functions
def process(coef, in_signal):
    FILTERTAPS = len(coef)
    values = in_signal[:FILTERTAPS].copy()
    k = 0
    out_signal = []
    gain = 1.0
    for in_value in in_signal:
        out = 0.0
        values[k] = in_value
        for i in range(len(coef)):
            out += coef[i] * values[(i + k) % FILTERTAPS]
        out /= gain
        k = (k + 1) % FILTERTAPS
        out_signal.append(out)
    return out_signal

def allfiltering(input_signal):
    LPF_outputs = {}
    HPF_outputs = {}

    LPF_outputs['LPF5Hz'] = process(coefLPF5Hz, input_signal)
    LPF_outputs['LPF10Hz'] = process(coefLPF10Hz, input_signal)
    LPF_outputs['LPF15Hz'] = process(coefLPF15Hz, input_signal)
    LPF_outputs['LPF20Hz'] = process(coefLPF20Hz, input_signal)
    LPF_outputs['LPF25Hz'] = process(coefLPF25Hz, input_signal)
    LPF_outputs['LPF30Hz'] = process(coefLPF30Hz, input_signal)
    LPF_outputs['LPF35Hz'] = process(coefLPF35Hz, input_signal)
    LPF_outputs['LPF40Hz'] = process(coefLPF40Hz, input_signal)
    LPF_outputs['LPF45Hz'] = process(coefLPF45Hz, input_signal)
    LPF_outputs['LPF50Hz'] = process(coefLPF50Hz, input_signal)

    HPF_outputs['HPF5Hz'] = process(coefHPF5Hz, input_signal)
    HPF_outputs['HPF10Hz'] = process(coefHPF10Hz, input_signal)
    HPF_outputs['HPF15Hz'] = process(coefHPF15Hz, input_signal)
    HPF_outputs['HPF20Hz'] = process(coefHPF20Hz, input_signal)
    HPF_outputs['HPF25Hz'] = process(coefHPF25Hz, input_signal)
    HPF_outputs['HPF30Hz'] = process(coefHPF30Hz, input_signal)
    HPF_outputs['HPF35Hz'] = process(coefHPF35Hz, input_signal)
    HPF_outputs['HPF40Hz'] = process(coefHPF40Hz, input_signal)
    HPF_outputs['HPF45Hz'] = process(coefHPF45Hz, input_signal)
    HPF_outputs['HPF50Hz'] = process(coefHPF50Hz, input_signal)

    all_outputs = pd.DataFrame({**LPF_outputs, **HPF_outputs})
    return all_outputs

def apply_allfiltering_to_columns(df):
    output_dfs = []
    for column in df.columns:
        input_signal = df[column]
        filtered_output = allfiltering(input_signal)
        filtered_output.columns = [f"{column}_{col}" for col in filtered_output.columns]
        output_dfs.append(filtered_output)
    return pd.concat(output_dfs, axis=1)

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

# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("Web_App_Trebirth/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# User input for Row No., Tree No., Scan No., and Label
row_number = st.text_input('Enter Row number', 'All')
tree_number = st.text_input('Enter Tree number', 'All')
scan_number = st.text_input('Enter Scan number', 'All')

# Dropdown for InfStat label selection
label_infstat = st.selectbox('Select Label', ['All', 'Infected', 'Healthy'], index=0)

# Dropdown for selecting sheets in Excel
selected_sheets = st.multiselect('Select Sheets', ['Raw Data', 'Detrended Data', 'Normalized Data', 'Detrended & Normalized Data', 'Metadata', 'Time Domain Features', 'Frequency Domain Features', 'Column Comparison', 'Filtered Data'], default=['Raw Data', 'Metadata'])

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
query = query.get()

if len(query) == 0:
    st.write("No data found matching the specified criteria.")
else:
    # Create empty lists to store data
    radar_data = []
    adxl_data = []
    ax_data = []
    ay_data = []
    az_data = []
    metadata_list = []

    for doc in query:
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

    # Create separate DataFrames for Radar, ADXL, Ax, Ay, Az data
    df_radar = pd.DataFrame(radar_data).transpose().add_prefix('Radar ')
    df_adxl = pd.DataFrame(adxl_data).transpose().add_prefix('ADXL ')
    df_ax = pd.DataFrame(ax_data).transpose().add_prefix('Ax ')
    df_ay = pd.DataFrame(ay_data).transpose().add_prefix('Ay ')
    df_az = pd.DataFrame(az_data).transpose().add_prefix('Az ')

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
            # Combine detrended and normalized data
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
        if 'Column Comparison' in selected_sheets:  # Add new sheet for column comparison
            df_comparison = columns_reports_unique(df_combined_detrended)
            df_comparison.to_excel(writer, sheet_name='Column Comparison', index=False)
        if 'Filtered Data' in selected_sheets:  # Add new sheet for filtered data
            df_filtered.to_excel(writer, sheet_name='Filtered Data', index=False)
            df_filtered = apply_allfiltering_to_columns(df_combined_detrended)

    excel_data.seek(0)

    # Download button for selected sheets and metadata
    st.download_button("Download Selected Sheets and Metadata", excel_data, file_name=f"{file_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excel')
