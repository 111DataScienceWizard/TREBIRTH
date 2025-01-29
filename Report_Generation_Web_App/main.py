import streamlit as st
import numpy as np
import google.cloud
from firebase_admin import firestore
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pydeck as pdk
import calendar
from PIL import Image
from google.cloud.firestore import FieldFilter
import datetime
import json



st.set_page_config(layout="wide")


# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("testdata1-20ec5-firebase-adminsdk-an9r6-d15c118c96.json")
#key_dict = json.loads(st.secrets["textkey"])
#creds = service_account.Credentials.from_service_account_info(key_dict)
#db = firestore.Client(credentials=creds, project="TestData1")
 
# Create a reference to the all the docs 
#docs_ref = db.collection("DevMode").stream()
i=1 
df = pd.DataFrame()
TreeNos_list = []
#for doc in docs_ref:
    #TreeNos_list.append(doc.to_dict()['TreeNo'])
   # timestamp = doc.to_dict()['timestamp']

query = db.collection('Mr.Arjun').where(filter=FieldFilter("RowNo", "==", 1)).get()

for doc in query: 
    TreeNos_list.append(doc.to_dict()['TreeNo'])
    timestamp = doc.to_dict()['timestamp']


#date = docs_ref[0].to_dict()['timestamp']
#year,month,day = timestamp.year,timestamp.month,timestamp.day
Total_trees = np.max(np.array(TreeNos_list)); 
#st.write(timestamp.weekday());
field_filter2 = FieldFilter("InfStat", "==", 'Infected');

count = 1;
no_inf = 0; 

while (count <= Total_trees):
    query = db.collection('Mr.Arjun').where(filter=FieldFilter("RowNo", "==", 1)).where(filter=FieldFilter("TreeNo", "==", count)).where(filter=field_filter2);
    count_query=query.count().get(); 
    nb_docs=count_query[0][0].value;
    count+=1 
    if nb_docs > 0: 
        no_inf+=1
     

Inf_per = (no_inf/Total_trees)*100; 
no_healthy = Total_trees - no_inf; 


#date = datetime.datetime.fromtimestamp(timestamp.seconds)
#dayOfWeek = date.weekday()
#st.write(dayOfWeek);
    #result = TreeNos.items()
    #data = list(result)
    #npTrees = np.array(data)

#st.write(np.max(npTrees));  

st.markdown("""

<style>
    [data-testid=stSidebar] {
        background-color: #1b1a28;
    }
</style>

 """, 
unsafe_allow_html=True)

image = Image.open('Farmer face in a circle.png')
new_image = image.resize((200, 200))

st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #1b1a28;
    }
</style>
 """, unsafe_allow_html=True)

st.markdown(
    """
    <style>
        [data-testid=stSidebar] [data-testid=stImage]{
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True
)

st.sidebar.image(new_image)

st.sidebar.markdown("<h1 style='text-align: center; color: white;font-size: 32px;'>Ramesh Kapare  </h1>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: white;font-size: 25px;'>Niphad Farm </h2>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #247370;font-size: 19px;'>Plot number 1 </h2>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #1a5361;font-size: 19px'>Plot number 2 </h2>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #1a5361;font-size: 19px'>Plot number 3 </h2>", unsafe_allow_html=True)
#st.sidebar.markdown("<h2 style='text-align: center; color: white;font-size: 25px;'>Pimpalgaon Farm </h2>", unsafe_allow_html=True)
#st.sidebar.markdown("<h2 style='text-align: center; color: #31458a;font-size: 19px'>Plot number 3 </h2>", unsafe_allow_html=True)
#st.sidebar.markdown("<h2 style='text-align: center; color: #738fd9;font-size: 19px'>Plot number 4 </h2>", unsafe_allow_html=True)
# Convert the calendar data into a printable format
cal_rows = [['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']]
cal = calendar.monthcalendar(2024, 3)
for week in cal:
 cal_rows.append([str(day) if day != 0 else '' for day in week])
 
df = pd.DataFrame(cal_rows)
new_header = df.iloc[0] #grab the first row for the header
df = df[1:] #take the data less the header row
df.columns = new_header #set the header row as the df header
#Display the calendar using Streamlit components
st.sidebar.dataframe(df,hide_index = True,width=500)
def v_spacer(height, sb=False) -> None:
    for _ in range(height):
        if sb:
            st.sidebar.write('\n')
        else:
            st.write('\n')
#st.write(cal_rows)
#st.dataframe(df)
#st.dataframe(df.style.hide(axis="index"))
#st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)


col1, col2 = st.columns([2,2])

