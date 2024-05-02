import streamlit as st
import pandas as pd
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

# Function to plot signals
def plot_signals(data, domain='all', columns='all'):
    if domain == 'all':
        domains = ['Time Domain', 'Frequency Domain']
    else:
        domains = [domain]
    
    for domain in domains:
        if domain == 'Time Domain':
            st.subheader('Time Domain Plots')
            plot_time_domain(data, columns)
        elif domain == 'Frequency Domain':
            st.subheader('Frequency Domain Plots')
            plot_frequency_domain(data, columns)

# Function to plot signals in time domain
def plot_time_domain(data, columns):
    if columns == 'all':
        columns = data.columns
    
    for column in columns:
        st.write(f"## {column} - Time Domain")
        fig, ax = plt.subplots()
        ax.plot(data.index, data[column])
        st.pyplot(fig)
        save_button(fig, f"{column}_time_domain.png")

# Function to plot signals in frequency domain
def plot_frequency_domain(data, columns):
    if columns == 'all':
        columns = data.columns
    
    for column in columns:
        st.write(f"## {column} - Frequency Domain")
        frequencies, powers = fq(data[column])
        fig, ax = plt.subplots()
        ax.plot(frequencies, powers)
        st.pyplot(fig)
        save_button(fig, f"{column}_frequency_domain.png")

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

# Rest of your code...

# User input for plotting
selected_domain = st.selectbox('Select Domain', ['All', 'Time Domain', 'Frequency Domain'], index=0)
selected_columns = st.multiselect('Select Columns to Plot', ['Radar', 'ADXL', 'Ax', 'Ay', 'Az'], default=['Radar', 'ADXL', 'Ax', 'Ay', 'Az'])

# Plot signals based on user selections
plot_signals(df_combined_detrended, domain=selected_domain, columns=selected_columns)
