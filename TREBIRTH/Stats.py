## This file calculates the Stats (Mean, Median, Std deviation, PtP Skew and Kurtosis of an Input DF and returns the Stats DF)
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

def calculate_statistics(df):
    stats = {
        'Mean': df.mean(),
        'Median': df.median(),
        'Std Deviation': df.std(),
        'PTP': df.apply(lambda x: np.ptp(x)), 
        'Skewness': skew(df),
        'Kurtosis': kurtosis(df)
    }
    stats_df = pd.DataFrame(stats)
    
    return stats_df
