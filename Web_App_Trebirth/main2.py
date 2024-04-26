import streamlit as st
from google.cloud import firestore
import pandas as pd
import xlsxwriter
import tempfile
from datetime import datetime

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
label_infstat = st.text_input('Enter InfStat label', 'All')

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

    st.write(df_combined)

    # Create a temporary file for Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
        temp_file_name = temp_file.name

        # Write data to Excel file
        with pd.ExcelWriter(temp_file_name, engine='xlsxwriter') as writer:
            # Write combined data to first sheet
            df_combined.to_excel(writer, sheet_name='Raw Data', index=False)

            # Metadata extraction
            for doc in query:
                metadata = doc.to_dict()
                # Convert datetime values to timezone-unaware
                for key, value in metadata.items():
                    if isinstance(value, datetime):
                        metadata[key] = value.replace(tzinfo=None)
                metadata_list.append(metadata)

            # Convert list of dictionaries to DataFrame
            df_metadata = pd.DataFrame(metadata_list)

            # Select only the desired columns
            desired_columns = ['TreeSec', 'TreeNo', 'InfStat', 'TreeID', 'RowNo', 'ScanNo', 'timestamp']
            df_metadata_filtered = df_metadata[desired_columns]

            # Write metadata to second sheet
            df_metadata_filtered.to_excel(writer, sheet_name='Metadata', index=False)

    # Download button for combined data and metadata
    st.download_button("Download Combined Data and Metadata", temp_file_name, "Combined_Data_Metadata.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excel')
