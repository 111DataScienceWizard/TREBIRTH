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
from collection_1 import collection_1_data
from collection_2 import collection_2_data
from collection_3 import collection_3_data
from collection_4 import collection_4_data
from collection_5 import collection_5_data
from collection_6 import collection_6_data
from collection_7 import collection_7_data
from collection_8 import collection_8_data
from collection_9 import collection_9_data
from collection_10 import collection_10_data
from collection_11 import collection_11_data

# Define the collection data mapping
collection_data = {
    'collection_1': collection_1_data,
    'collection_2': collection_2_data,
    'collection_3': collection_3_data,
    'collection_4': collection_4_data,
    'collection_5': collection_5_data,
    'collection_6': collection_6_data,
    'collection_7': collection_7_data,
    'collection_8': collection_8_data,
    'collection_9': collection_9_data,
    'collection_10': collection_10_data,
    'collection_11': collection_11_data
}

# Mapping collections to farmer images
farmer_images = {
    'collection_1': 'Admin_web_app/F1.png',
    'collection_2': 'Admin_web_app/F2.png',
    'collection_3': 'Admin_web_app/F6.png',
    'collection_4': 'Admin_web_app/F4.png',
    'collection_5': 'Admin_web_app/F5.png',
    'collection_6': 'Admin_web_app/F3.png',
    'collection_7': 'Admin_web_app/F7.png',
    'collection_8': 'Admin_web_app/F8.png',
    'collection_9': 'Admin_web_app/F9.png',
    'collection_10': 'Admin_web_app/F10.png',
    'collection_11': 'Admin_web_app/F11.png'
}


farmer_names = {
    'collection_1': 'Dipak Sangamnere',
    'collection_2': 'Ramesh Kapre',
    'collection_3': 'Arvind Khode',
    'collection_4': 'Ravindra Sambherao',
    'collection_5': 'Prabhakr Shirsath',
    'collection_6': 'Arjun Jachak',
    'collection_7': 'Yash More',
    'collection_8': 'Anant More',
    'collection_9': 'Dananjay Yadav',
    'collection_10': 'Kiran Derle',
    'collection_11': 'Nitin Gaidhani'
}

# Farm location mapping
farm_locations = {
    'collection_1': 'Niphad - Kherwadi',
    'collection_2': 'Niphad - Panchkeshwar',
    'collection_3': 'Nashik - Indira Nagar',
    'collection_4': 'Manori - Khurd',
    'collection_5': 'Kundwadi - Niphad',
    'collection_6': 'Pathardi',
    'collection_7': 'Niphad - Pimpalgaon',
    'collection_8': 'Rahuri - Nashik',
    'collection_9': 'Niphad - Kundewadi',
    'collection_10': 'Nashik - Palse',
    'collection_11': 'Nashik - Indira Nagar'
}

# Plot size mapping
plot_sizes = {
    'collection_1': '1 Acre',
    'collection_2': '3 Acre',
    'collection_3': '1 Acre',
    'collection_4': '1.5 Acre',
    'collection_5': '3 Acre',
    'collection_6': '2 Acre',
    'collection_7': '1 Acre',
    'collection_8': '2.5 Acre',
    'collection_9': '2 Acre',
    'collection_10': '3 Acre',
    'collection_11': '2.5 Acre'
}

#How old is the farm
farm_ages = {
    'collection_1': '8 Years',
    'collection_2': '13 Years',
    'collection_3': '6 Years',
    'collection_4': '9 Years',
    'collection_5': '11 Years',
    'collection_6': '8 Years',
    'collection_7': '7 Years',
    'collection_8': '10 Years',
    'collection_9': '7 Years',
    'collection_10': '4 Years',
    'collection_11': '12 Years'
}

# Set page configuration
st.set_page_config(layout="wide")
st.title("Farm Analytics")

# Create a list of unique farmer names
farmer_options = list(set(farmer_names.values()))
# Function to load the data from the imported variables
def load_collection(collection_name):
    return collection_data[collection_name]

# Multiselect for collections (Dropdown 1)
collections = st.multiselect(
    "Select farms:", 
    options=farmer_options, 
)

# Create a placeholder for the second dropdown
#if collections:
    # Load data for all selected collections
