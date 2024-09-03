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

# Initialize Firestore DB
def initialize_firestore():
    db = firestore.Client.from_service_account_json(
        "WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json"
    )
    return db

# Fetch the most recent scan data from the "demo_db" collection
def get_most_recent_scan(db):
    docs = (
        db.collection('demo_db')
        .order_by('timestamp', direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )
    for doc in docs:
        data_dict = doc.to_dict()
        radar_raw = data_dict.get('RadarRaw', [])
        timestamp = data_dict.get('timestamp')
        return radar_raw, timestamp
    return None, None

# Preprocess data
def preprocess_data(radar_raw):
    df_radar = pd.DataFrame(radar_raw, columns=['Radar'])
    # Drop null values
    df_radar.dropna(inplace=True)
    # Impute missing values with mean if any
    df_radar.fillna(df_radar.mean(), inplace=True)
    return df_radar

# Function to calculate statistics
def calculate_statistics(df):
    df = df.apply(pd.to_numeric, errors='coerce')
    df.fillna(df.mean(), inplace=True)
    stats = {
        'Column': df.columns,
        'Mean': df.mean(),
        'Median': df.median(),
        'Std Deviation': df.std(),
        'PTP': df.apply(lambda x: np.ptp(x)),
        'Skewness': skew(df),
        'Kurtosis': kurtosis(df),
        'Min': df.min(),
        'Max': df.max()
    }
    stats_df = pd.DataFrame(stats)
    return stats_df

def plot_time_domain(data):
    st.write("## Time Domain")
    fig, ax = plt.subplots()
    sampling_rate = 100  # Assuming a sampling rate of 100 Hz
    time_seconds = np.arange(len(data)) / sampling_rate
    ax.plot(time_seconds, data)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Signal')
    st.pyplot(fig)
    return fig

# Function to plot signals in the frequency domain
def plot_frequency_domain(data):
    st.write("## Frequency Domain")
    frequencies = np.fft.fftfreq(len(data), d=1/100)
    fft_values = np.fft.fft(data)
    powers = np.abs(fft_values) / len(data)
    powers_db = 20 * np.log10(powers)
    fig, ax = plt.subplots()
    ax.plot(frequencies[:len(frequencies)//2], powers_db[:len(frequencies)//2])
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power Spectrum (dB)')
    st.pyplot(fig)
    return fig

# Function to plot statistics
def plot_statistics(stats_df):
    st.write("## Radar Column Statistics")
    fig, ax = plt.subplots(figsize=(10, 6))
    stats_df.plot(kind='bar', ax=ax)
    ax.set_title('Statistics of Radar Column')
    ax.set_ylabel('Values')
    st.pyplot(fig)
    return fig

# Function to convert matplotlib figure to BytesIO for download
def fig_to_bytesio(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    return buffer

def main():
    db = initialize_firestore()
    radar_raw, timestamp = get_most_recent_scan(db)

    if radar_raw is not None:
        df_radar = preprocess_data(radar_raw)
        radar_data = df_radar['Radar'].values

        # Display timestamp information
        st.markdown(f"**Timestamp of Latest Scan:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        # Create three columns for plots
        col1, col2, col3 = st.columns(3)

        with col1:
            time_fig = plot_time_domain(radar_data)
            time_buffer = fig_to_bytesio(time_fig)
            st.download_button(
                label="Download Time Domain Plot",
                data=time_buffer,
                file_name="time_domain_plot.png",
                mime="image/png"
            )

        with col2:
            freq_fig = plot_frequency_domain(radar_data)
            freq_buffer = fig_to_bytesio(freq_fig)
            st.download_button(
                label="Download Frequency Domain Plot",
                data=freq_buffer,
                file_name="frequency_domain_plot.png",
                mime="image/png"
            )

        with col3:
            stats_df = calculate_statistics(df_radar)
            stats_fig = plot_statistics(stats_df)
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
