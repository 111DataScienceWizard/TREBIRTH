import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter
from io import BytesIO
from datetime import datetime

# Define detrend function
def detrend(dataframe):
    detrended_data = dataframe - dataframe.mean()
    return detrended_data

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
selected_sheets = st.multiselect('Select Sheets', ['Raw Data', 'Detrended Data', 'Normalized Data', 'Detrended & Normalized Data', 'Metadata'], default=['Raw Data', 'Metadata'])

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

    # Change column names according to the scan number
    df_combined_normalized.columns = [f"{col}{scan_number}" for col in df_combined_normalized.columns]

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

    # Append timestamp to ensure uniqueness
    timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{file_name}_{timestamp_str}.xlsx"

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

    excel_data.seek(0)

    # Download button for selected sheets and metadata
    st.download_button("Download Selected Sheets and Metadata", excel_data, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excel')
