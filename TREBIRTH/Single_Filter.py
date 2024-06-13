import pandas as pd
import numpy as np

def process(coef, in_signal):
    FILTERTAPS = len(coef)  # Calculate the number of filter taps based on the length of coef
    values = in_signal[:FILTERTAPS].copy()  # Initialize the values list with a copy of the input signal, truncated to FILTERTAPS
    k = 0  # Initialize k to 0
    out_signal = []  # Initialize an empty list to store the output signal
    gain = 1.0  # Assuming gain is fixed
    for in_value in in_signal:  # Iterate over the entire input signal
        out = 0.0  # Initialize output for current input value
        values[k] = in_value  # Store the input value in the buffer
        for i in range(len(coef)):
            out += coef[i] * values[(i + k) % FILTERTAPS]  # Apply filter coefficients
        out /= gain  # Scale the output
        k = (k + 1) % FILTERTAPS  # Update buffer position
        out_signal.append(out)  # Append the filtered output to the output signal list
    return out_signal  # Return the filtered signal

Healthy = pd.read_csv("/content/Healthy_Radar.csv",header = None ,index_col=None).iloc[:, 0]
Infected = pd.read_csv("/content/Infected_Radar.csv",header = None, index_col=None).iloc[:, 0]

Healthy = Healthy.dropna()

LPF_coefs = pd.read_excel("Coefs_LPF.xlsx", index_col=None)
HPF_coefs = pd.read_excel("Coefs_HPF.xlsx", index_col=None)
LPF_5Hz = LPF_coefs['5Hz LPF']
LPF_10Hz = LPF_coefs['10Hz LPF']
LPF_15Hz = LPF_coefs['15Hz LPF']
LPF_20Hz = LPF_coefs['20Hz LPF']
LPF_25Hz = LPF_coefs['25Hz LPF']
LPF_30Hz = LPF_coefs['30Hz LPF']
LPF_35Hz = LPF_coefs['35Hz LPF']
LPF_40Hz = LPF_coefs['40Hz LPF']
LPF_45Hz = LPF_coefs['45Hz LPF']
LPF_50Hz = LPF_coefs['50Hz LPF']
HPF_5Hz = HPF_coefs['5Hz HPF']
HPF_10Hz = HPF_coefs['10Hz HPF']
HPF_15Hz = HPF_coefs['15Hz HPF']
HPF_20Hz = HPF_coefs['20Hz HPF']
HPF_25Hz = HPF_coefs['25Hz HPF']
HPF_30Hz = HPF_coefs['30Hz HPF']
HPF_35Hz = HPF_coefs['35Hz HPF']
HPF_40Hz = HPF_coefs['40Hz HPF']
HPF_45Hz = HPF_coefs['45Hz HPF']
HPF_50Hz = HPF_coefs['50Hz HPF']

# example
LPF_10Hz_Healthy = process(LPF_10Hz,Healthy)