with col1:
 st.title('Farm Analytics')
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
 #st.write(timestamp)   
 option = st.selectbox("Historical Analysis(Select timeframe):", ["1 Week Data", "This Month's Data", "6 Months Data"])
 #st.write(timestamp.weekday())   

 if option == "1 Week Data":
    fig = go.Figure()
    plot3_y = [0,0,0,0,0,0]
    plot3_y[timestamp.weekday()] = Inf_per; 
    fig.add_trace(go.Scatter(x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri','Sat'], y=[20, 40, 25, 15,10,40], fill='tozeroy',mode='none',name='Plot 1',line_shape='spline')) # fill down to xaxis
    fig.add_trace(go.Scatter(x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri','Sat'], y=[10, 15, 20, 35,28,15], fill='tonexty',mode='none',name='Plot 2',line_shape='spline'))
    fig.add_trace(go.Scatter(x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri','Sat'], y=plot3_y, fill='tozeroy',mode='none',name='Plot 3',line_shape='spline'))# fill to trace0 y
    fig.update_traces()
    fig.update_layout(
       title="1 Week Data",
       xaxis_title="Day",
       yaxis_title="Percentage Infestation",
       width=800,
       height=450,
     )
    fig.update_layout({
    'plot_bgcolor': 'rgb(27, 26, 40)',
    'paper_bgcolor': 'rgb(27, 26, 40)',
    })
    st.plotly_chart(fig,use_container_width=True)
 

 elif option == "This Month's Data":
    st.write('This Months Data')
    
 elif option == "6 Months Data": 
     fig = go.Figure()
     fig.add_trace(go.Scatter(x=['Jan', 'Feb', 'March', 'April', 'May','June'], y=[20, 40, 25, 15,10,40], fill='tozeroy',mode='none',name='Plot 1',line_shape='spline')) # fill down to xaxis
     fig.add_trace(go.Scatter(x=['Jan', 'Feb', 'March', 'April', 'May','June'], y=[10, 15, 20, 35,28,15], fill='tonexty',mode='none',name='Plot 2',line_shape='spline')) # fill to trace0 y
     fig.update_layout(
       title="6 Months Data",
       xaxis_title="Month",
       yaxis_title="Percentage Infestation",
       width=800,
       height=450,
      )
     fig.update_layout({
     'plot_bgcolor': 'rgb(27, 26, 40)',
     'paper_bgcolor': 'rgb(27, 26, 40)',
     })
     st.plotly_chart(fig,use_container_width=True)
 
 #st.image('Scans_Image.jpg',width=620)
 Plots=['Plot 1', 'Plot 2', 'Plot 3']
 fig3 = go.Figure(data=[
    go.Bar(name='Healthy', x=Plots, y=[60, 70,no_healthy],marker_color='#3488a0'),
    go.Bar(name='Infected', x=Plots, y=[50, 25,no_inf],marker_color='#773871'),
    #go.Bar(name='Suspicious', x=Plots, y=[120, 180,10],marker_color='#25d9c4')
 ])
 fig3.update_layout(barmode='group',width=800,
    height=530,title='Comparative Analysis')
 fig3.update_layout({
  'plot_bgcolor': 'rgb(27, 26, 40)',
  'paper_bgcolor': 'rgb(27, 26, 40)',
 })
 st.plotly_chart(fig3,use_container_width=True)


with col2:
 st.markdown('##')
 st.markdown('##')
 st.markdown('##')
 st.markdown('##')
 st.markdown('##')
 st.markdown('##')
 #st.markdown('##')
 #st.markdown('##')
#st.markdown('##')
 #st.markdown('##')
 #st.markdown('##')


 image2 = Image.open("Frame_4_2.jpg")
 new_image2 = image2.resize((800, 500))
 st.image(new_image2);


 
 chart_data = pd.DataFrame(
   np.random.randn(5, 1) / [60, 60] + [20.079966, 74.109314],
   columns=['lat', 'lon'])
 #st.markdown("<h2 style='text-align: left; color: white;font-size: 18px'>Overview </h2>", unsafe_allow_html=True)
 st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/satellite-streets-v12',
    initial_view_state=pdk.ViewState(
        latitude=20.079966,
        longitude=74.109314,
        zoom=13,
        pitch=50,
        height=430, width=600,
    ),
    layers=[
     pdk.Layer(
            "ScreenGridLayer",
            data=chart_data,
            get_position='[lon, lat]',
            get_color='[100, 30, 0, 160]',
            pickable=False,
            opacity=0.8,
            cell_size_pixels=20,
    #        color_range=[
    #         [0, 25, 0, 25],
     #        [0, 85, 0, 85],
     #        [0, 127, 0, 127],
     #        [0, 170, 0, 170],
     #        [0, 190, 0, 190],
     #        [0, 255, 0, 255],
      #        ],
         ),
    ],
  ))
