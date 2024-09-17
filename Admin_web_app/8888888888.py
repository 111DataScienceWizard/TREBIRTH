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
def get_recent_scans(db, num_scans=3):
    docs = (
        db.collection('demo_db')
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(num_scans)
        .stream()
    )
    radar_data_list = []
    timestamps = []
    device_names = []
    for doc in docs:
        data_dict = doc.to_dict()
        radar_raw = data_dict.get('RadarRaw', [])
        timestamp = data_dict.get('timestamp')
        device_name = data_dict.get('DeviceName', 'Unknown')  # Ensure to handle missing device names
        radar_data_list.append(radar_raw)
        timestamps.append(timestamp)
        device_names.append(device_name)
    return radar_data_list, timestamps, device_names

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
        'PTP': df.apply(lambda x: np.ptp(x)),
        'Min': df.min(),
        'Max': df.max()
    }
    stats_df = pd.DataFrame(stats)
    return stats_df

# Plot multiple scans in time domain
def plot_multiple_time_domain(data_list, timestamps):
    st.write("## Time Domain")
    fig = go.Figure()
    colors = ['green', 'blue']
    for i, data in enumerate(data_list):
        fig.add_trace(go.Scatter(
            y=data,
            mode='lines',
            name=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}',
            line=dict(color=colors[i])
        ))
    fig.update_layout(
        template='plotly_white',
        xaxis_title="Index",
        yaxis_title="Signal",
        legend_title="Scans",
        font=dict(color="black"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig)
    return fig
    
# Plot multiple scans in frequency domain using Plotly
def plot_multiple_frequency_domain(data_list, timestamps):
    st.write("## Frequency Domain")
    fig = go.Figure()
    colors = ['green', 'blue']
    for i, data in enumerate(data_list):
        frequencies = np.fft.fftfreq(len(data), d=1/100)
        fft_values = np.fft.fft(data)
        powers = np.abs(fft_values) / len(data)
        powers_db = 20 * np.log10(powers)
        fig.add_trace(go.Scatter(
            x=frequencies[:len(frequencies)//2],
            y=powers_db[:len(powers_db)//2],
            mode='lines',
            name=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}',
            line=dict(color=colors[i])
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
                y=[stats_df[measure].values[0] for measure in stats_measures],
                name=f'Scan {i+1} - {timestamps[i].strftime("%Y-%m-%d %H:%M:%S")}',
                marker_color=colors[i],
            ))
    fig.update_layout(
        barmode='group',
        template='plotly_white',
        xaxis_title="Statistics",
        yaxis_title="Values",
        font=dict(color="white"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig)
    return fig

def main():
    radar_data_list, timestamps, device_names = get_recent_scans(db, num_scans=3)

    if radar_data_list:
        # Determine device names and indices for plotting
        device_counts = pd.Series(device_names).value_counts()
        most_common_device = device_counts.idxmax()
        most_common_device_count = device_counts.max()
        
        if most_common_device_count >= 2:
            # Filter scans for the most common device
            same_device_indices = [i for i, device in enumerate(device_names) if device == most_common_device]
            if len(same_device_indices) >= 2:
                indices_to_plot = same_device_indices[:2]  # Plot the 2 most recent scans with the same device
            else:
                indices_to_plot = same_device_indices
        else:
            # All 3 devices are different or not enough scans with the same device
            indices_to_plot = list(range(min(2, len(radar_data_list))))  # Plot the 2 most recent scans if available

        # Preprocess data for each scan
        processed_data_list = preprocess_multiple_scans([radar_data_list[i] for i in indices_to_plot])
        
        # Display timestamps of scans
        st.markdown(f"**DATA ANALYSIS OF SELECTED SCANS**")
        
        # Create three columns for plots
        col1, col2, col3 = st.columns(3)

        # Time domain plot for selected scans
        with col1:
            time_fig = plot_multiple_time_domain([df['Radar'].values for df in processed_data_list], [timestamps[i] for i in indices_to_plot])
        
        # Frequency domain plot for selected scans
        with col2:
            freq_fig = plot_multiple_frequency_domain([df['Radar'].values for df in processed_data_list], [timestamps[i] for i in indices_to_plot])
        
        # Statistics plot for selected scans
        with col3:
            stats_dfs = [calculate_statistics(df) for df in processed_data_list]
            stats_fig = plot_multiple_statistics(stats_dfs, [timestamps[i] for i in indices_to_plot])

if __name__ == "__main__":
    main()
