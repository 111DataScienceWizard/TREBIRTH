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
def get_recent_scans(db, num_scans=3):
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
    fig, ax = plt.subplots()
    colors = ['r', 'g', 'b']  # Assign different colors to each scan
    sampling_rate = 100  # Assuming a sampling rate of 100 Hz

    for i, data in enumerate(data_list):
        time_seconds = np.arange(len(data)) / sampling_rate
        ax.plot(time_seconds, data, label=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}', color=colors[i])
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Signal')
    ax.legend()
    st.pyplot(fig)
    return fig

# Plot multiple scans in frequency domain
def plot_multiple_frequency_domain(data_list, timestamps):
    st.write("## Frequency Domain")
    fig, ax = plt.subplots()
    colors = ['r', 'g', 'b']

    for i, data in enumerate(data_list):
        frequencies = np.fft.fftfreq(len(data), d=1/100)
        fft_values = np.fft.fft(data)
        powers = np.abs(fft_values) / len(data)
        powers_db = 20 * np.log10(powers)
        ax.plot(frequencies[:len(frequencies)//2], powers_db[:len(frequencies)//2], label=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}', color=colors[i])
    
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power Spectrum (dB)')
    ax.legend()
    st.pyplot(fig)
    return fig

# Function to plot statistics for multiple scans
def plot_multiple_statistics(stats_dfs, timestamps):
    st.write("## Radar Column Statistics")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['r', 'g', 'b']
    
    for i, stats_df in enumerate(stats_dfs):
        stats_df.plot(kind='bar', ax=ax, alpha=0.6, color=colors[i], label=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}')
    
    ax.set_title('Statistics of Radar Column')
    ax.set_ylabel('Values')
    ax.legend()
    st.pyplot(fig)
    return fig

# Function to convert matplotlib figure to BytesIO for download
def fig_to_bytesio(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    return buffer

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
            time_buffer = fig_to_bytesio(time_fig)
            st.download_button(
                label="Download Time Domain Plot",
                data=time_buffer,
                file_name="time_domain_plot.png",
                mime="image/png"
            )

        # Frequency domain plot for multiple scans
        with col2:
            freq_fig = plot_multiple_frequency_domain([df['Radar'].values for df in processed_data_list], timestamps)
            freq_buffer = fig_to_bytesio(freq_fig)
            st.download_button(
                label="Download Frequency Domain Plot",
                data=freq_buffer,
                file_name="frequency_domain_plot.png",
                mime="image/png"
            )

        # Statistics plot for multiple scans
        with col3:
            stats_dfs = [calculate_statistics(df) for df in processed_data_list]
            stats_fig = plot_multiple_statistics(stats_dfs, timestamps)
            stats_buffer = fig_to_bytesio(stats_fig)
            st.download_button(
                label="Download Statistics Plot",
                data=stats_buffer,
                file_name="statistics_plot.png",
                mime="image/png"
            )
    else:
        st.error("No data available in the 'demo_db' collection.")

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
        fig, ax = plt.subplots(figsize=(3, 2))  # Small plot size
        ax.pie([total_healthy, total_infected], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
        ax.axis('equal')
        ax.set_title('Combined Healthy vs Infected Scans')
        col1.pyplot(fig)

    # Pie chart showing data share by each collection
    if collection_scan_counts:
        total_scans_all_collections = sum(collection_scan_counts.values())
        if total_scans_all_collections > 0:
            scan_shares = [count / total_scans_all_collections * 100 for count in collection_scan_counts.values()]
            fig, ax = plt.subplots(figsize=(3, 2))  # Small plot size
            ax.pie(scan_shares, labels=collection_scan_counts.keys(), autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('Data Share by Each Collection')
            col2.pyplot(fig)

    # Bar chart showing collections with most infected scans
    if total_infected > 0:
        sorted_collections = sorted(collection_scan_counts.items(), key=lambda item: item[1], reverse=True)
        collections = [item[0] for item in sorted_collections]
        infected_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Infected') for collection in collections]

        fig, ax = plt.subplots(figsize=(3, 2))  # Small plot size
        ax.barh(collections, infected_counts, color='#FF0000')
        ax.set_xlabel('Number of Infected Scans')
        ax.set_ylabel('Collection')
        ax.set_title('Infected Scans by Collection (Most to Least)')
        col3.pyplot(fig)


    # Layout for the second row (Vertical Bar Chart)
    if device_data:
        device_names = list(device_data.keys())
        dates = sorted(set(date for date_counts in device_data.values() for date in date_counts.keys()))

        fig, ax = plt.subplots(figsize=(5, 3))  # Small plot size
        for device in device_names:
            counts = [device_data[device].get(date, {'Healthy': 0, 'Infected': 0})['Healthy'] +
                      device_data[device].get(date, {'Healthy': 0, 'Infected': 0})['Infected'] for date in dates]
            ax.bar(dates, counts, label=device)

        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Scans')
        ax.set_title('Scans by Device Across Collections')
        ax.legend(title='Device', bbox_to_anchor=(1.05, 1), loc='upper left')
        fig.autofmt_xdate()  # Rotate date labels
        st.pyplot(fig)

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
            st.write(f"**Farmer Name:** {farmer_name}")
    
        with col2:
            # Display scan counts
            st.write(f"**Total Scans:** {total_scans}")
            st.write(f"**Healthy Scans:** {healthy_count}")
            st.write(f"**Infected Scans:** {infected_count}")
            location = farm_locations.get(collection, 'Unknown Location')
            plot_size = plot_sizes.get(collection, 'Unknown Plot Size')
            st.write(f"**Farm Location:** {location}")
            st.write(f"**Plot Size:** {plot_size}")

        with col3:
        # Plot pie chart for healthy vs infected scans
            if total_scans > 0:
                fig, ax = plt.subplots(figsize=(3, 3))  # Small plot size
                ax.pie([healthy_count, infected_count], labels=['Healthy', 'Infected'], autopct='%1.1f%%', startangle=90, colors=['#00FF00', '#FF0000'])
                ax.axis('equal')
                st.pyplot(fig)

        with col4:
            # Plot vertical bar chart for device scan counts
            fig, ax = plt.subplots(figsize=(3, 3))  # Small plot size for bar chart
        
            # Prepare data for the bar chart
            device_names = list(device_data.keys())
            dates = sorted(set(date for date_counts in device_data.values() for date in date_counts.keys()))
        
            for device_name in device_names:
                counts = [device_data[device_name].get(date, {'Healthy': 0, 'Infected': 0})['Healthy'] +
                          device_data[device_name].get(date, {'Healthy': 0, 'Infected': 0})['Infected'] for date in dates]
                healthy_counts = [device_data[device_name].get(date, {'Healthy': 0, 'Infected': 0})['Healthy'] for date in dates]
                infected_counts = [device_data[device_name].get(date, {'Healthy': 0, 'Infected': 0})['Infected'] for date in dates]
            
                # Plot bars for each device
                ax.bar(dates, healthy_counts, width=0.4, label=f'{device_name} - Healthy', color='#00FF00')
                ax.bar(dates, infected_counts, width=0.4, bottom=healthy_counts, label=f'{device_name} - Infected', color='#FF0000')
        
            # Configure x-axis to show dates
            ax.set_xticks(dates)
            ax.set_xticklabels(dates, rotation=45, ha='right')
        
            # Set labels and legend
            ax.set_xlabel('Date')
            ax.set_ylabel('Number of Scans')
            ax.set_title(f'{collection} Collection - Device Scan Counts')
            ax.legend(loc='upper right', title='Devices')
        
            st.pyplot(fig)


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
