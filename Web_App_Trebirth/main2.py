import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter
from io import BytesIO
import xlsxwriter
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
label = st.text_input('Enter Label', 'All')

# Create a reference to the Google post.
query = db.collection('DevOps')

# Filter based on user input
if row_number != 'All':
    query = query.where('RowNo', '==', int(row_number))
if tree_number != 'All':
    query = query.where('TreeNo', '==', int(tree_number))
if scan_number != 'All':
    query = query.where('ScanNo', '==', int(scan_number))
if label != 'All':
    query = query.where('InfStat', '==', label)

# Get documents based on the query
query = query.get()

# Create empty lists to store data
radar_data = []
adxl_data = []
ax_data = []
ay_data = []
az_data = []
metadata_list = []

for doc in query:
    radar_data.append(doc.to_dict()['RadarRaw'])
    adxl_data.append(doc.to_dict()['ADXLRaw'])
    ax_data.append(doc.to_dict()['Ax'])
    ay_data.append(doc.to_dict()['Ay'])
    az_data.append(doc.to_dict()['Az'])
    metadata = doc.to_dict()
    # Convert datetime values to timezone-unaware
    for key, value in metadata.items():
        if isinstance(value, datetime):
            metadata[key] = value.replace(tzinfo=None)
    metadata_list.append(metadata)

# Create DataFrame for radar, ADXL, Ax, Ay, Az data
df_radar = pd.DataFrame(radar_data).transpose().add_prefix('Radar ')
df_adxl = pd.DataFrame(adxl_data).transpose().add_prefix('ADXL ')
df_ax = pd.DataFrame(ax_data).transpose().add_prefix('Ax ')
df_ay = pd.DataFrame(ay_data).transpose().add_prefix('Ay ')
df_az = pd.DataFrame(az_data).transpose().add_prefix('Az ')

# Concatenate the DataFrames column-wise
df_combined = pd.concat([df_radar, df_adxl, df_ax, df_ay, df_az], axis=1)

# Create DataFrame for metadata
df_metadata = pd.DataFrame(metadata_list)

# Excel file creation
excel_data = BytesIO()

# Write data to Excel file
with pd.ExcelWriter(excel_data, engine='xlsxwriter', mode='w') as writer:
    # Write combined data to first sheet
    df_combined.to_excel(writer, sheet_name='Raw Data', index=False)
    # Write metadata to second sheet
    df_metadata.to_excel(writer, sheet_name='Metadata', index=False)

# Get the bytes of the Excel data
excel_bytes = excel_data.getvalue()

# Download button for combined data and metadata
st.download_button("Download Combined Data and Metadata", excel_bytes, "Combined_Data_Metadata.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excel')
