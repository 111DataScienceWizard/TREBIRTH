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

# Function to apply filter
def apply_filter(data, filter_type, cutoff_freq, sampling_rate=100, stopband_attenuation=60, steepness=0.9999):
    nyquist_freq = 0.5 * sampling_rate
    
    if filter_type == 'LPF' or filter_type == 'HPF':
        normalized_cutoff_freq = cutoff_freq / nyquist_freq
        pass_zero = (filter_type == 'LPF')
        # Design the filter using remez
        numtaps = 2 * int(sampling_rate / cutoff_freq) + 1  # Adjust filter length based on cutoff frequency
        b = signal.remez(numtaps, [0, normalized_cutoff_freq - steepness / 2, normalized_cutoff_freq + steepness / 2, 1], [1, 0], fs=sampling_rate, weight=[1, stopband_attenuation])
    elif filter_type == 'BPF':
        normalized_cutoff_freq = (cutoff_freq[0] / nyquist_freq, cutoff_freq[1] / nyquist_freq)
        # Design the filter using remez
        numtaps = 2 * int(sampling_rate / min(cutoff_freq)) + 1  # Adjust filter length based on minimum cutoff frequency
        b = signal.remez(numtaps, [0, normalized_cutoff_freq[0] - steepness / 2, normalized_cutoff_freq[0] + steepness / 2, normalized_cutoff_freq[1] - steepness / 2, normalized_cutoff_freq[1] + steepness / 2, 1], [0, 1, 0], fs=sampling_rate, weight=[stopband_attenuation, 1, stopband_attenuation])
    
    # Apply the filter
    filtered_data = signal.lfilter(b, 1, data)
    return filtered_data



