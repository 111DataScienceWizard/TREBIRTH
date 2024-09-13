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

def exponential_backoff(retries):
    base_delay = 1
    max_delay = 60
    delay = base_delay * (2 ** retries) + random.uniform(0, 1)
    return min(delay, max_delay)

def get_firestore_data(query):
    retries = 0
    max_retries = 10
    while retries < max_retries:
        try:
            results = query.stream()
            return list(results)
        except ResourceExhausted as e:
            st.warning(f"Quota exceeded, retrying... (attempt {retries + 1})")
            time.sleep(exponential_backoff(retries))
            retries += 1
        except RetryError as e:
            st.warning(f"Retry error: {e}, retrying... (attempt {retries + 1})")
            time.sleep(exponential_backoff(retries))
            retries += 1
        except Exception as e:
            st.error(f"An error occurred: {e}")
            break
    raise Exception("Max retries exceeded")


# Set page configuration
st.set_page_config(layout="wide")
st.title("Farm Analytics")

db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Fetch the most recent scan data from the "demo_db" collection
def get_recent_scans(db, num_scans=2):
    docs = (
        db.collection('demo_db')
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(num_scans)
        .stream()
    )
    radar_data_list = []
    timestamps = []
    for doc in docs:
        data_dict = doc.to_dict()
        radar_raw = data_dict.get('RadarRaw', [])
        timestamp = data_dict.get('timestamp')
        radar_data_list.append(radar_raw)
        timestamps.append(timestamp)
    return radar_data_list, timestamps

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

# Plot multiple scans in time domain
def plot_multiple_time_domain(data_list, timestamps):
    st.write("## Time Domain")
    # Initialize the Plotly figure
    fig = go.Figure()
    
    # Define colors for the different scans
    colors = ['#E24E42', '#59C3C3']
    
    # Add traces (lines) for each scan
    for i, data in enumerate(data_list):
        fig.add_trace(go.Scatter(
            y=data,  # Plot the raw index data on the y-axis
            mode='lines',
            name=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}',
            line=dict(color=colors[i])
        ))
    
    # Update layout for transparent background
    fig.update_layout(
        template='plotly_white',  # Use a template with no dark background
        xaxis_title="Index",  # Raw index numbers
        yaxis_title="Signal",
        legend_title="Scans",
        font=dict(color="black"),  # Adjust text color if needed
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)'  # Transparent background
    )

    # Render the plot using Streamlit
    st.plotly_chart(fig)
    return fig
    
# Plot multiple scans in frequency domain using Plotly
def plot_multiple_frequency_domain(data_list, timestamps):
    st.write("## Frequency Domain")
    fig = go.Figure()

    colors = ['green', 'blue']

    for i, data in enumerate(data_list):
        # Perform FFT
        frequencies = np.fft.fftfreq(len(data), d=1/100)
        fft_values = np.fft.fft(data)
        powers = np.abs(fft_values) / len(data)
        powers_db = 20 * np.log10(powers)

        # Add trace to the Plotly figure
        fig.add_trace(go.Scatter(
            x=frequencies[:len(frequencies)//2], 
            y=powers_db[:len(powers_db)//2], 
            mode='lines',
            name=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}',
            line=dict(color=colors[i])
        ))

    # Update layout for transparent background
    fig.update_layout(
        template='plotly_white',
        xaxis_title="Frequency (Hz)",
        yaxis_title="Power Spectrum (dB)",
        legend_title="Scans",
        font=dict(color="white"),
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)'  # Transparent background
    )

    st.plotly_chart(fig)
    return fig

# Plot statistics for multiple scans using Plotly
def plot_multiple_statistics(stats_dfs, timestamps):
    st.write("## Radar Column Statistics")
    
    fig = go.Figure()

    stats_measures = ['Mean', 'Median', 'PTP', 'Min', 'Max']
    colors = ['green', 'blue']

    for i, stats_df in enumerate(stats_dfs):
        for measure in stats_measures:
            fig.add_trace(go.Bar(
                x=stats_measures,
                y=[stats_df[measure].values[0] for measure in stats_measures],  # Assuming one radar column
                name=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}',
                marker_color=colors[i],
            ))

    # Update layout for transparent background
    fig.update_layout(
        barmode='group',
        template='plotly_white',
        xaxis_title="Statistics",
        yaxis_title="Values",
        font=dict(color="white"),
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)'  # Transparent background
    )

    st.plotly_chart(fig)
    return fig

def main():
    radar_data_list, timestamps = get_recent_scans(db, num_scans=2)

    if radar_data_list:
        # Preprocess data for each scan
        processed_data_list = preprocess_multiple_scans(radar_data_list)
        
        # Display timestamps of scans
        #st.markdown(f"**Timestamps of Recent Scans:** {', '.join([ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps])}")
        st.markdown(f"**DATA ANALAYSIS OF 2 RECENT SCANS**")

        # Create three columns for plots
        col1, col2, col3 = st.columns(3)

        # Time domain plot for multiple scans
        with col1:
            time_fig = plot_multiple_time_domain([df['Radar'].values for df in processed_data_list], timestamps)
            

        # Frequency domain plot for multiple scans
        with col2:
            freq_fig = plot_multiple_frequency_domain([df['Radar'].values for df in processed_data_list], timestamps)
            

        # Statistics plot for multiple scans
        with col3:
            stats_dfs = [calculate_statistics(df) for df in processed_data_list]
            stats_fig = plot_multiple_statistics(stats_dfs, timestamps)
    else:
        st.error("No data available in the 'Dananjay Yadav' collection.")

if __name__ == "__main__":
    main()

