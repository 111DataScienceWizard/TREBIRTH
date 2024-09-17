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
    index_data = []
    for doc in docs:
        data_dict = doc.to_dict()
        radar_raw = data_dict.get('RadarRaw', [])
        timestamp = data_dict.get('timestamp')
        index_radar = data_dict.get('IndexRadar', [])
        radar_data_list.append(radar_raw)
        timestamps.append(timestamp)
        if index_radar:
            index_data.append({
                'IndexRadar': index_radar
            })
    return radar_data_list, timestamps, index_data


# Insert missing packets
def insert_missing_packets(data_list, index_list, packet_size=5, total_packets=200):
    complete_data_list = []
    for data, index in zip(data_list, index_list):
        df_data = pd.DataFrame(data)
        df_index = pd.Series(index)
        
        # Calculate expected indexes
        expected_indexes = list(range(total_packets))
        
        # Identify missing packets
        missing_indexes = list(set(expected_indexes) - set(df_index))
        
        # Insert NaN rows for missing packets
        for mi in missing_indexes:
            start_pos = mi * packet_size
            end_pos = (mi + 1) * packet_size
            insert_df = pd.DataFrame(np.nan, index=range(start_pos, end_pos), columns=df_data.columns)
            df_data = pd.concat([df_data.iloc[:start_pos], insert_df, df_data.iloc[start_pos:]]).reset_index(drop=True)
        
        # Ensure the final length is correct
        df_data = df_data.iloc[:total_packets * packet_size]
        
        complete_data_list.append(df_data)
    
    return complete_data_list

# Process and check data
def process_and_check_data(data_list, index_list, prefix):
    processed_list = []
    for i, (data, index) in enumerate(zip(data_list, index_list)):
        if len(data) != 999:
            missing_packets = 999 - len(data)
            if missing_packets > 200:
                st.write(f"Data packets are lost for {prefix}{i+1}. Please retake the scan.")
                continue
            else:
                data = insert_missing_packets([data], [index])[0]
        df = pd.DataFrame(data)
        df.fillna(df.median(), inplace=True)
        new_columns = [f'{prefix}{i+1}']
        df.columns = new_columns
        processed_list.append(df)
    return pd.concat(processed_list, axis=1) if processed_list else pd.DataFrame()

# Preprocess data for each scan
def preprocess_multiple_scans(radar_data_list, index_data_list):
    processed_data_list = []
    for radar_raw, index_data in zip(radar_data_list, index_data_list):
        processed_df = process_and_check_data([radar_raw], [index_data['IndexRadar']], 'Radar ')
        processed_data_list.append(processed_df)
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
    # Get recent scan data
    radar_data_list, timestamps = get_recent_scans(db, num_scans=2)
    
    # Retrieve index data
    index_data = []
    for doc in get_firestore_data(db.collection('demo_db').stream()):
        if 'IndexRadar' in doc:
            index_data.append({'IndexRadar': doc['IndexRadar']})

    # Check and process data for missing packets
    if radar_data_list:
        index_list = [idx['IndexRadar'] for idx in index_data]
        processed_data_list = process_and_check_data(radar_data_list, index_list, 'Radar ')
        
        # Display timestamps of scans
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
st.write(f"**Farm Location:** Null", color='white')
st.write(f"**Farm Age:** Null", color='white')
st.write(f"**Plot Size:** Null", color='white')
