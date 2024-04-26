import streamlit as st
import numpy as np
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter

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

number_row = st.text_input('Enter Row number', '1')
number = st.text_input('Enter Tree number', '1')

# Create a reference to the Google post.
query = db.collection('DevOps').where(filter=FieldFilter("RowNo", "==", int(number_row))).where(filter=FieldFilter("TreeNo", "==", int(number))).get()

# Create dataframes to store the data
df_radar = pd.DataFrame()
df_adxl = pd.DataFrame()
df_ax = pd.DataFrame()
df_ay = pd.DataFrame()
df_az = pd.DataFrame()
TreeNos_list = []

for i, doc in enumerate(query):
    adxl = doc.to_dict().get('ADXLRaw', [])
    radar = doc.to_dict().get('RadarRaw', [])
    Ax = doc.to_dict().get('Ax', [])
    Ay = doc.to_dict().get('Ay', [])
    Az = doc.to_dict().get('Az', [])
    
    df_radar['Radar '+str(i)] = radar
    df_adxl['ADXL '+str(i)] = adxl
    df_ax['Ax '+str(i)] = Ax
    df_ay['Ay '+str(i)] = Ay
    df_az['Az '+str(i)] = Az
    TreeNos_list.append(doc.to_dict().get('InfStat', 'Unknown'))

# Filter out NaN values and select the desired range
df_radar = df_radar.dropna()[100:1800]
df_adxl = df_adxl.dropna()[100:1800]
df_ax = df_ax.dropna()[100:1800]
df_ay = df_ay.dropna()[100:1800]
df_az = df_az.dropna()[100:1800]

# Write data to Excel file
excel_file_path = "Combined_Data.xlsx"
with pd.ExcelWriter(excel_file_path, engine='xlsxwriter', mode='w') as writer:
    df_radar.to_excel(writer, sheet_name='Radar', index=False)
    df_adxl.to_excel(writer, sheet_name='ADXL', index=False)
    df_ax.to_excel(writer, sheet_name='Ax', index=False)
    df_ay.to_excel(writer, sheet_name='Ay', index=False)
    df_az.to_excel(writer, sheet_name='Az', index=False)

# Provide download button for the Excel file
st.download_button(
    "Download Combined Data",
    excel_file_path,
    "Combined_Data.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key='download-excel'
)
