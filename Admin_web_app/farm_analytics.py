import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from scipy.stats import skew, kurtosis
from google.cloud import firestore
from google.cloud.firestore import FieldFilter
from datetime import datetime, timedelta
import pytz
import time
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


# Set page configuration
st.set_page_config(layout="wide")
st.title("Farm Analytics")

db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")


def convert_to_local_time(timestamp, timezone='Asia/Kolkata'):
    local_tz = pytz.timezone(timezone)
    # Convert to UTC and then localize to the given timezone
    return timestamp.astimezone(local_tz)
    
# Fetch the most recent scan data from the "demo_db" collection
def get_recent_scans(db, num_scans=3):
    docs = (
        db.collection('demo_day')
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(num_scans)
        .stream()
    )
    metadata_list = []
    for doc in docs:
        data_dict = doc.to_dict()
        metadata = {
            'RadarRaw': data_dict.get('RadarRaw', []),
            'InfStat': data_dict.get('InfStat', 'Unknown'),
            'timestamp': convert_to_local_time(data_dict.get('timestamp')),
            'DeviceName': data_dict.get('Devicename', 'Unknown')
        }
        metadata_list.append(metadata)
    return metadata_list

# Filter scans by the same device name
def filter_scans_by_device(scans):
    scans_df = pd.DataFrame(scans).sort_values(by='timestamp', ascending=False)
    for device, group in scans_df.groupby('DeviceName'):
        if len(group) >= 2:
            return group.head(2)
    
    return pd.DataFrame()
    
# Preprocess data for each scan
def preprocess_multiple_scans(radar_data_list):
    processed_data_list = []
    for radar_raw in radar_data_list:
        df_radar = pd.DataFrame(radar_raw, columns=['Radar'])
        df_radar.dropna(inplace=True)
        df_radar.fillna(df_radar.mean(), inplace=True)
        processed_data_list.append(df_radar)
    return processed_data_list

# Function to calculate statistics
def calculate_statistics(df):
    df = df.apply(pd.to_numeric, errors='coerce')
    df.fillna(df.mean(), inplace=True)
    stats = {
        'Column': df.columns,
        'Mean': df.mean(),
        'Median': df.median(),
        #'Std Deviation': df.std(),
        'PTP': df.apply(lambda x: np.ptp(x)),
        #'Skewness': skew(df),
        #'Kurtosis': kurtosis(df),
        'Min': df.min(),
        'Max': df.max()
    }
    stats_df = pd.DataFrame(stats)
    return stats_df

