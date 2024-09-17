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
    'Dipak Sangamnere': collection_1_data,
    'Ramesh Kapre': collection_2_data,
    'Arvind Khode': collection_3_data,
    'Ravindra Sambherao': collection_4_data,
    'Prabhakr Shirsath': collection_5_data,
    'Arjun Jachak': collection_6_data,
    'Yash More': collection_7_data,
    'Anant More': collection_8_data,
    'Dananjay Yadav': collection_9_data,
    'Kiran Derle': collection_10_data,
    'Nitin Gaidhani': collection_11_data
}

# Mapping collections to farmer images
farmer_images = {
    'Dipak Sangamnere': 'Admin_web_app/F1.png',
    'Ramesh Kapre': 'Admin_web_app/F2.png',
    'Arvind Khode': 'Admin_web_app/F6.png',
    'Ravindra Sambherao': 'Admin_web_app/F4.png',
    'Prabhakr Shirsath': 'Admin_web_app/F5.png',
    'Arjun Jachak': 'Admin_web_app/F3.png',
    'Yash More': 'Admin_web_app/F7.png',
    'Anant More': 'Admin_web_app/F8.png',
    'Dananjay Yadav': 'Admin_web_app/F9.png',
    'Kiran Derle': 'Admin_web_app/F10.png',
    'Nitin Gaidhani': 'Admin_web_app/F11.png'
}


farmer_names = {
    'Dipak Sangamnere': 'Dipak Sangamnere',
    'Ramesh Kapre': 'Ramesh Kapre',
    'Arvind Khode': 'Arvind Khode',
    'Ravindra Sambherao': 'Ravindra Sambherao',
    'Prabhakr Shirsath': 'Prabhakr Shirsath',
    'Arjun Jachak': 'Arjun Jachak',
    'Yash More': 'Yash More',
    'Anant More': 'Anant More',
    'Dananjay Yadav': 'Dananjay Yadav',
    'Kiran Derle': 'Kiran Derle',
    'Nitin Gaidhani': 'Nitin Gaidhani'
}

# Farm location mapping
farm_locations = {
    'Dipak Sangamnere': 'Niphad - Kherwadi',
    'Ramesh Kapre': 'Niphad - Panchkeshwar',
    'Arvind Khode': 'Nashik - Indira Nagar',
    'Ravindra Sambherao': 'Manori - Khurd',
    'Prabhakr Shirsath': 'Kundwadi - Niphad',
    'Arjun Jachak': 'Pathardi',
    'Yash More': 'Niphad - Pimpalgaon',
    'Anant More': 'Rahuri - Nashik',
    'Dananjay Yadav': 'Niphad - Kundewadi',
    'Kiran Derle': 'Nashik - Palse',
    'Nitin Gaidhani': 'Nashik - Indira Nagar'
}

# Plot size mapping
plot_sizes = {
    'Dipak Sangamnere': '1 Acre',
    'Ramesh Kapre': '3 Acre',
    'Arvind Khode': '1 Acre',
    'Ravindra Sambherao': '1.5 Acre',
    'Prabhakr Shirsath': '3 Acre',
    'Arjun Jachak': '2 Acre',
    'Yash More': '1 Acre',
    'Anant More': '2.5 Acre',
    'Dananjay Yadav': '2 Acre',
    'Kiran Derle': '3 Acre',
    'Nitin Gaidhani': '2.5 Acre'
}

#How old is the farm
farm_ages = {
    'Dipak Sangamnere': '8 Years',
    'Ramesh Kapre': '13 Years',
    'Arvind Khode': '6 Years',
    'Ravindra Sambherao': '9 Years',
    'Prabhakr Shirsath': '11 Years',
    'Arjun Jachak': '8 Years',
    'Yash More': '7 Years',
    'Anant More': '10 Years',
    'Dananjay Yadav': '7 Years',
    'Kiran Derle': '4 Years',
    'Nitin Gaidhani': '12 Years'
}

# Set page configuration
st.set_page_config(layout="wide")
st.title("Farm Analytics")

# Function to load the data from the imported variables
def load_collection(collection_name):
    return collection_data[collection_name]
    
# Multiselect for collections (Dropdown 1)
collections = st.multiselect(
    "Select farm(s):", 
    options=list(collection_data.keys()), 
    help="You can select one or multiple collections."
)

