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
db = firestore.Client.from_service_account_json("testdata1-20ec5-firebase-adminsdk-an9r6-d15c118c96.json")

number_row = st.text_input('Enter Row number', '1')
number = st.text_input('Enter Tree number', '1')
 
# Create a reference to the Google post.
#doc_ref = db.collection("T1R1").select("ADXL Raw", "Radar Raw").stream()


doc_ref = db.collection("DevOps").stream()
i=1 
df = pd.DataFrame()
df2 = pd.DataFrame()
df3 = pd.DataFrame()
Axdf = pd.DataFrame()
Aydf = pd.DataFrame()
Azdf = pd.DataFrame()
TreeNos_list = []

query = db.collection('DevOps').where(filter=FieldFilter("RowNo", "==", int(number_row))).where(filter=FieldFilter("TreeNo", "==", int(number))).get()

for doc in query:
    adxl = doc.to_dict()['ADXLRaw']
    radar = doc.to_dict()['RadarRaw']
    Ax = doc.to_dict()['Ax']
    Ay = doc.to_dict()['Ay']
    Az = doc.to_dict()['Az']
    #true_labels = doc.to_dict()['InfStat']
    df['Radar '+str(i)] = pd.Series(radar)
    df2['ADXL '+str(i)] = pd.Series(adxl)
    Axdf['Ax '+str(i)] = pd.Series(Ax)
    Aydf['Ay '+str(i)] = pd.Series(Ay)
    Azdf['Az '+str(i)] = pd.Series(Az)
    TreeNos_list.append(doc.to_dict()['InfStat'])
    i+=1
    
 #   df['Radar'] = pd.DataFrame.from_dict(radar, orient='index');
 #   df['ADXL'] = pd.DataFrame.from_dict(adxl, orient='index');
#    i+=1
df = df.dropna()
df2 = df2.dropna()
Axdf = Axdf.dropna()
Aydf = Aydf.dropna()
Azdf = Azdf.dropna()

df = df[100:1800]
df2 = df2[100:1800]
Axdf = Axdf[100:1800]
Aydf = Aydf[100:1800]
Azdf = Azdf[100:1800]


#st.write(df);
st.write(df); 
st.write(df2); 
st.write(Axdf); 
st.write(Aydf); 
st.write(Azdf); 
st.write(TreeNos_list)

#TreeNos_list.to_numpy

@st.cache
def convert_df(df):
 return df.to_csv().encode('utf-8')
csv = convert_df(df)
csv2 = convert_df(df2)
csv3 = convert_df(Axdf)
csv4 = convert_df(Aydf)
csv5 = convert_df(Azdf)

st.download_button(
     "Press to Download Radar",
     csv,
     "Radar.csv",
     "text/csv",
     key='download-csvradar'
 )

st.download_button(
     "Press to Download ADXL",
     csv2,
     "ADXL.csv",
     "text/csv",
     key='download-csvadxl'
 )
st.download_button(
     "Press to Download Ax",
     csv3,
     "Ax.csv",
     "text/csv",
     key='download-csvax'
 )
st.download_button(
     "Press to Download Ay",
     csv4,
     "Ay.csv",
     "text/csv",
     key='download-csvay'
 )
st.download_button(
     "Press to Download Az",
     csv5,
     "Az.csv",
     "text/csv",
     key='download-csvaz'
 )
