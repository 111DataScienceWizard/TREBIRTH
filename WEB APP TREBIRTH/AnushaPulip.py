import streamlit as st
import pandas as pd
import numpy as np
from scipy.fft import fft, fftfreq
from scipy import signal
from scipy.signal import spectrogram
import matplotlib.pyplot as plt
from google.cloud import firestore
from io import BytesIO
from datetime import datetime
from scipy.signal import remez, get_window

# Function to apply filter
def apply_filter(data, filter_type, cutoff_freq, sampling_rate=100, stopband_attenuation=60, steepness=0.9999):
    if filter_type == 'LPF' or filter_type == 'HPF':
        numtaps = 2 * int(sampling_rate / cutoff_freq) + 1
        b = signal.remez(numtaps, [0, cutoff_freq - steepness / 2, cutoff_freq + steepness / 2, sampling_rate / 2], [1, 0], fs=sampling_rate, weight=[1, stopband_attenuation])
    elif filter_type == 'BPF':
        numtaps = 2 * int(sampling_rate / min(cutoff_freq)) + 1
        b = signal.remez(numtaps, [0, cutoff_freq[0] - steepness / 2, cutoff_freq[0] + steepness / 2, cutoff_freq[1] - steepness / 2, cutoff_freq[1] + steepness / 2, sampling_rate / 2], [0, 1, 0], fs=sampling_rate, weight=[stopband_attenuation, 1, stopband_attenuation])
    
    window = get_window('hamming', numtaps)
    b *= window
    filtered_data = signal.lfilter(b, 1, data)
    return filtered_data

