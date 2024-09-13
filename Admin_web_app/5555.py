import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from scipy.stats import skew, kurtosis 
from google.cloud import firestore
from google.cloud.firestore import FieldFilter
from datetime import datetime, timedelta
import time
import zipfile
import os
import random
from google.api_core.exceptions import ResourceExhausted, RetryError
from collections import defaultdict
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go
import openpyxl

# Set page configuration
st.set_page_config(layout="wide")
st.title("Farm Analytics")

db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Mapping collections to farmer images
farmer_images = {
    'collection_1': 'Admin_web_app/F1.png',
    'collection_2': 'Admin_web_app/F2.png',
    'collection_3': 'Admin_web_app/F6.png',
    'collection_4': 'Admin_web_app/F4.png',
    'collection_5': 'Admin_web_app/F5.png',
    'collection_6': 'Admin_web_app/F3.png',
    'collection_7': 'Admin_web_app/F7.png',
    'demo_db': 'Admin_web_app/F8.png',
    'collection_9': 'Admin_web_app/F9.png',
    'collection_10': 'Admin_web_app/F10.png',
    'collection_11': 'Admin_web_app/F11.png',
    'collection_12': 'Admin_web_app/F712.png'
}


farmer_names = {
    'collection_1': 'Dipak Sangamnere',
    'collection_2': 'Ramesh Kapre',
    'collection_3': 'Arvind Khode',
    'collection_4': 'Ravindra Sambherao',
    'collection_5': 'Prabhakr Shirsath',
    'collection_6': 'Arjun Jachak',
    'collection_7': 'Yash More',
    'demo_db': 'Dananjay Yadav',
    'collection_9': 'Anant More',
    'collection_10': 'Kiran Derle',
    'collection_11': 'Nitin Gaidhani',
    'collection_12': 'Umesh Khode'
}

# Farm location mapping
farm_locations = {
    'collection_1': 'Niphad - Kherwadi',
    'collection_2': 'Niphad - Panchkeshwar',
    'collection_3': 'Nashik - Indira Nagar',
    'collection_4': 'Manori Khurd',
    'collection_5': 'Kundwadi Niphad',
    'collection_6': 'Pathardi',
    'collection_7': 'Niphad - Pimpalgaon',
    'demo_db': 'Rahuri Nashik',
    'collection_9': 'Niphad - Pimpalgaon',
    'collection_10': 'Niphad - Kunndewadi',
    'collection_11': 'Nashik - Palse',
    'collection_12': 'Nashik - Indira Nagar'
}

# Plot size mapping
plot_sizes = {
    'collection_1': '1 Acre',
    'collection_2': '3 Acres',
    'collection_3': '1 Acre',
    'collection_4': '1.5 Acres',
    'collection_5': '3 Acres',
    'collection_6': '1 Acre',
    'collection_7': '1 Acre',
    'demo_db': '2.5 Acres',
    'collection_9': '1 Acre',
    'collection_10': '2 Acres',
    'collection_11': '2.5 Acres',
    'collection_12': '1.2 Acres'
}

#How old is the farm
farm_ages = {
    'collection_1': '8 Years',
    'collection_2': '13 Years',
    'collection_3': '6 Years',
    'collection_4': '9 Years',
    'collection_5': '11 Years',
    'collection_6': '8 Years',
    'collection_7': '10 Years',
    'demo_db': '7 Years',
    'collection_9': '8 Years',
    'collection_10': '12 Years',
    'collection_11': '10 Years',
    'collection_12': '9 Years'
}
# Collection dates mapping (using original date format)
collection_dates = {'demo_db': []}

