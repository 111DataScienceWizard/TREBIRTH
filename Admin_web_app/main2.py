import streamlit as st
import numpy as np
import google.cloud
from firebase_admin import firestore
import plotly.graph_objects as go
import pandas as pd
import pydeck as pdk
import calendar
from PIL import Image
import base64
from io import BytesIO
from google.cloud.firestore import FieldFilter
import random


st.set_page_config(layout="wide")

# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Define your Firestore query and data extraction logic
i = 1 
df = pd.DataFrame()
TreeNos_list = []
query = db.collection('Mr.Arjun').where(filter=FieldFilter("RowNo", "==", 1)).get()

for doc in query: 
    TreeNos_list.append(doc.to_dict()['TreeNo'])
    timestamp = doc.to_dict()['timestamp']

Total_trees = np.max(np.array(TreeNos_list))
field_filter2 = FieldFilter("InfStat", "==", 'Infected')

count = 1
no_inf = 0
while (count <= Total_trees):
    query = db.collection('Mr.Arjun').where(filter=FieldFilter("RowNo", "==", 1)).where(filter=FieldFilter("TreeNo", "==", count)).where(filter=field_filter2)
    count_query = query.count().get()
    nb_docs = count_query[0][0].value
    count += 1
    if nb_docs > 0: 
        no_inf += 1

Inf_per = (no_inf / Total_trees) * 100
no_healthy = Total_trees - no_inf

# Sidebar customization
image = Image.open('Admin_web_app/Farmer face in a circle.png')
new_image = image.resize((200, 200))

buffer = BytesIO()
new_image.save(buffer, format="PNG")
img_str = base64.b64encode(buffer.getvalue()).decode()
# Display the centered image and text in the sidebar
st.sidebar.markdown(
    f"""
    <div style="text-align: center;">
        <img src="data:image/png;base64,{img_str}" width="200" height="200" style="border-radius:50%;"/>
    </div>
    """, unsafe_allow_html=True
)

#st.sidebar.image(new_image)
st.sidebar.markdown("<h1 style='text-align: center; color: white;font-size: 32px;'>Ramesh Kapare</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: white;font-size: 25px;'>Niphad Farm</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #247370;font-size: 19px;'>Plot number 1</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #1a5361;font-size: 19px'>Plot number 2 </h2>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #1a5361;font-size: 19px'>Plot number 3 </h2>", unsafe_allow_html=True)

st.markdown('#')
# Calendar
cal_rows = [['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']]
cal = calendar.monthcalendar(2024, 3)

# Find valid days that are not Sunday
valid_dates = [day for week in cal for day in week[:-1] if day != 0]  # Ignore Sundays (last element in each week)

# Select 5 consecutive random dates, avoiding Sundays
start_day = random.choice(valid_dates[:-4])  # Ensure we can pick 5 consecutive dates
random_dates = [start_day + i for i in range(5) if (start_day + i) in valid_dates]

# Build calendar rows with highlighted dates
for week in cal:
    cal_rows.append([day if day != 0 else '' for day in week])

# Convert calendar rows to a DataFrame
df = pd.DataFrame(cal_rows)
df.columns = df.iloc[0]
df = df[1:]

def highlight_random_dates(val):
    if val in random_dates:
        return 'background-color: lightblue; color: black; padding: 5px; font-weight: bold; border-radius: 10px;'
    return ''
# Apply styling to the DataFrame
styled_df = df.style.applymap(highlight_random_dates)
st.sidebar.write("Calendar to schedule farm visit:")
# Display the styled DataFrame in the sidebar
st.sidebar.dataframe(styled_df, hide_index=True, width=500)

# Function to add vertical spacing
def v_spacer(height, sb=False) -> None:
    for _ in range(height):
        if sb:
            st.sidebar.write('\n')
        else:
            st.write('\n')

# Example of using the v_spacer function to create space below the calendar
v_spacer(2, sb=True)  # Adds 2 newlines worth of space in the sidebar

# Creating the layout with columns
col1, col2 = st.columns([3, 2])

with col1:
    st.title('Farm Analytics')

    # Dropdown for historical analysis
    option = st.selectbox("Historical Analysis (Select timeframe):", ["1 Week Data", "This Month's Data", "6 Months Data"])

    # Conditional plot based on option selection
    if option == "1 Week Data":
        fig = go.Figure()
        plot3_y = [0, 0, 0, 0, 0, 0]
        plot3_y[timestamp.weekday()] = Inf_per
        fig.add_trace(go.Scatter(x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], y=plot3_y, fill='tozeroy', name='Plot 3', line_shape='spline'))
        fig.update_layout(
            title="1 Week Data",
            xaxis_title="Day",
            yaxis_title="Percentage Infestation",
            width=800,
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

    elif option == "6 Months Data":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=['Jan', 'Feb', 'March', 'April', 'May', 'June'], y=[20, 40, 25, 15, 10, 40], fill='tozeroy', line_shape='spline'))
        fig.update_layout(
            title="6 Months Data",
            xaxis_title="Month",
            yaxis_title="Percentage Infestation",
            width=800,
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

    # Comparative Analysis bar chart
    fig3 = go.Figure(data=[
        go.Bar(name='Healthy', x=['Plot 1', 'Plot 2', 'Plot 3'], y=[60, 70, no_healthy], marker_color='#3488a0'),
        go.Bar(name='Infected', x=['Plot 1', 'Plot 2', 'Plot 3'], y=[50, 25, no_inf], marker_color='#773871')
    ])
    fig3.update_layout(
        barmode='group',
        title="Comparative Analysis",
        width=800,
        height=530
    )
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    # Image and Map
    st.markdown('##')
    st.markdown('##')
    st.markdown('#')
    # Load and resize the image to fit within the container
    #image2 = Image.open("Admin_web_app/Frame_4_2.jpg")
    #new_image2 = image2.resize((600, 375))  # Resize the image to fit within the screen width
    
    # Use st.image with adjusted width to prevent horizontal scrolling
    #st.image(new_image2, use_column_width=True)
    st.markdown("<h2 style='color: white; font-size: 18px;'>Actions to be taken:</h2>", unsafe_allow_html=True)
    st.image("Admin_web_app/Frame_4_2.jpg", use_column_width=True)

    st.markdown('##')
    st.markdown('##')
    st.markdown("<h2 style='color: white; font-size: 18px;'>MAP:</h2>", unsafe_allow_html=True)
    chart_data = pd.DataFrame(
        np.random.randn(5, 1) / [60, 60] + [20.079966, 74.109314],
        columns=['lat', 'lon']
    )
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/satellite-streets-v12',
        initial_view_state=pdk.ViewState(
            latitude=20.079966,
            longitude=74.109314,
            zoom=13,
            pitch=50,
            height=430,
            width=600
        ),
        layers=[
            pdk.Layer(
                "ScreenGridLayer",
                data=chart_data,
                get_position='[lon, lat]',
                get_color='[100, 30, 0, 160]',
                pickable=False,
                opacity=0.8,
                cell_size_pixels=20
            )
        ]
    ))
