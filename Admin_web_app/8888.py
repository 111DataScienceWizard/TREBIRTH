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
    colors = ['#E24E42', '#59C3C3', '#E9B44C']
    
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

    colors = ['red', 'green', 'blue']

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
        font=dict(color="black"),
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
    colors = ['red', 'green', 'blue']

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
        font=dict(color="black"),
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)'  # Transparent background
    )

    st.plotly_chart(fig)
    return fig

def main():
    radar_data_list, timestamps = get_recent_scans(db, num_scans=3)

    if radar_data_list:
        # Preprocess data for each scan
        processed_data_list = preprocess_multiple_scans(radar_data_list)
        
        # Display timestamps of scans
        st.markdown(f"**Timestamps of Recent Scans:** {', '.join([ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps])}")

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




# Mapping collections to farmer images
farmer_images = {
    'TechDemo': 'Admin_web_app/F1.png',
    'Mr.Arjun': 'Admin_web_app/F2.png',
    'DevOps': 'Admin_web_app/F6.png',
    'DevMode': 'Admin_web_app/F4.png',
    'debugging': 'Admin_web_app/F5.png',
    'testing': 'Admin_web_app/F3.png',
    'QDIC_test': 'Admin_web_app/F7.png',
    'demo_db': 'Admin_web_app/F8.png'
}


farmer_names = {
    'TechDemo': 'Dipak Sangamnere',
    'Mr.Arjun': 'Ramesh Kapre',
    'DevOps': 'Arvind Khode',
    'DevMode': 'Ravindra Sambherao',
    'debugging': 'Prabhakr Shirsath',
    'testing': 'Arjun Jachak',
    'QDIC_test': 'Yash More',
    'demo_db': 'Dananjay Yadav'
}

# Farm location mapping
farm_locations = {
    'TechDemo': 'Niphad - Kherwadi',
    'Mr.Arjun': 'Niphad - Panchkeshwar',
    'DevOps': 'Nashik - Indira Nagar',
    'DevMode': 'Manori Khurd',
    'debugging': 'Kundwadi Niphad',
    'testing': 'Pathardi',
    'QDIC_test': 'Niphad - Pimpalgaon',
    'demo_db': 'Rahuri Nashik'
}

# Plot size mapping
plot_sizes = {
    'TechDemo': '1 Acre',
    'Mr.Arjun': '3 Acre',
    'DevOps': '1 Acre',
    'DevMode': '1.5 Acre',
    'debugging': '3 Acre',
    'testing': '1 Acre',
    'QDIC_test': '1 Acre',
    'demo_db': '2.5 Acre'
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
    'demo_db': ['2024-08-23', '2024-08-24'],
    'QDIC_test': ['2024-09-03']
    
}

# Generate dropdown options with collection names and original date format
dropdown_options = []
for collection, dates in collection_dates.items():
    farmer_name = farmer_names.get(collection, 'Unknown Farmer')
    if dates:
        dropdown_options.extend([f"{farmer_name} - {date}" for date in dates])
    else:
        dropdown_options.append(f"{farmer_name} - No Dates")

# Sort dropdown options by newest to oldest
dropdown_options = sorted(dropdown_options, key=lambda x: datetime.strptime(x.split(' - ')[1], '%Y-%m-%d') if 'No Dates' not in x else datetime.min, reverse=True)

# Create dropdown menu
selected_options = st.multiselect('Select farmer plots with Dates', dropdown_options)

