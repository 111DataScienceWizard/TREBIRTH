import streamlit as st
import numpy as np
import google.cloud
from google.cloud import firestore
import pandas as pd
import joblib
from prediction import predict
#from google.cloud import FieldFilter
from google.cloud.firestore import FieldFilter
#from google.cloud.firestore.types import FieldFilter
from sklearn.metrics import accuracy_score, classification_report
from scipy import signal
from sklearn.preprocessing import MinMaxScaler


st.set_page_config(layout="wide")
st.title('Data Analytics')
st.markdown(
    """
    <style>
    .reportview-container {{
        background-color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True,
  )

# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("Web_App_Trebirth/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

number_row = st.text_input('Enter Row number', '1')
number = st.text_input('Enter Tree number', '1')
 
# Create a reference to the Google post.
#doc_ref = db.collection("T1R1").select("ADXL Raw", "Radar Raw").stream()


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
def convert_df(df):
    return df.to_csv().encode('utf-8')

csv_combined = convert_df(df_combined)

st.download_button("Download Combined Radar and ADXL Data", csv_combined, "Combined_Data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-csvcombined')
