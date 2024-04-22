import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.cloud.firestore import FieldFilter
from io import BytesIO

# Set page configuration
st.set_page_config(layout="wide")
st.title('Data Analytics')

# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("Web_App_Trebirth/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Input fields for row number and tree number
number_row = st.text_input('Enter Row number', '1')
number = st.text_input('Enter Tree number', '1')

# Retrieve data from Firestore based on row and tree number
query = db.collection('DevOps').where(filter=FieldFilter("RowNo", "==", int(number_row))).where(filter=FieldFilter("TreeNo", "==", int(number))).get()

# DataFrames to store metadata
df_metadata = pd.DataFrame(columns=['Key', 'Value'])

# Iterate over documents and extract metadata
for doc in query:
    metadata = doc.to_dict()
    for key, value in metadata.items():
        df_metadata = pd.concat([df_metadata, pd.DataFrame({'Key': [key], 'Value': [value]})], ignore_index=True)

# Convert DataFrame to Excel format
excel_data = BytesIO()
with pd.ExcelWriter(excel_data, engine='xlsxwriter', mode='w') as writer:
    df_metadata.to_excel(writer, index=False)

# Get the bytes of the Excel data
excel_bytes = excel_data.getvalue()

# Download button for metadata
st.download_button("Download Metadata", excel_bytes, "Metadata.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excelmetadata')
