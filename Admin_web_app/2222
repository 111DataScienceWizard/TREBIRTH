import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from scipy.signal import welch
from datetime import datetime
from google.cloud import firestore

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

# Plot time domain
def plot_time_domain(data, sampling_rate=100):
    time_seconds = np.arange(len(data)) / sampling_rate  # Assuming 100 samples per second
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(time_seconds, data, color='blue', linewidth=1)
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Amplitude', fontsize=12)
    ax.set_title('Time Domain Plot', fontsize=16)
    ax.grid(True)
    st.pyplot(fig)
    return fig

# Plot frequency domain
def plot_frequency_domain(data, sampling_rate=100):
    # Calculate power spectral density using Welch's method
    freq, power = welch(data, fs=sampling_rate, nperseg=1024)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.semilogy(freq, power, color='red', linewidth=1)
    ax.set_xlabel('Frequency (Hz)', fontsize=12)
    ax.set_ylabel('Power Spectrum Density', fontsize=12)
    ax.set_title('Frequency Domain Plot', fontsize=16)
    ax.grid(True)
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

        # Create two columns for plots
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Time Domain")
            time_fig = plot_time_domain(radar_data)
            time_buffer = fig_to_bytesio(time_fig)
            st.download_button(
                label="Download Time Domain Plot",
                data=time_buffer,
                file_name="time_domain_plot.png",
                mime="image/png"
            )

        with col2:
            st.subheader("Frequency Domain")
            freq_fig = plot_frequency_domain(radar_data)
            freq_buffer = fig_to_bytesio(freq_fig)
            st.download_button(
                label="Download Frequency Domain Plot",
                data=freq_buffer,
                file_name="frequency_domain_plot.png",
                mime="image/png"
            )
    else:
        st.error("No data available in the 'demo_db' collection.")

if __name__ == "__main__":
    main()