collection_file_paths = {
    'collection_1': 'Admin_web_app/collection_1.xlsx',
    'collection_2': 'Admin_web_app/collection_2.xlsx',
    'collection_3': 'Admin_web_app/collection_3.xlsx',
    'collection_4': 'Admin_web_app/collection_4.xlsx',
    'collection_5': 'Admin_web_app/collection_5.xlsx',
    'collection_6': 'Admin_web_app/collection_6.xlsx',
    'collection_7': 'Admin_web_app/collection_7.xlsx',
    'collection_9': 'Admin_web_app/collection_9.xlsx',
    'collection_10': 'Admin_web_app/collection_10.xlsx',
    'collection_11': 'Admin_web_app/collection_11.xlsx',
    'collection_12': 'Admin_web_app/collection_12.xlsx',
}

# Dropdown for collections
dropdown_options = ['Dananjay Yadav']  # 'demo_db' as the default
dropdown_options.extend([f"{farmer_names[collection]} - Collection {collection[-1]}" for collection in collection_file_paths.keys()])

selected_collections = st.multiselect('Select collections', dropdown_options)

# Dates dropdown based on selected collections
dates_dropdown_options = []
selected_collections_dict = {collection: [] for collection in collection_file_paths.keys()}

for option in selected_collections:
    if option == 'Dananjay Yadav':
        selected_collections_dict['demo_db'] = [None]
    else:
        collection = [key for key, value in farmer_names.items() if value == option.split(' - ')[0]][0]
        selected_collections_dict[collection] = []

# Retrieve unique dates for the selected collections
all_dates = set()
for collection, dates in selected_collections_dict.items():
    if collection == 'demo_db':
        # Process Firestore data
        docs = db.collection(collection).stream()
    else:
        docs = []
        for date in dates:
            if date:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
            file_path = collection_file_paths.get(collection)

            if file_path:
                try:
                    df_metadata = pd.read_excel(file_path)

                    # Strip spaces and normalize case in column names
                    df_metadata.columns = df_metadata.columns.str.strip().str.lower()

                    # Define desired columns in lowercase
                    desired_columns = ['device name', 'total scan', 'total infected scan', 'total healthy scan', 'date of scans']

                    # Check if desired columns exist
                    if all(col in df_metadata.columns for col in desired_columns):
                        df_metadata_filtered = df_metadata[desired_columns]
                        docs.append(df_metadata_filtered)
                    else:
                        st.warning(f"Columns not found in {file_path}: {desired_columns}")
                except Exception as e:
                    st.error(f"Error reading {file_path}: {e}")

# Sort and filter dates dropdown
if 'Dananjay Yadav' in selected_collections:
    dates_dropdown_options = []  # No date filter for Firestore data
else:
    dates_dropdown_options = sorted(all_dates)

if dates_dropdown_options:
    selected_dates = st.multiselect('Select dates', dates_dropdown_options)
else:
    selected_dates = []

# Continue processing based on selections
total_healthy = 0
total_infected = 0
collection_scan_counts = {}
device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

# Example data retrieval logic (Firestore and Excel processing)
for collection, dates in selected_collections_dict.items():
    if collection == 'demo_db':
        # Process Firestore data
        docs = db.collection(collection).stream()
    else:
        docs = []
        for date in dates:
            if date:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
            file_path = collection_file_paths.get(collection)
            if file_path:
                df_metadata = pd.read_excel(file_path)
                docs.append(df_metadata)

    metadata_list = []
    for doc in docs:
        if isinstance(doc, pd.DataFrame):  # Excel data
            metadata_list.append(doc)

    df_metadata = pd.concat(metadata_list, ignore_index=True)

    # Check and filter columns
    expected_columns = ['Device Name', 'Total Scan', 'Total Infected Scan', 'Total Healthy Scan', 'Date of Scans']
    missing_columns = [col for col in expected_columns if col not in df_metadata.columns]
    if missing_columns:
        st.error(f"Missing columns: {missing_columns}")
    else:
        df_metadata_filtered = df_metadata[expected_columns]

        # Process and sum the data
        total_scans = df_metadata_filtered['Total Scan'].sum()
        infected_count = df_metadata_filtered['Total Infected Scan'].sum()
        healthy_count = df_metadata_filtered['Total Healthy Scan'].sum()

        total_healthy += healthy_count
        total_infected += infected_count
        collection_scan_counts[collection] = total_scans