# Create a placeholder for the second dropdown
if collections:
    # Load data for all selected collections
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

    # If dates are selected
    if selected_dates:
        healthy_counts = []
        infected_counts = []
        farmer_names_list = [farmer_names.get(collection, 'Unknown Farmer') for collection in collections]

        # Process data for each selected collection
        for collection in collections:
            data = load_collection(collection)
            filtered_data = [entry for entry in data if pd.to_datetime(entry['Date of Scans']).date() in selected_dates]

            # Calculate total healthy and infected scans for the collection
            total_healthy = sum(entry['Total Healthy Scan'] for entry in filtered_data)
            total_infected = sum(entry['Total Infected Scan'] for entry in filtered_data)
            
            healthy_counts.append(total_healthy)
            infected_counts.append(total_infected)
            
        # If data is filtered, generate statistics
        if filtered_data:
            filtered_df = pd.DataFrame(filtered_data)
            total_healthy = filtered_df['Total Healthy Scan'].sum()
            total_infected = filtered_df['Total Infected Scan'].sum()
            
            # Infection and healthy percentage calculations
            total_scans = total_healthy + total_infected
            infection_percentage = (total_infected / total_scans) * 100 if total_scans > 0 else 0
            healthy_percentage = 100 - infection_percentage if total_scans > 0 else 0
            
            # Share data by each device
            if 'Device Name' in filtered_df.columns:
                device_scan_counts = filtered_df.groupby('Device Name')['Total Scan'].sum()
                data_share_text = "".join([f"{device}: {count / device_scan_counts.sum() * 100:.2f}%<br>" for device, count in device_scan_counts.items()])
          
            # Example placeholders for additional metrics
            most_active_device = "Sloth's Katana"
            least_active_device = "Borer_blade_2"
            total_infected_trees = "987"
            most_infected_plot = "Ramesh Kapre"
            least_infected_plot = "Arvind Khode"
        
        # Layout for bar charts
        col1, col2 = st.columns(2)

        # Bar chart for healthy and infected counts
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=farmer_names_list,
            y=healthy_counts,
            name='Healthy',
            marker=dict(color='#00FF00'),  # Green for healthy scans
        ))

        fig.add_trace(go.Bar(
            x=farmer_names_list,
            y=infected_counts,
            name='Infected',
            marker=dict(color='#FF0000'),  # Red for infected scans
        ))

        fig.update_layout(
            title="Healthy and Infected Scans by Collection",
            xaxis_title="Collection",
            yaxis_title="Number of Scans",
            barmode='group',
            bargap=0.2,
            font=dict(color='white'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300
        )

        col1.plotly_chart(fig, use_container_width=True)

        # Layout for the second row (Vertical Bar Chart)
        if selected_dates:
            fig = go.Figure()

            color_palette_healthy = ['#00FF00', '#1E90FF', '#FFA500', '#FFFF00', '#800080', '#FF69B4']  # Healthy colors
            color_palette_infected = ['#FF6347', '#DC143C', '#8B0000', '#FF4500', '#FF1493', '#C71585']  # Infected colors

            filtered_data = df[df['Date of Scans'].isin(selected_dates)]
            # Initialize color index
            color_index_healthy = 0
            color_index_infected = 0

            
            # Iterate through selected collections and extract device-wise data
            for collection in collections:
                collection_data_filtered = filtered_data[filtered_data['Device Name'].isin(
                    [item['Device Name'] for item in load_collection(collection)]
                )]
                
                device_names = list(set(collection_data_filtered['Device Name']))  # Unique device names
                for device_name in device_names:
                    device_data = collection_data_filtered[collection_data_filtered['Device Name'] == device_name]
                    dates = device_data['Date of Scans']
                    healthy_values = device_data['Total Healthy Scan']
                    infected_values = device_data['Total Infected Scan']

                    
                    # Plot healthy scans
                    fig.add_trace(go.Bar(
                        x=[d.strftime('%b %d') for d in dates],
                        y=healthy_values,
                        name=f'{device_name} - Healthy ({collection})',
                        marker=dict(color=color_palette_healthy[color_index_healthy % len(color_palette_healthy)]),  # Assign unique healthy color
                    ))

                    # Plot infected scans
                    fig.add_trace(go.Bar(
                        x=[d.strftime('%b %d') for d in dates],
                        y=infected_values,
                        name=f'{device_name} - Infected ({collection})',
                        marker=dict(color=color_palette_infected[color_index_infected % len(color_palette_infected)]),  # Assign unique infected color
                    ))
                    color_index_healthy += 1
                    color_index_infected += 1# Move to the next color in the palette

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
                        <strong>Data Share by Each Device:</strong>
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
            st.write(f"** **")
            # If dates are selected
            if selected_dates:
                 # Initialize data storage for each collection
                collection_summaries = {}

                for collection in collections:
                    data = load_collection(collection)
                    filtered_data = [entry for entry in data if pd.to_datetime(entry['Date of Scans']).date() in selected_dates]
            
                    # Calculate total healthy and infected scans for the collection
                    total_healthy = sum(entry['Total Healthy Scan'] for entry in filtered_data)
                    total_infected = sum(entry['Total Infected Scan'] for entry in filtered_data)
                    total_scans = sum(entry['Total Scan'] for entry in filtered_data)
                    total_trees = sum(entry['Total Trees'] for entry in filtered_data)
                    total_healthy_trees = sum(entry['Total Healthy Trees'] for entry in filtered_data)
                    total_infected_trees = sum(entry['Total Infected Trees'] for entry in filtered_data)
            
                    collection_summaries[collection] = {
                        'total_trees': total_trees,
                        'total_scans': total_scans,
                        'total_healthy': total_healthy,
                        'total_infected': total_infected,
                        'total_healthy_trees': total_healthy_trees,
                        'total_infected_trees': total_infected_trees
                    }
        
                # Display the filtered data in the desired format
                for collection in collections:
                    if collection in collection_summaries:
                        summary = collection_summaries[collection]
                        total_scans = summary['total_scans']
                        total_trees = summary['total_trees']
                        total_healthy = summary['total_healthy']
                        total_infected = summary['total_infected']
                        total_healthy_trees = summary['total_healthy_trees']
                        total_infected_trees = summary['total_infected_trees']

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
                                    <b>Total Healthy Scans:</b> {total_healthy}<br>
                                    <b>Total Infected Scans:</b> {total_infected}<br>
                                    <b>Farm Location:</b> {location}<br>
                                    <b>Farm Age:</b> {farm_age}<br>
                                    <b>Plot Size:</b> {plot_size}
                                </div>
                            """, unsafe_allow_html=True)
            
                        with col3:
                        #   Plot pie chart for healthy vs infected scans
                            if total_scans > 0:
                                fig = go.Figure(data=[go.Pie(
                                    labels=['Healthy Trees', 'Infected Trees'],
                                    values=[total_healthy_trees, total_infected_trees],
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
                                
                        # If selected dates are available
                        # If dates are selected
                        if selected_dates:
                            for collection in collections:
                                # Filter data for the current collection and selected dates
                                collection_data_filtered = [entry for entry in load_collection(collection) if pd.to_datetime(entry['Date of Scans']).date() in selected_dates]
                                
                                # Convert filtered data to DataFrame
                                collection_df = pd.DataFrame(collection_data_filtered)
                                
                                # Aggregate data by device and date
                                aggregated_data = collection_df.groupby(['Device Name', 'Date of Scans']).agg({
                                    'Total Healthy Scan': 'sum',
                                    'Total Infected Scan': 'sum'
                                }).reset_index()

                                # Plot bar chart
                                fig = go.Figure()
                                
                                devices = aggregated_data['Device Name'].unique()
                                colors = ['#00FF00', '#FF0000', '#1E90FF', '#FF6347', '#FF4500']  # Define more colors if needed
                                
                                for i, device in enumerate(devices):
                                    device_data = aggregated_data[aggregated_data['Device Name'] == device]
                                    
                                    fig.add_trace(go.Bar(
                                        x=device_data['Date of Scans'],
                                        y=device_data['Total Healthy Scan'],
                                        name=f'{device} - Healthy',
                                        marker_color=colors[i % len(colors)]
                                    ))
                                    
                                    fig.add_trace(go.Bar(
                                        x=device_data['Date of Scans'],
                                        y=device_data['Total Infected Scan'],
                                        name=f'{device} - Infected',
                                        marker_color=colors[(i + len(devices)) % len(colors)]
                                    ))

                                fig.update_layout(
                                    title_text=f"Scans for {collection} by Device",
                                    xaxis_title="Date",
                                    yaxis_title="Number of Scans",
                                    barmode='group',
                                    xaxis=dict(tickvals=selected_dates, ticktext=[date.strftime('%Y-%m-%d') for date in selected_dates]),
                                    font=dict(color='white'),
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    height=400
                                )

                                # Display the bar chart
                                st.plotly_chart(fig, use_container_width=True)