def stats_radar(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        std_list, ptp_list, mean_list, rms_list = [], [], [], []

        dfx= df[column]
        dfx = pd.DataFrame(dfx)
        dfx = dfx.dropna()
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
        result_df = pd.concat([result_df, column_result_df],axis=0)
    return result_df

def stats_adxl(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        std_list, ptp_list, mean_list, rms_list = [], [], [], []

        dfx= df[column]
        dfx = pd.DataFrame(dfx)
        dfx = dfx.dropna()
        std_value = np.std(df[column])
        ptp_value = np.ptp(df[column])
        mean_value = np.mean(df[column])
        rms_value = np.sqrt(np.mean(df[column]**2))

        std_list.append(std_value)
        ptp_list.append(ptp_value)
        mean_list.append(mean_value)
        rms_list.append(rms_value)


        column_result_df = pd.DataFrame({
        "adxl_STD": std_list,
        "adxl_PTP": ptp_list,
        "adxl_Mean": mean_list,
        "adxl_RMS": rms_list
        })
        result_df = pd.concat([result_df, column_result_df],axis=0)
    return result_df


def stats_ax(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        std_list, ptp_list, mean_list, rms_list = [], [], [], []

        dfx= df[column]
        dfx = pd.DataFrame(dfx)
        dfx = dfx.dropna()
        std_value = np.std(df[column])
        ptp_value = np.ptp(df[column])
        mean_value = np.mean(df[column])
        rms_value = np.sqrt(np.mean(df[column]**2))

        std_list.append(std_value)
        ptp_list.append(ptp_value)
        mean_list.append(mean_value)
        rms_list.append(rms_value)


        column_result_df = pd.DataFrame({
        "ax_STD": std_list,
        "ax_PTP": ptp_list,
        "ax_Mean": mean_list,
        "ax_RMS": rms_list
        })
        result_df = pd.concat([result_df, column_result_df],axis=0)
    return result_df

def stats_ay(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        std_list, ptp_list, mean_list, rms_list = [], [], [], []

        dfx= df[column]
        dfx = pd.DataFrame(dfx)
        dfx = dfx.dropna()
        std_value = np.std(df[column])
        ptp_value = np.ptp(df[column])
        mean_value = np.mean(df[column])
        rms_value = np.sqrt(np.mean(df[column]**2))

        std_list.append(std_value)
        ptp_list.append(ptp_value)
        mean_list.append(mean_value)
        rms_list.append(rms_value)


        column_result_df = pd.DataFrame({
        "ay_STD": std_list,
        "ay_PTP": ptp_list,
        "ay_Mean": mean_list,
        "ay_RMS": rms_list
        })
        result_df = pd.concat([result_df, column_result_df],axis=0)
    return result_df

def stats_az(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        std_list, ptp_list, mean_list, rms_list = [], [], [], []

        dfx= df[column]
        dfx = pd.DataFrame(dfx)
        dfx = dfx.dropna()
        std_value = np.std(df[column])
        ptp_value = np.ptp(df[column])
        mean_value = np.mean(df[column])
        rms_value = np.sqrt(np.mean(df[column]**2))

        std_list.append(std_value)
        ptp_list.append(ptp_value)
        mean_list.append(mean_value)
        rms_list.append(rms_value)


        column_result_df = pd.DataFrame({
        "az_STD": std_list,
        "az_PTP": ptp_list,
        "az_Mean": mean_list,
        "az_RMS": rms_list
        })
        result_df = pd.concat([result_df, column_result_df],axis=0)
    return result_df

def detrend(dataframe):
    detrended_data = dataframe-dataframe.mean()
    #normalized_data = (detrended_data - detrended_data.min()) / (detrended_data.max() - detrended_data.min())
    return (detrended_data)

def preprocess(radar,adxl,ax,ay,az):
  radar_stats =stats_radar(radar)
  adxl_stats =stats_adxl(adxl)
  ax_stats =stats_ax(ax)
  ay_stats =stats_ay(ay)
  az_stats =stats_az(az)
  radar_detrend = detrend(radar)
  adxl_detrend = detrend(adxl)
  ax_detrend = detrend(ax)
  ay_detrend = detrend(ay)
  az_detrend = detrend(az)
  radar_detrend_stats = stats_radar(radar_detrend)
  adxl_detrend_stats = stats_adxl(adxl_detrend)
  ax_detrend_stats = stats_ax(ax_detrend)
  ay_detrend_stats = stats_ay(ay_detrend)
  az_detrend_stats = stats_az(az_detrend)

  return(radar_stats,adxl_stats,ax_stats,ay_stats,az_stats,radar_detrend,adxl_detrend,ax_detrend,ay_detrend,az_detrend,radar_detrend_stats,adxl_detrend_stats,ax_detrend_stats,ay_detrend_stats,az_detrend_stats)

radar_stats,adxl_stats,ax_stats,ay_stats,az_stats,radar_detrend,adxl_detrend,ax_detrend,ay_detrend,az_detrend,radar_detrend_stats,adxl_detrend_stats,ax_detrend_stats,ay_detrend_stats,az_detrend_stats = preprocess(df,df2,Axdf,Aydf,Azdf) 
stats = pd.concat([radar_stats,adxl_stats,ax_stats,ay_stats,az_stats],axis=1)
detrend_stats = pd.concat([radar_detrend_stats,adxl_detrend_stats,ax_detrend_stats,ay_detrend_stats,az_detrend_stats],axis=1)


if st.button("Run all models"):
 result_model1,result_model2 = predict(stats,detrend_stats)
 st.text(result_model1)
 st.text(result_model2)   
# st.text(result_model2)
 #st.text(result_model3)
 #st.text(result_clf_norm_stat)
 model1_accuracy = accuracy_score(TreeNos_list,result_model1)
 st.write("model1 Accuracy = "+str(model1_accuracy*100)+"%")
 model2_accuracy = accuracy_score(TreeNos_list,result_model2)
 st.write("model2 Accuracy = "+str(model2_accuracy*100)+"%")
# model3_accuracy = accuracy_score(TreeNos_list,result_model3)
 #st.write("result_clf_norm_p Accuracy = "+str(model3_accuracy*100)+"%")
 #result_clf_norm_stat_accuracy = accuracy_score(TreeNos_list,result_clf_norm_stat)
 #st.write("result_clf_norm_stat Accuracy = "+str(result_clf_norm_stat_accuracy*100)+"%")
 #st.write(df_freqnstat,df_freq_trans,df_norm_p_trans,df_norm_stat)