selected_collections = [collection for collection, name in farmer_names.items() if name in selected_farmers]
    all_data = []
    for collection in collections:
        data = load_collection(collection)
        all_data.extend(data)
    
    # Convert list of dictionaries to DataFrame
    df = pd.DataFrame(all_data)
    
    # Convert 'Date of Scans' to datetime
    df['Date of Scans'] = pd.to_datetime(df['Date of Scans']).dt.date
    
    # Extract unique dates for the selected collections
    unique_dates = df['Date of Scans'].unique()
    
    # Multiselect for unique dates (Dropdown 2)
    selected_dates = st.multiselect(
        "Select unique date(s):",
        options=sorted(unique_dates),
        help="Select one or more dates to filter data."
    )

    if selected_dates:
        # Filter the data by the selected dates
        filtered_data = df[df['Date of Scans'].isin(selected_dates)]
        
        # Calculate percentages for combined collection
        total_healthy = filtered_data['Total Healthy Scan'].sum()
        total_infected = filtered_data['Total Infected Scan'].sum()
        
        if total_healthy + total_infected > 0:
            infection_percentage = (total_infected / (total_healthy + total_infected)) * 100
            healthy_percentage = (total_healthy / (total_healthy + total_infected)) * 100
        else:
            infection_percentage = 0
            healthy_percentage = 0

        # Calculate data share by each collection
        collection_scan_counts = filtered_data.groupby('Device Name')['Total Scan'].sum()
        data_share_text = ""
        
        if collection_scan_counts.sum() > 0:
            for collection, count in collection_scan_counts.items():
                share_percentage = (count / collection_scan_counts.sum()) * 100
                farmer_name = farmer_names.get(collection, 'Unknown Farmer')
                data_share_text += f"{farmer_name}: {share_percentage:.2f}%<br>"

        # Example placeholders for other statistics
        most_active_device = "Sloth's Katana"  # You might want to calculate this
        least_active_device = "Proto 2"  # You might want to calculate this
        total_infected_trees = filtered_data['Total Infected Trees'].sum()
        most_infected_plot = "Devmode"  # You might want to calculate this
        least_infected_plot = "Testing"  # You might want to calculate this
        # Display the filtered data in the desired format
        #st.write("Filtered Data:")
        #for date in selected_dates:
            #st.write(f"Date: {date}")
            #date_data = filtered_data[filtered_data['Date of Scans'] == date]
            #for index, row in date_data.iterrows():
                #st.write(f"Device Name: {row['Device Name']}")
                #st.write(f"Total Scan: {row['Total Scan']}")
                #st.write(f"Total Infected Scan: {row['Total Infected Scan']}")
                #st.write(f"Total Healthy Scan: {row['Total Healthy Scan']}")
                #st.write(f"Total Trees: {row['Total Trees']}")
                #st.write(f"Total Infected Trees: {row['Total Infected Trees']}")
                #st.write(f"Total Healthy Trees: {row['Total Healthy Trees']}")
                #st.write("---")  # Separator for each entry
        # Layout for the first row (2 columns)
        col1, col2 = st.columns(2)

        # Bar chart showing collections with most infected scans
        if collections:
            farmer_names_list = [farmer_names.get(collection, 'Unknown Farmer') for collection in collections]
            # Calculate healthy and infected counts for each collection
            healthy_counts = []
            infected_counts = []

            # Iterate through selected collections to get healthy and infected counts
            for collection in collections:
                data = collection_data[collection]
                healthy_sum = sum(item['Total Healthy Scan'] for item in data)
                infected_sum = sum(item['Total Infected Scan'] for item in data)
                healthy_counts.append(healthy_sum)
                infected_counts.append(infected_sum)
                
            fig = go.Figure()

            # Add healthy counts for each collection
            fig.add_trace(go.Bar(
                x=farmer_names_list,
                y=healthy_counts,
                name='Healthy',
                marker=dict(color='#00FF00'),  # Green for healthy
            ))

            # Add infected counts for each collection
            fig.add_trace(go.Bar(
                x=farmer_names_list,
                y=infected_counts,
                name='Infected',
                marker=dict(color='#FF0000'),  # Red for infected
            ))

            fig.update_layout(
                title_text="Healthy and Infected Scans by Collection",
                xaxis_title="Collection",
                yaxis_title="Number of Scans",
                barmode='group',  # Side-by-side grouping
                bargap=0.2,  # Gap between bars (adjust as needed)
                font=dict(color='white'),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300
            )

            col1.plotly_chart(fig, use_container_width=True)

        # Layout for the second row (Vertical Bar Chart)
        if collections:
            fig = go.Figure()

            # Iterate through selected collections and extract device-wise data
            for collection in collections:
                data = collection_data[collection]
                device_names = list(set(item['Device Name'] for item in data))  # Unique device names
                for device_name in device_names:
                    device_data = [item for item in data if item['Device Name'] == device_name]
                    dates = [item['Date of Scans'] for item in device_data]
                    healthy_values = [item['Total Healthy Scan'] for item in device_data]
                    infected_values = [item['Total Infected Scan'] for item in device_data]

                    # Plot healthy scans
                    fig.add_trace(go.Bar(
                        x=dates,
                        y=healthy_values,
                        name=f'{device_name} - Healthy',
                        marker=dict(color='#00FF00'),  # Green for healthy
                    ))

                    # Plot infected scans
                    fig.add_trace(go.Bar(
                        x=dates,
                        y=infected_values,
                        name=f'{device_name} - Infected',
                        marker=dict(color='#FF0000'),  # Red for infected
                    ))

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

            
            st.markdown(f"""
                <div style="
                    padding: 10px;
                    background-color: #ADD8E6;
                    border-radius: 10px;
                    box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
                    font-family: 'Arial', sans-serif;
                    color: #333333;
                    width: 100%;
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
                        <strong>Least Infected Plot:</strong> {least_infected_plot}
                    </p>
                </div>
            """, unsafe_allow_html=True)

            if selected_dates:
            # Filter the data by the selected dates
                filtered_data = df[df['Date of Scans'].isin(selected_dates)]
        
             # Display the filtered data in the desired format
                for collection in collections:
                    collection_data = df[df['Date of Scans'].isin(selected_dates)]
            
                    # Initialize counts
                    healthy_count = 0
                    infected_count = 0
                    total_scans = 0
            
                    # Initialize device data storage
                    device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))
            
                    for index, row in collection_data.iterrows():
                        inf_stat = 'Healthy' if row['Total Healthy Scan'] > 0 else 'Infected'
                        device_name = row['Device Name']
                        date_key = row['Date of Scans']
                
                        if inf_stat == 'Healthy':
                            healthy_count += row['Total Healthy Scan']
                            device_data[device_name][date_key]['Healthy'] += row['Total Healthy Scan']
                        elif inf_stat == 'Infected':
                            infected_count += row['Total Infected Scan']
                            device_data[device_name][date_key]['Infected'] += row['Total Infected Scan']
            
                    total_scans = healthy_count + infected_count
            
                    # Layout for collection details
                    col1, col2, col3 = st.columns(3)
            
                    with col1:
                        # Display farmer image
                        farmer_image = farmer_images.get(collection, 'default.png')
                        farmer_name = farmer_names.get(collection, 'Unknown Farmer')
                        st.image(farmer_image, width=300, use_column_width=False)
                        st.write(f"**Farmer Name:** {farmer_name}", color='white')
            
                    with col2:
                        # Display scan counts and farm details
                        location = farm_locations.get(collection, 'Unknown Location')
                        plot_size = plot_sizes.get(collection, 'Unknown Plot Size')
                        farm_age = farm_ages.get(collection, 'Unknown Farm Age')
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
                            height=350
                        )
                        st.plotly_chart(fig)

            # Plot vertical bar chart for device scan counts
            fig = go.Figure()

            # Extract device names and dates from the current data structure
            device_names = list(device_data.keys())
            dates = sorted(set(date for device in device_data.values() for date in device.keys()))

            # Define a color palette for healthy and infected bars
            color_palette_healthy = ['#00FF00', '#1E90FF', '#FFA500', '#FFFF00', '#800080', '#FF69B4']  # Healthy colors
            color_palette_infected = ['#FF6347', '#DC143C', '#8B0000', '#FF4500', '#FF1493', '#C71585']  # Infected colors

            # Iterate through devices and dates to plot healthy and infected scans
            for i, device_name in enumerate(device_names):
                for date in dates:
                # Retrieve healthy and infected scan counts for the given date and device
                    healthy_count = device_data[device_name].get(date, {'Healthy': 0})['Healthy']
                    infected_count = device_data[device_name].get(date, {'Infected': 0})['Infected']

                    # Add bar for healthy scans
                    fig.add_trace(go.Bar(
                        x=[date],  # Date for healthy scans
                        y=[healthy_count],
                        name=f'{device_name} - Healthy',
                        marker=dict(color=color_palette_healthy[i % len(color_palette_healthy)]),  # Assign unique healthy color
                        width=0.35,  # Bar width
                        offsetgroup=device_name,  # Group by device
                        hoverinfo='y'
                    ))

                    # Add bar for infected scans
                    fig.add_trace(go.Bar(
                        x=[date],  # Date for infected scans
                        y=[infected_count],
                        name=f'{device_name} - Infected',
                        marker=dict(color=color_palette_infected[i % len(color_palette_infected)]),  # Assign unique infected color
                        width=0.35,  # Same bar width as healthy
                        offsetgroup=device_name,  # Group by device
                        hoverinfo='y'
                    ))

            # Update layout for grouped bars, improved aesthetics, and legend placement
            fig.update_layout(
                barmode='group',  # Group healthy and infected bars side by side
                bargap=0.2,  # Gap between different devices
                title_text=f'Device Scan Counts by Date',
                xaxis_title="Date",
                yaxis_title="Number of Scans",
                font=dict(color='white'),  # White font for dark theme
                paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot background
                legend_title_text="Devices",
                legend=dict(
                    orientation="v",  # Vertical legend
                    y=0.5,  # Center vertically
                    x=1.02,  # Move it outside the chart on the right
                    xanchor='left'  # Anchor the legend to the left of the plot
                ),
                height=400,  # Chart height
                xaxis=dict(tickformat='%Y-%m-%d'),  # Display only the date in 'YYYY-MM-DD' format
            )

            # Plot the figure in Streamlit
            st.plotly_chart(fig)