def plot_frequency_domain_with_filter(data, filter_type, cutoff_freq, sampling_rate=100):
    for column in data.columns:
        st.write(f"## {column} - Frequency Domain with {filter_type} Filter (Cutoff Frequency: {cutoff_freq} Hz)")
        filtered_data = apply_filter(data[column], filter_type, cutoff_freq, sampling_rate=sampling_rate)
        N = len(filtered_data)
        frequencies = fftfreq(N, 1 / sampling_rate)
        fft_values = fft(filtered_data)
        powers = np.abs(fft_values) / N  
        powers_db = 20 * np.log10(powers)  
        fig, ax = plt.subplots()
        ax.plot(frequencies[:N//2], powers_db[:N//2])  
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Power Spectrum (dB)')
        st.pyplot(fig)
        save_button(fig, f"{column}_frequency_domain_{filter_type.lower()}_{cutoff_freq}hz.png")

def plot_time_domain_with_filter(data, filter_type, cutoff_freq, sampling_rate=100):
    for column in data.columns:
        st.write(f"## {column} - Time Domain with {filter_type} Filter (Cutoff Frequency: {cutoff_freq} Hz)")
        filtered_data = apply_filter(data[column], filter_type, cutoff_freq, sampling_rate=sampling_rate)
        fig, ax = plt.subplots()
        time_seconds = np.arange(len(filtered_data)) / sampling_rate
        ax.plot(time_seconds, filtered_data)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Signal')
        st.pyplot(fig)
        save_button(fig, f"{column}_time_domain_{filter_type.lower()}_{cutoff_freq}hz.png")

# Function to plot signals in time domain
def plot_time_domain(data):
    columns = data.columns
    for column in columns:
        st.write(f"## {column} - Time Domain")
        fig, ax = plt.subplots()
        # Calculate time in seconds based on sampling rate
        time_seconds = np.arange(len(data[column])) / sampling_rate
        ax.plot(time_seconds, data[column].values)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Signal')
        st.pyplot(fig)
        save_button(fig, f"{column}_time_domain.png")

# Function to plot signals in frequency domain
def plot_frequency_domain(data):
    columns = data.columns
    for column in columns:
        st.write(f"## {column} - Frequency Domain")
        sensor_name = column.split()[0]  # Get the sensor name (e.g., 'Radar', 'ADXL', etc.)
        frequencies = np.fft.fftfreq(len(data[column]), d=1/100)
        fft_values = np.fft.fft(data[column])
        powers = np.abs(fft_values) / len(data[column])
        powers_db = 20 * np.log10(powers)  
        fig, ax = plt.subplots()
        ax.plot(frequencies[:len(frequencies)//2], powers_db[:len(frequencies)//2])  
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Power Spectrum (dB)')
        st.pyplot(fig)
        save_button(fig, f"{sensor_name}_frequency_domain.png")

def export_filtered_data(filtered_data, filename):
    excel_data = BytesIO()
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        filtered_data.to_excel(writer, sheet_name='Filtered Data', index=False)
    excel_data.seek(0)
    st.download_button("Download Filtered Data", excel_data, file_name=f"{filename}_filtered_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-filtered-data')

# Plot signals based on user selections
def plot_signals(data, domain='all', filter_type=None, cutoff_freq=None):
    if domain == 'none':
        return  # Don't plot any graphs
    
    if domain == 'all':
        domains = ['Time Domain', 'Spectrogram', 'Frequency Domain']
    else:
        domains = [domain]
    
    for domain in domains:
        if domain == 'Time Domain':
            st.subheader('Time Domain Plots')
            if filter_type and cutoff_freq:
                filtered_data = apply_filter(data, filter_type, cutoff_freq)
                filtered_df = pd.DataFrame(filtered_data, columns=data.columns)  # Convert filtered data to DataFrame
                plot_time_domain_with_filter(data, filter_type, cutoff_freq)
                export_filtered_data(filtered_df, "time_domain_filtered_data")
            else:
                plot_time_domain(data)
        elif domain == 'Spectrogram':
            st.subheader('Spectrogram Plots')
            if filter_type == 'None':
                spectrogram_plot(data)
            else:
                st.write("No filter applied for Spectrogram")
        elif domain == 'Frequency Domain':
            st.subheader('Frequency Domain Plots')
            if filter_type and cutoff_freq:
                filtered_data = apply_filter(data, filter_type, cutoff_freq)
                filtered_df = pd.DataFrame(filtered_data, columns=data.columns)  # Convert filtered data to DataFrame
                plot_frequency_domain_with_filter(data, filter_type, cutoff_freq)
                export_filtered_data(filtered_df, "frequency_domain_filtered_data")
            else:
                plot_frequency_domain(data)


# Function to plot spectrogram
def spectrogram_plot(data):
    columns = data.columns

    for i, column in enumerate(columns):
        fig, ax = plt.subplots()
        sensor_name = column.split()[0]
        f, t, Sxx = spectrogram(data[column], fs=100, window='hamming', nperseg=256, noverlap=128, scaling='density')
        pcm = ax.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud')  
        ax.set_ylabel('Frequency [Hz]')
        ax.set_xlabel('Time [s]')
        ax.set_title(f'Spectrogram of {column}')
        cbar = plt.colorbar(pcm, ax=ax, label='Intensity [dB]')  
        st.pyplot(fig)
        save_button(fig, f"{sensor_name}_Spectrogram.png")

# Function to save plotted graphs as PNG
def save_button(fig, filename):
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    st.download_button(
        label="Download Plot as PNG",
        data=buf,
        file_name=filename,
        mime="image/png",
    )

# Define detrend function
def detrend(dataframe):
    detrended_data = dataframe - dataframe.mean()
    return detrended_data

# Define feature extraction functions
def fq(df):
    frequencies = []
    powers = []

    for i in df:
        f, p = signal.welch(df[i], 100, 'flattop', 1024, scaling='spectrum')
        frequencies.append(f)
        powers.append(p)

    frequencies = pd.DataFrame(frequencies)
    powers = pd.DataFrame(powers)
    return frequencies, powers

# Define statistics calculation function for radar data
def stats_radar(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        std_value = np.std(df[column])
        ptp_value = np.ptp(df[column])
        mean_value = np.mean(df[column])
        rms_value = np.sqrt(np.mean(df[column]**2))

        column_result_df = pd.DataFrame({
            "STD": [std_value],
            "PTP": [ptp_value],
            "Mean": [mean_value],
            "RMS": [rms_value]
        })
        result_df = pd.concat([result_df, column_result_df], axis=0)
    return result_df

# Set page configuration
st.set_page_config(layout="wide")
st.title('Data Analytics')
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("Web_App_Trebirth/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# User input for Row No., Tree No., Scan No., and Label
row_number = st.text_input('Enter Row number', 'All')
tree_number = st.text_input('Enter Tree number', 'All')
scan_number = st.text_input('Enter Scan number', 'All')

# Dropdown for InfStat label selection
label_infstat = st.selectbox('Select Label', ['All', 'Infected', 'Healthy'], index=0)

# Dropdown for selecting sheets in Excel
selected_sheets = st.multiselect('Select Sheets', ['Raw Data', 'Detrended Data', 'Normalized Data', 'Detrended & Normalized Data', 'Metadata', 'Time Domain Features', 'Frequency Domain Features'], default=['Raw Data', 'Metadata'])

# User input for plotting
selected_domain = st.selectbox('Select Domain', ['All', 'Time Domain', 'Spectrogram', 'Frequency Domain'], index=0)

# Add user input for filter type and cutoff frequency
filter_type = st.selectbox('Select Filter Type', ['None', 'LPF', 'HPF', 'BPF'])
if filter_type != 'None':
    cutoff_freq = st.slider('Select Cutoff Frequency (Hz)', min_value=1, max_value=50, value=(1, 2) if filter_type == 'BPF' else 1)
    stopband_attenuation = st.slider('Select Stopband Attenuation (dB)', min_value=10, max_value=100, value=60)
    steepness = st.slider('Select Steepness', min_value=0.5, max_value=0.9999, value=0.9999)
else:
    cutoff_freq = None
    stopband_attenuation = 60
    steepness = 0.9999
    
# Set sampling rate and filter order
sampling_rate = 100
order = 51

# Create a reference to the Google post.
query = db.collection('DevOps')

# Filter based on user input
if row_number != 'All':
    query = query.where('RowNo', '==', int(row_number))
if tree_number != 'All':
    query = query.where('TreeNo', '==', int(tree_number))
if scan_number != 'All':
    query = query.where('ScanNo', '==', int(scan_number))
if label_infstat != 'All':
    query = query.where('InfStat', '==', label_infstat)

# Get documents based on the query
query = query.get()

if len(query) == 0:
    st.write("No data found matching the specified criteria.")
else:
    # Create empty lists to store data
    radar_data = []
    adxl_data = []
    ax_data = []
    ay_data = []
    az_data = []
    metadata_list = []

    for doc in query:
        radar_data.append(doc.to_dict().get('RadarRaw', []))
        adxl_data.append(doc.to_dict().get('ADXLRaw', []))
        ax_data.append(doc.to_dict().get('Ax', []))
        ay_data.append(doc.to_dict().get('Ay', []))
        az_data.append(doc.to_dict().get('Az', []))
        metadata = doc.to_dict()
        # Convert datetime values to timezone-unaware
        for key, value in metadata.items():
            if isinstance(value, datetime):
                metadata[key] = value.replace(tzinfo=None)
        metadata_list.append(metadata)

    # Create separate DataFrames for Radar, ADXL, Ax, Ay, Az data
    df_radar = pd.DataFrame(radar_data).transpose().add_prefix('Radar ')
    df_adxl = pd.DataFrame(adxl_data).transpose().add_prefix('ADXL ')
    df_ax = pd.DataFrame(ax_data).transpose().add_prefix('Ax ')
    df_ay = pd.DataFrame(ay_data).transpose().add_prefix('Ay ')
    df_az = pd.DataFrame(az_data).transpose().add_prefix('Az ')

    # Concatenate the DataFrames column-wise
    df_combined = pd.concat([df_radar, df_adxl, df_ax, df_ay, df_az], axis=1)

    # Slice the DataFrame to the desired range
    df_combined = df_combined[100:1800]

    # Drop null values from the combined dataframe
    df_combined.dropna(inplace=True)

    # Impute missing values (if any)
    df_combined.fillna(df_combined.mean(), inplace=True)

    # Detrend all the columns
    df_combined_detrended = df_combined.apply(detrend)

    # Normalize all the columns
    df_combined_normalized = (df_combined_detrended - df_combined_detrended.min()) / (df_combined_detrended.max() - df_combined_detrended.min())

    # Convert list of dictionaries to DataFrame
    df_metadata = pd.DataFrame(metadata_list)

    # Select only the desired columns
    desired_columns = ['TreeSec', 'TreeNo', 'InfStat', 'TreeID', 'RowNo', 'ScanNo', 'timestamp']
    df_metadata_filtered = df_metadata[desired_columns]

    # Construct file name based on user inputs
    file_name_parts = []
    if row_number != 'All':
        file_name_parts.append(f'R{row_number}')
    if tree_number != 'All':
        file_name_parts.append(f'T{tree_number}')
    if scan_number != 'All':
        file_name_parts.append(f'S{scan_number}')

    # Join file name parts with underscore
    file_name = '_'.join(file_name_parts)

    # Convert DataFrame to Excel format
    excel_data = BytesIO()
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        if 'Raw Data' in selected_sheets:
            df_combined.to_excel(writer, sheet_name='Raw Data', index=False)
        if 'Detrended Data' in selected_sheets:
            df_combined_detrended.to_excel(writer, sheet_name='Detrended Data', index=False)
        if 'Normalized Data' in selected_sheets:
            df_combined_normalized.to_excel(writer, sheet_name='Normalized Data', index=False)
        if 'Detrended & Normalized Data' in selected_sheets:
            # Combine detrended and normalized data
            df_combined_detrended_normalized = (df_combined_detrended - df_combined_detrended.min()) / (df_combined_detrended.max() - df_combined_detrended.min())
            df_combined_detrended_normalized.to_excel(writer, sheet_name='Detrended & Normalized Data', index=False)
        if 'Metadata' in selected_sheets:
            df_metadata_filtered.to_excel(writer, sheet_name='Metadata', index=False)
        if 'Time Domain Features' in selected_sheets:
            time_domain_features = stats_radar(df_combined_detrended)
            time_domain_features.to_excel(writer, sheet_name='Time Domain Features', index=False)
        if 'Frequency Domain Features' in selected_sheets:
            frequencies, powers = fq(df_combined_detrended)
            frequencies.to_excel(writer, sheet_name='Frequencies', index=False)
            powers.to_excel(writer, sheet_name='Powers', index=False)

    excel_data.seek(0)

    # Download button for selected sheets and metadata
    st.download_button("Download Selected Sheets and Metadata", excel_data, file_name=f"{file_name}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='download-excel')

    # Plot signals based on user selections
    plot_signals(df_combined_normalized, domain=selected_domain, filter_type=filter_type, cutoff_freq=cutoff_freq)