st.write(f"**Farmer Name:** Dananjay Yadav", color='white')
st.write(f"**Farm Location:** Rahuri Nashik", color='white')
st.write(f"**Farm Age:** 7 Years", color='white')
st.write(f"**Plot Size:** 2.5 Acre", color='white')

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
    'collection_9':
    'collection_10':
    'collection_11':
    'collection_12':
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
collection_dates = {
    'TechDemo': ['2024-02-28', '2024-02-29'],
    'Mr.Arjun': ['2024-03-04', '2024-03-05'],
    'DevOps': ['2024-03-11', '2024-03-12', '2024-03-13', '2024-03-14', '2024-03-15', '2024-03-16', 
               '2024-06-04', '2024-06-05'],
    'DevMode': ['2024-02-22', '2024-02-23', '2024-02-24', '2024-02-25', '2024-02-26', '2024-02-28'],
    'debugging': ['2024-06-10', '2024-06-13', '2024-06-14'],
    'testing': ['2024-06-13'],
    'demo_db': [],
    'QDIC_test': ['2024-09-03']
    
}


# Generate dropdown options with collection names and original date format
dropdown_options = ['Dananjay Yadav']
for collection, dates in collection_dates.items():
    farmer_name = farmer_names.get(collection, 'Unknown Farmer')
    if dates:
        dropdown_options.extend([f"{farmer_name} - {date}" for date in dates])
    else:
        dropdown_options.append(f"{farmer_name} - No Dates")

# Sort dropdown options by newest to oldest
dropdown_options[1:] = sorted(dropdown_options[1:], key=lambda x: datetime.strptime(x.split(' - ')[1], '%Y-%m-%d') if 'No Dates' not in x else datetime.min, reverse=True)

# Create dropdown menu
selected_options = st.multiselect('Select farmer plots with Dates', dropdown_options)

if selected_options:
    selected_collections = {}
    total_healthy = 0
    total_infected = 0
    collection_scan_counts = {}
    device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

    for option in selected_options:
        if option == 'Dananjay Yadav':  # If Dananjay Yadav is selected
            collection = 'demo_db'
            selected_collections[collection] = [None]  # No specific dates
        else:
            farmer_name, date_str = option.split(' - ')
            collection = [key for key, value in farmer_names.items() if value == farmer_name][0]  # Find the collection based on farmer name
            if date_str == "No Dates":
                date_str = None
            if collection not in selected_collections:
                selected_collections[collection] = []
            selected_collections[collection].append(date_str)

    # Fetch data and plot charts
    for collection, dates in selected_collections.items():
        if collection == 'demo_db' or "No Dates" in dates or not dates[0]:  # Retrieve all scans for Dananjay Yadav
            docs = db.collection(collection).stream()
        else:
            docs = []
            for date_str in dates:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                start_datetime = datetime.combine(date_obj, datetime.min.time())
                end_datetime = datetime.combine(date_obj, datetime.max.time())
                docs.extend(db.collection(collection)
                            .where('timestamp', '>=', start_datetime)
                            .where('timestamp', '<=', end_datetime)
                            .stream())

        # Process documents and retrieve device names using the DataFrame method
        metadata_list = []
        for doc in docs:
            doc_data = doc.to_dict()
            # Convert datetime values to timezone-unaware
            for key, value in doc_data.items():
                if isinstance(value, datetime):
                    doc_data[key] = value.replace(tzinfo=None)
            metadata_list.append(doc_data)

        # Convert list of dictionaries to DataFrame
        df_metadata = pd.DataFrame(metadata_list)

        # Filter out the required columns including DeviceName
        desired_columns = ['DeviceName', 'InfStat', 'timestamp']
        df_metadata_filtered = df_metadata[desired_columns]

        # Sum up counts based on 'InfStat' for healthy and infected
        healthy_count = df_metadata_filtered[df_metadata_filtered['InfStat'] == 'Healthy'].shape[0]
        infected_count = df_metadata_filtered[df_metadata_filtered['InfStat'] == 'Infected'].shape[0]
        total_scans = healthy_count + infected_count

        # Accumulate counts for combined and data share pie charts
        total_healthy += healthy_count
        total_infected += infected_count
        collection_scan_counts[collection] = total_scans

        # Collect device data
        for _, row in df_metadata_filtered.iterrows():
            device_name = row['DeviceName']
            if pd.isna(device_name):
                continue  # Skip if DeviceName is missing
            date_key = row['timestamp'].strftime('%Y-%m-%d')
            inf_stat = row['InfStat']
            if inf_stat == 'Healthy':
                device_data[device_name][date_key]['Healthy'] += 1
            elif inf_stat == 'Infected':
                device_data[device_name][date_key]['Infected'] += 1
                
    # Layout for the first row (4 columns)
    col1, col2 = st.columns(2)


    # Bar chart showing collections with most infected scans
    if collection_scan_counts:
        farmer_names_list = [farmer_names.get(collection, 'Unknown Farmer') for collection in collection_scan_counts.keys()]
        # Calculate healthy and infected counts for each collection
        healthy_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Healthy') for collection in collection_scan_counts.keys()]
        infected_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Infected') for collection in collection_scan_counts.keys()]

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
    if device_data:
        fig = go.Figure()

        device_names = list(device_data.keys())
        # Collect all device names from selected collections
        for device_name in device_names:
            healthy_values = [device_data[device_name][date]['Healthy'] for date in device_data[device_name].keys()]
            infected_values = [device_data[device_name][date]['Infected'] for date in device_data[device_name].keys()]
            dates = list(device_data[device_name].keys())  # Fetch dates associated with each device

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
