import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter
from io import BytesIO
import sys
import xlsxwriter

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

radar_data = []
adxl_data = []

for doc in query:
    radar_data.append(doc.to_dict()['RadarRaw'])
    adxl_data.append(doc.to_dict()['ADXLRaw'])

# Create separate DataFrames for Radar and ADXL data
df_radar = pd.DataFrame(radar_data).transpose().add_prefix('Radar ')
df_adxl = pd.DataFrame(adxl_data).transpose().add_prefix('ADXL ')

# Concatenate the DataFrames column-wise
df_combined = pd.concat([df_radar, df_adxl], axis=1)

# Slice the DataFrame to the desired range
df_combined = df_combined[100:1800]

st.write(df_combined)

@st.cache
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

csv_combined = convert_df_to_csv(df_combined)

st.download_button("Download Combined Radar and ADXL Data", csv_combined, "Combined_Data.csv", "text/csv", key='download-csvcombined')

# Metadata extraction
metadata_list = []

# Iterate over documents and extract metadata
for doc in query:
    metadata = doc.to_dict()
    # Convert datetime values to timezone-unaware
    for key, value in metadata.items():
        if isinstance(value, datetime):
            metadata[key] = value.replace(tzinfo=None)
    metadata_list.append(metadata)

# Convert list of dictionaries to DataFrame
df_metadata = pd.DataFrame(metadata_list)

# Convert DataFrame to Excel format
excel_data = BytesIO()
with pd.ExcelWriter(excel_data, engine='xlsxwriter', mode='w') as writer:
    df_metadata.to_excel(writer, index=False)

# Get the bytes of the Excel data
excel_bytes = excel_data.getvalue()

# Download button for metadata
st.download_button("Download Metadata", excel_bytes, "Metadata.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excelmetadata')