if selected_options:
    selected_collections = {}
    total_healthy = 0
    total_infected = 0
    collection_scan_counts = {}
    device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

    for option in selected_options:
        farmer_name, date_str = option.split(' - ')
        collection = [key for key, value in farmer_names.items() if value == farmer_name][0]  # Find the collection based on farmer name
        if date_str == "No Dates":
            date_str = None
        if collection not in selected_collections:
            selected_collections[collection] = []
        selected_collections[collection].append(date_str)

    # Fetch data and plot charts
    for collection, dates in selected_collections.items():
        if "No Dates" in dates or not dates[0]:
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

        healthy_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Healthy')
        infected_count = sum(1 for doc in docs if doc.to_dict().get('InfStat') == 'Infected')
        total_scans = healthy_count + infected_count

        # Accumulate counts for combined and data share pie charts
        total_healthy += healthy_count
        total_infected += infected_count
        collection_scan_counts[collection] = total_scans

        # Collect device data
        for doc in docs:
            doc_data = doc.to_dict()
            device_name = doc_data.get('DeviceName:')
            if not device_name:
                continue  # Skip if DeviceName is missing
            date_key = doc_data['timestamp'].date().strftime('%Y-%m-%d')
            inf_stat = doc_data.get('InfStat', 'Unknown')
            if inf_stat == 'Healthy':
                device_data[device_name][date_key]['Healthy'] += 1
            elif inf_stat == 'Infected':
                device_data[device_name][date_key]['Infected'] += 1

    # Layout for the first row (4 columns)
    col1, col2, col3 = st.columns(3)

    # Pie chart for combined data across all selected collections
    if total_healthy + total_infected > 0:
        fig = go.Figure(data=[go.Pie(
            labels=['Healthy', 'Infected'],
            values=[total_healthy, total_infected],
            hole=0.3,  # To make it a donut chart if desired
            marker=dict(colors=['#00FF00', '#FF0000'])
        )])
        fig.update_layout(
            title_text="Combined Healthy vs Infected Scans",
            font=dict(color='white'),
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            plot_bgcolor='rgba(0,0,0,0)'
        )
        col1.plotly_chart(fig)

        # Pie chart showing data share by each collection
        if collection_scan_counts:
            total_scans_all_collections = sum(collection_scan_counts.values())
            if total_scans_all_collections > 0:
                scan_shares = [count / total_scans_all_collections * 100 for count in collection_scan_counts.values()]
                fig = go.Figure(data=[go.Pie(
                    labels=list(collection_scan_counts.keys()),
                    values=scan_shares,
                    hole=0.3
                )])
                fig.update_layout(
                    title_text="Data Share by Each Collection",
                    font=dict(color='white'),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                col2.plotly_chart(fig)

    # Bar chart showing collections with most infected scans
    if total_infected > 0:
        sorted_collections = sorted(collection_scan_counts.items(), key=lambda item: item[1], reverse=True)
        collections = [item[0] for item in sorted_collections]
        infected_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Infected') for collection in collections]

        fig = go.Figure(data=[go.Bar(
            y=collections,
            x=infected_counts,
            orientation='h',
            marker=dict(color='#FF0000')
        )])
        fig.update_layout(
            title_text="Infected Scans by Collection (Most to Least)",
            xaxis_title="Number of Infected Scans",
            yaxis_title="Collection",
            font=dict(color='white'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        col3.plotly_chart(fig)


    # Layout for the second row (Vertical Bar Chart)
    if device_data:
        fig = go.Figure()
        device_names = list(device_data.keys())
        dates = sorted(set(date for date_counts in device_data.values() for date in date_counts.keys()))

        for device in device_names:
            healthy_counts = []
            infected_counts = []
            
            for date in dates:
                # Safely get the healthy and infected counts for each device on each date
                healthy_count = device_data[device].get(date, {'Healthy': 0, 'Infected': 0})['Healthy']
                infected_count = device_data[device].get(date, {'Healthy': 0, 'Infected': 0})['Infected']
            
                # Append the counts to the respective lists
                healthy_counts.append(healthy_count)
                infected_counts.append(infected_count)

            # Add healthy counts for the device
            fig.add_trace(go.Bar(
                x=dates,
                y=healthy_counts,
                name=f'{device} - Healthy',
                marker=dict(color='#00FF00')  # Green for healthy
            ))

            # Add infected counts for the device
            fig.add_trace(go.Bar(
                x=dates,
                y=infected_counts,
                name=f'{device} - Infected',
                marker=dict(color='#FF0000'),  # Red for infected
                base=healthy_counts  # Stack infected on top of healthy
            ))
            
        fig.update_layout(
            barmode='stack',
            title_text="Scans by Device Across Collections",
            xaxis_title="Date",
            yaxis_title="Number of Scans",
            font=dict(color='white'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend_title_text="Devices",  # Add a title to the legend
            xaxis=dict(tickangle=-45),  # Rotate x-axis labels for better readability
            height = 300
        )
        st.plotly_chart(fig, use_container_width=True)

    # Styled box for comments
    most_active_device = "Sloth's Katana"
    least_active_device = "Proto 2"
    total_infected_trees = 456
    most_infected_plot = "Devmode"
    least_infected_plot = "testing"

    st.markdown(f"""
        <div style="
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 10px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
            font-family: 'Arial', sans-serif;
            color: #333333;
            width: 100%;  /* Take full column width */
            margin-top: 20px;
        ">
            <h4 style="color: #007ACC; margin-bottom: 10px;">Comments</h4>
            <hr style="border: none; height: 1px; background-color: #007ACC; margin-bottom: 10px;">
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
            device_name = doc_data.get('DeviceName:')
            timestamp = doc_data.get('timestamp', None)
        
            if not timestamp:
                continue
        
            date_key = timestamp.date().strftime('%Y-%m-%d')

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

        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            # Display farmer image
            farmer_image = farmer_images.get(collection, 'default.png')
            farmer_name = farmer_names.get(collection, 'Unknown Farmer')
            st.image(farmer_image, width=60, use_column_width=True)
            st.write(f"**Farmer Name:** {farmer_name}", color='white')
    
        with col2:
            # Display scan counts
            st.write(f"**Total Scans:** {total_scans}", color='white')
            st.write(f"**Healthy Scans:** {healthy_count}", color='white')
            st.write(f"**Infected Scans:** {infected_count}", color='white')
            location = farm_locations.get(collection, 'Unknown Location')
            plot_size = plot_sizes.get(collection, 'Unknown Plot Size')
            st.write(f"**Farm Location:** {location}", color='white')
            st.write(f"**Plot Size:** {plot_size}", color='white')

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
                    title_text=f'{collection} - Healthy vs Infected',
                    font=dict(color='white'),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig)

        with col4:
            # Plot vertical bar chart for device scan counts
            fig = go.Figure()

            # Prepare data for the bar chart
            device_names = list(device_data.keys())
            dates = sorted(set(date for date_counts in device_data.values() for date in date_counts.keys()))

            # Add data for each device
            for device_name in device_names:
                healthy_counts = [device_data[device_name].get(date, {'Healthy': 0})['Healthy'] for date in dates]
                infected_counts = [device_data[device_name].get(date, {'Infected': 0})['Infected'] for date in dates]
        
            # Plot healthy counts for the device
            fig.add_trace(go.Bar(
                x=dates,
                y=healthy_counts,
                name=f'{device_name} - Healthy',
                marker=dict(color='#00FF00'),  # Green for healthy
                width=0.1
            ))

            # Plot infected counts for the device
            fig.add_trace(go.Bar(
                x=dates,
                y=infected_counts,
                name=f'{device_name} - Infected',
                marker=dict(color='#FF0000'),  # Red for infected
                base=healthy_counts,  # Stack infected on top of healthy
                width=0.1
            ))

        # Update layout for transparency and appropriate colors
        fig.update_layout(
            barmode='stack',  # Stack bars on top of each other
            title_text=f'{collection} Collection - Device Scan Counts',
            xaxis_title="Date",
            yaxis_title="Number of Scans",
            font=dict(color='white'),  # White font for dark background
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot background
            legend_title_text="Devices",
            height =300,
        )

        # Plot the figure in Streamlit
        st.plotly_chart(fig)


    # Add a button in the middle of the app with larger size
    button_html = """
        <div style="display: flex; justify-content: center; align-items: center; height: 100px;">
            <a href="https://webbapptrebirth-dxf7mxdthdtwclmx6d2mcx.streamlit.app/" target="_blank" style="
                display: inline-block;
                padding: 20px 40px;
                font-size: 24px;
                font-weight: bold;
                background-color: #007ACC;
                color: white;
                text-align: center;
                text-decoration: none;
                border-radius: 10px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            ">
                Go to Next Web App
            </a>
        </div>
    """

    st.markdown(button_html, unsafe_allow_html=True)