# Layout for the first row (4 columns)
col1, col2 = st.columns(2)

# Bar chart showing collections with most infected scans
if collection_scan_counts:
    farmer_names_list = [farmer_names.get(collection, 'Unknown Farmer') for collection in collection_scan_counts.keys()]
    healthy_counts = [collection_scan_counts[collection] - device_data[collection]['Infected'] for collection in collection_scan_counts.keys()]
    infected_counts = [device_data[collection]['Infected'] for collection in collection_scan_counts.keys()]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=farmer_names_list, y=healthy_counts, name='Healthy', marker=dict(color='#00FF00')))  # Green for healthy
    fig.add_trace(go.Bar(x=farmer_names_list, y=infected_counts, name='Infected', marker=dict(color='#FF0000')))  # Red for infected

    fig.update_layout(
        title_text="Healthy and Infected Scans by Collection",
        xaxis_title="Collection",
        yaxis_title="Number of Scans",
        barmode='group',  # Side-by-side grouping
        bargap=0.2,
        font=dict(color='white'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300
    )

    col1.plotly_chart(fig, use_container_width=True)

# Layout for the second row (Vertical Bar Chart)
if device_data:
    fig = go.Figure()

    for device_name, dates in device_data.items():
        healthy_values = [dates[date]['Healthy'] for date in sorted(dates.keys())]
        infected_values = [dates[date]['Infected'] for date in sorted(dates.keys())]
        dates_sorted = sorted(dates.keys())

        fig.add_trace(go.Bar(x=dates_sorted, y=healthy_values, name=f'{device_name} - Healthy', marker=dict(color='#00FF00')))
        fig.add_trace(go.Bar(x=dates_sorted, y=infected_values, name=f'{device_name} - Infected', marker=dict(color='#FF0000')))

    fig.update_layout(
        title_text="Scans by Device (Grouped by Collection)",
        xaxis_title="Date",
        yaxis_title="Number of Scans",
        barmode='group',  # Group devices by collection
        font=dict(color='white'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300
    )

    col2.plotly_chart(fig, use_container_width=True)

    # Calculate percentages for combined collection
    if total_healthy + total_infected > 0:
        infection_percentage = (total_infected / (total_healthy + total_infected)) * 100
        healthy_percentage = (total_healthy / (total_healthy + total_infected)) * 100
    else:
        infection_percentage = 0
        healthy_percentage = 0

    # Calculate data share by each collection
    data_share_text = ""
    
    if collection_scan_counts:
        total_scans_all_collections = sum(collection_scan_counts.values())
        if total_scans_all_collections > 0:
            for collection, count in collection_scan_counts.items():
                share_percentage = (count / total_scans_all_collections) * 100
                farmer_name = farmer_names.get(collection, 'Unknown Farmer')
                data_share_text += f"{farmer_name}: {share_percentage:.2f}%<br>"

    # Styled box for comments
    most_active_device = "Sloth's Katana"
    least_active_device = "Proto 2"
    total_infected_trees = 456
    most_infected_plot = "Devmode"
    least_infected_plot = "testing"

    st.markdown(f"""
        <div style="
            padding: 10px;
            background-color: #ADD8E6;
            border-radius: 10px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
            font-family: 'Arial', sans-serif;
            color: #333333;
            width: 100%;  /* Take full column width */
            margin-top: 10px;
        ">
            <h4 style="color: #007ACC; margin-bottom: 1px;">Comments</h4>
            <hr style="border: none; height: 1px; background-color: #007ACC; margin-bottom: 1px;">
            <p style="font-size: 14px; margin: 5px 0;">
                <strong>Combined Collection:</strong> Infection status: {infection_percentage:.2f}%, Healthy status: {healthy_percentage:.2f}%
            </p>
            <p style="font-size: 14px; margin: 5px 0;">
                <strong>Data Share by Each Collection:</strong>
            </p>
            {data_share_text}
            <p style="font-size: 14px; margin: 5px 0;">
                <strong>Most Active Device:</strong> {most_active_device}
            </p>
            <p style="font-size: 14px; margin: 5px 0;">
                <strong>Least Active Device:</strong> {least_active_device}
            </p>
            <p style="font-size: 14px; margin: 5px 0;">
                <strong>Total Infected Trees Detected by Team TREBIRTH:</strong> {total_infected_trees}
            </p>
            <p style="font-size: 14px; margin: 5px 0;">
                <strong>Most Infected Plot:</strong> {most_infected_plot}
            </p>
            <p style="font-size: 14px; margin: 5px 0;">
                <strong>Least Infected plot:</strong> {least_infected_plot}
            </p>
        </div>
    """, unsafe_allow_html=True)
    # Process and analyze the retrieved documents
    # Process and analyze the retrieved documents
    for collection in selected_collections.keys():
        docs = db.collection(collection).stream()
    
        # Initialize counts
        healthy_count = 0
        infected_count = 0
        total_scans = 0
    
        # Initialize device data storage
        device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

        # Process each document
        for doc in docs:
            doc_data = doc.to_dict()
            inf_stat = doc_data.get('InfStat', 'Unknown')
            device_name = doc_data.get('DeviceName')
            timestamp = doc_data.get('timestamp', None)
        
            if not timestamp or not device_name:
                continue
            date_key = timestamp.strftime('%Y-%m-%d')

            # Update counts
            if inf_stat == 'Healthy':
                healthy_count += 1
                device_data[device_name][date_key]['Healthy'] += 1
            elif inf_stat == 'Infected':
                infected_count += 1
                device_data[device_name][date_key]['Infected'] += 1

        total_scans = healthy_count + infected_count

        if total_scans > 0:
            st.write(f"** **")
        # Layout for collection details
        
        col1, col2, col3 = st.columns(3)
    
        with col1:
            # Display farmer image
            farmer_image = farmer_images.get(collection, 'default.png')
            farmer_name = farmer_names.get(collection, 'Unknown Farmer')
            st.image(farmer_image, width= 300, use_column_width=False)
            st.write(f"**Farmer Name:** {farmer_name}", color='white')
    
        with col2:
            # Display scan counts
            #st.write(f"**Total Scans:** {total_scans}", color='white')
            #st.write(f"**Healthy Scans:** {healthy_count}", color='white')
            #st.write(f"**Infected Scans:** {infected_count}", color='white')
            location = farm_locations.get(collection, 'Unknown Location')
            plot_size = plot_sizes.get(collection, 'Unknown Plot Size')
            farm_age = farm_ages.get(collection, 'Unknown farm age')
            st.markdown(f"""
                <div style='
                    text-align: center; 
                    color: white; 
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 10px;'>
                    Farm Details
                </div>
                <div style='
                    text-align: justify; 
                    color: white; 
                    background-color: rgba(0, 128, 0, 0.1); 
                    border: 2px solid white; 
                    padding: 10px; 
                    border-radius: 10px;
                    margin: 10px auto;
                    width: 80%;'>
                    <br>
                    <b>Total Scans:</b> {total_scans}<br>
                    <b>Healthy Scans:</b> {healthy_count}<br>
                    <b>Infected Scans:</b> {infected_count}<br>
                    <b>Farm Location:</b> {location}<br>
                    <b>Farm Age:</b> {farm_age}<br>
                    <b>Plot Size:</b> {plot_size}
                </div>
                """, unsafe_allow_html=True)
            #st.write(f"**Farm Location:** {location}", color='white')
            #st.write(f"**Farm Age:** {farm_age}", color='white')
            #st.write(f"**Plot Size:** {plot_size}", color='white')
        
        with col3:
        # Plot pie chart for healthy vs infected scans
            if total_scans > 0:
                fig = go.Figure(data=[go.Pie(
                    labels=['Healthy', 'Infected'],
                    values=[healthy_count, infected_count],
                    hole=0.3,  # Donut chart style
                    marker=dict(colors=['#00FF00', '#FF0000'])
                )])
                fig.update_layout(
                    title_text=f'{farmer_name} - Healthy vs Infected',
                    font=dict(color='white'),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height= 350
                )
                st.plotly_chart(fig)
        
        # Plot vertical bar chart for device scan counts
        fig = go.Figure()

        device_names = list(device_data.keys())
        dates = sorted(set(date for device in device_data.values() for date in device.keys()))
        
        
        # Define a color palette for both healthy and infected bars
        color_palette_healthy = ['#00FF00', '#1E90FF', '#FFA500', '#FFFF00', '#800080', '#FF69B4']  # Colors for healthy scans
        color_palette_infected = ['#FF6347', '#DC143C', '#8B0000', '#FF4500', '#FF1493', '#C71585']  # Colors for infected scans

        # Add data for each date, grouping healthy and infected bars side by side for each device
        for i, device_name in enumerate(device_names):
            for date in dates:
                # Get healthy and infected scan counts for the current date and device
                healthy_count = device_data[device_name].get(date, {'Healthy': 0})['Healthy']
                infected_count = device_data[device_name].get(date, {'Infected': 0})['Infected']

                # Plot healthy counts for the device
                fig.add_trace(go.Bar(
                    x=[date],  # Same date for healthy and infected, but split by device
                    y=[healthy_count],
                    name=f'{device_name} - Healthy',
                    marker=dict(color=color_palette_healthy[i % len(color_palette_healthy)]),  # Unique color for healthy
                    width=0.35,  # Adjust bar thickness
                    offsetgroup=device_name,  # Group by device to align healthy/infected bars together
                    hoverinfo='y'
                ))

                # Plot infected counts for the device
                fig.add_trace(go.Bar(
                    x=[date],  # Same date for healthy and infected, but split by device
                    y=[infected_count],
                    name=f'{device_name} - Infected',
                    marker=dict(color=color_palette_infected[i % len(color_palette_infected)]),  # Unique color for infected
                    width=0.35,  # Same bar thickness as healthy
                    offsetgroup=device_name,  # Group by device to align healthy/infected bars together
                    hoverinfo='y'
                ))

        # Update layout for transparency, appropriate colors, and bar grouping
        fig.update_layout(
            barmode='group',  # Group healthy and infected bars side by side
            bargap=0.2,  # Small gap between different devices
            title_text=f'Device Scan Counts by Date',
            xaxis_title="Date",
            yaxis_title="Number of Scans",
            font=dict(color='white'),  # White font for dark background
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot background
            legend_title_text="Devices",
            legend=dict(orientation="v",  # Vertical legend
                        y=0.5,  # Align in the middle vertically
                        x=1.02,  # Move it outside the chart area, on the right
                        xanchor='left'),  # Anchor the legend to the left of the plot
            height=400,
            xaxis=dict(tickformat='%Y-%m-%d'),  # Display only the date
        )

        # Plot the figure in Streamlit
        st.plotly_chart(fig)
    
    
    # Add a button aligned to the left with a small, soft light blue style
    button_html = """
        <div style="display: flex; justify-content: center; align-items: center; gap: 30px; height: 50px;">
            <a href="https://qskfow5zno4xytjdx4ydcs.streamlit.app/" target="_blank" style="
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: normal;
                background-color: #ADD8E6;
                color: black;
                text-align: center;
                text-decoration: none;
                border-radius: 5px;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
            ">
                Detailed Scan Analysis
            </a>
            <a href="https://mainpy-vknuf7uh4vuaqyrhwqzvhk.streamlit.app/" target="_blank" style="
                display: inline-block;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: normal;
                background-color: #ADD8E6;
                color: black;
                text-align: center;
                text-decoration: none;
                border-radius: 5px;
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
            ">
                Customer View
            </a>
        </div>
    """
    st.markdown(button_html, unsafe_allow_html=True)