# Plot time domain
def plot_time_domain(preprocessed_scans, timestamps, infstats, device_names, sampling_rate=100):
    st.write("## Time Domain")
    fig = go.Figure()

    for i, preprocessed_scan in enumerate(preprocessed_scans):
        device_name_in_parentheses = device_names[i][device_names[i].find('(') + 1:device_names[i].find(')')]
        color = 'green' if infstats[i] == 'Healthy' else 'red'
        time_seconds = np.arange(len(preprocessed_scan)) / sampling_rate
        fig.add_trace(go.Scatter(
            x=time_seconds,
            y=preprocessed_scan['Radar'],
            mode='lines',
            name=f"{device_name_in_parentheses} - {timestamps[i].strftime('%Y-%m-%d %H:%M:%S')}",
            line=dict(color=color)
        ))

    fig.update_layout(
        template='plotly_white',
        xaxis_title="Time (s)",
        yaxis_title="Signal",
        legend_title="Scans",
        font=dict(color="white"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig)

def plot_frequency_domain(preprocessed_scans, timestamps, infstats, device_names, sampling_rate=100):
    st.write("## Frequency Domain")
    fig = go.Figure()

    for i, preprocessed_scan in enumerate(preprocessed_scans):
        device_name_in_parentheses = device_names[i][device_names[i].find('(') + 1:device_names[i].find(')')]
        color = 'green' if infstats[i] == 'Healthy' else 'red'
        # Apply FFT on the preprocessed scan data
        frequencies = np.fft.fftfreq(len(preprocessed_scan), d=1/sampling_rate)
        fft_values = np.fft.fft(preprocessed_scan['Radar'])
        powers = np.abs(fft_values) / len(preprocessed_scan)
        powers_db = 20 * np.log10(powers)

        fig.add_trace(go.Scatter(
            x=frequencies[:len(frequencies)//2],
            y=powers_db[:len(powers_db)//2],
            mode='lines',
            name=f"{device_name_in_parentheses} - {timestamps[i].strftime('%Y-%m-%d %H:%M:%S')}",
            line=dict(color=color)
        ))

    fig.update_layout(
        template='plotly_white',
        xaxis_title="Frequency (Hz)",
        yaxis_title="Power Spectrum (dB)",
        legend_title="Scans",
        font=dict(color="white"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig)

# Plot statistics for multiple scans using Plotly with InfStat-based coloring
def plot_multiple_statistics(stats_dfs, timestamps, infstats, device_names):
    st.write("## Radar Column Statistics")
    
    fig = go.Figure()

    stats_measures = ['Mean', 'Median', 'PTP', 'Min', 'Max']
    
    for i, stats_df in enumerate(stats_dfs):
        # Determine color based on InfStat
        device_name_in_parentheses = device_names[i][device_names[i].find('(') + 1:device_names[i].find(')')]
    
        if i < len(infstats):
            color = 'green' if infstats[i] == 'Healthy' else 'red'
        
        #for measure in stats_measures:
        fig.add_trace(go.Bar(
            x=stats_measures,
            y=[stats_df[measure].values[0] for measure in stats_measures],  # Assuming one radar column
            name=f'{device_name_in_parentheses} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}',
            marker_color=color,
            ))

    # Update layout for transparent background
    fig.update_layout(
        barmode='group',
        template='plotly_white',
        xaxis_title="Statistics",
        yaxis_title="Values",
        legend_title="Scans",
        font=dict(color="white"),  # Adjust text color if needed
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
    )

    st.plotly_chart(fig)
    return fig

def main():
    # Fetch recent scans
    recent_scans = get_recent_scans(db, num_scans=3)
    
    if recent_scans:
        # Filter scans by device name and pick the 2 most recent ones with the same device name
        filtered_scans = filter_scans_by_device(recent_scans)
        
        if not filtered_scans.empty:
            st.markdown(" Data Analysis of 2 Recent Scans with Same Device")
            
            # Preprocess the scan data
            processed_data_list = preprocess_multiple_scans(filtered_scans['RadarRaw'])
            
            # Extract timestamps and InfStat
            timestamps = filtered_scans['timestamp'].tolist()
            infstats = filtered_scans['InfStat'].tolist()
            device_names = filtered_scans['DeviceName'].tolist()
            
            # Create columns for plots
            col1, col2, col3 = st.columns(3)
            
            # Time domain plot in col1
            with col1:
                plot_time_domain(processed_data_list, timestamps, infstats, device_names)

            # Frequency domain plot in col2
            with col2:
                plot_frequency_domain(processed_data_list, timestamps, infstats, device_names)
            
            # Statistics plot in col3
            with col3:
                stats_dfs = [calculate_statistics(df) for df in processed_data_list]
                plot_multiple_statistics(stats_dfs, timestamps, infstats, device_names)
        else:
            st.warning("No matching scans found with the same device name.")
    else:
        st.error("No recent scan data available.")

if __name__ == "__main__":
    main()

st.write(f"**Farmer Name:** Dananjay Yadav", color='white')
st.write(f"**Farm Location:** Null", color='white')
st.write(f"**Farm Age:** Null", color='white')
st.write(f"**Plot Size:** Null", color='white')

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
                        if selected_dates:  
                                data = load_collection(collection)  
                                filtered_data = [entry for entry in data if pd.to_datetime(entry['Date of Scans']).date() in selected_dates]  
                  
                                # Extract unique device names and dates  
                                device_names = list(set(entry['Device Name'] for entry in filtered_data))  
                                dates = list(set(pd.to_datetime(entry['Date of Scans']).date() for entry in filtered_data))  
                  
                                # Initialize color palettes  
                                color_palette_healthy = ['#00FF00', '#1E90FF', '#FFA500', '#FFFF00', '#800080', '#FF69B4']  
                                color_palette_infected = ['#FF6347', '#DC143C', '#8B0000', '#FF4500', '#FF1493', '#C71585']  
                  
                                # Create a figure for the bar chart  
                                fig = go.Figure()  
                  
                                # Iterate through devices and dates  
                                for i, device_name in enumerate(device_names):  
                                    for date in dates:  
                                        # Filter data for the current device and date  
                                        device_data = [entry for entry in filtered_data if entry['Device Name'] == device_name and pd.to_datetime(entry['Date of Scans']).date() == date]  
                  
                                        # Calculate healthy and infected scans  
                                        healthy_scans = sum(entry['Total Healthy Scan'] for entry in device_data)  
                                        infected_scans = sum(entry['Total Infected Scan'] for entry in device_data)  
                  
                                        # Plot healthy scans  
                                        fig.add_trace(go.Bar(  
                                            x=[date],  
                                            y=[healthy_scans],  
                                            name=f'{device_name} - Healthy',  
                                            marker=dict(color=color_palette_healthy[i % len(color_palette_healthy)]),  
                                        ))  
                  
                                        # Plot infected scans  
                                        fig.add_trace(go.Bar(  
                                            x=[date],  
                                            y=[infected_scans],  
                                            name=f'{device_name} - Infected',  
                                            marker=dict(color=color_palette_infected[i % len(color_palette_infected)]),  
                                        ))  
                  
                                # Update layout  
                                fig.update_layout(  
                                    title_text=f'{collection} - Scans by Device',  
                                    xaxis_title="Date",  
                                    yaxis_title="Number of Scans",  
                                    barmode='group',  
                                    font=dict(color='white'),  
                                    paper_bgcolor='rgba(0,0,0,0)',  
                                    plot_bgcolor='rgba(0,0,0,0)',  
                                    height=300  
                                )  
                  
                                # Plot the figure  
                                st.plotly_chart(fig, use_container_width=True)  


    # Add a button aligned to the left with a small, soft light blue style
    button_html = """
        <div style="display: flex; justify-content: center; align-items: center; gap: 30px; height: 50px;">
            <a href="https://dataanalyticspy-gvr9jktw8byafkhxiqgabk.streamlit.app/" target="_blank" style="
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
            <a href="https://main2py-gulvcac5kwhumuymhhuarh.streamlit.app/" target="_blank" style="
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
