import pandas as pd 
import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import skew, kurtosis

def detrend(dataframe):
    detrended_data = dataframe - dataframe.mean()
    return detrended_data

# Define feature extraction functions
def fq(df):
    frequencies = []
    powers = []

    for i in df.columns:
        f, p = signal.welch(df[i], 100, 'flattop', 850, scaling='spectrum')
        frequencies.append(f[1:])
        powers.append(p[1:])

    frequencies_df = pd.DataFrame(frequencies).transpose()
    powers_df = pd.DataFrame(powers).transpose()
    return frequencies_df, powers_df

def stats_radar(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        column_list, std_list, ptp_list, median_list, mean_list, Skewness_list, Kurtosis_list, Min_list, Max_list = [], [], [], [], [], [], [], [], []
        df[column] = pd.to_numeric(df[column], errors='coerce')
        df[column].fillna(df[column].mean(), inplace=True)

        
        std_value = np.std(df[column])
        ptp_value = np.ptp(df[column])
        mean_value = np.mean(df[column])
        median_value = np.median(df[column])
        Skewness_value = skew(df[column])
        Kurtosis_value = kurtosis(df[column])
        Min_value = np.min(df[column])
        Max_value = np.max(df[column])
        #rms_value = np.sqrt(np.mean(df[column]**2))

        column_list.append(f"{column}")
        std_list.append(std_value)
        ptp_list.append(ptp_value)
        median_list.append(median_value)
        #rms_list.append(rms_value)
        mean_list.append(mean_value)
        Skewness_list.append(Skewness_value)
        Kurtosis_list.append(Kurtosis_value)
        Min_list.append(Min_value)
        Max_list.append(Max_value)
        
        column_result_df = pd.DataFrame({
            "Column": column_list,
            "STD Deviation": std_list,
            "PTP": ptp_value,
            "Mean": mean_list,
            "Median": median_list,
            "Skewness": Skewness_list,
            "Kurtosis": Kurtosis_list,
            "Min": Min_list,
            "Max": Max_list
            #"RMS": rms_list
        })
        result_df = pd.concat([result_df, column_result_df], axis=0)
    return result_df
    
def calculate_statistics(df):
    df = df.apply(pd.to_numeric, errors='coerce')
    df.fillna(df.median(), inplace=True)
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

def stats_filtereddata(df, band):
    stats = {
        "Band": [],
        "STD": [],
        "PTP": [],
        "Mean": [],
        "RMS": [],
        "Skew": [],
        "Kurtosis": []
    }

    for column in df.columns:
        # Ensure the column is numeric and handle NaN values
        df[column] = pd.to_numeric(df[column], errors='coerce')
        df[column].fillna(df[column].mean(), inplace=True)
      
        stats["Band"].append(f"{band} {column}")
        stats["STD"].append(np.std(df[column]))
        stats["PTP"].append(np.ptp(df[column]))
        stats["Mean"].append(np.mean(df[column]))
        stats["RMS"].append(np.sqrt(np.mean(df[column]**2)))
        stats["Skew"].append(skew(df[column]))
        stats["Kurtosis"].append(kurtosis(df[column]))

    return pd.DataFrame(stats)

# Define function to compare columns
def columns_reports_unique(df):
    report = []
    num_columns = len(df.columns)
    for i in range(num_columns):
        for j in range(i + 1, num_columns):  # Start j from i + 1
            column1 = df.columns[i]
            column2 = df.columns[j]
            diff = df[column1] - df[column2]
            mean_diff = np.mean(diff)
            deviation_diff = np.std(diff)
            ptp_diff = np.ptp(diff)
            skewness_diff = skew(diff)
            correlation = df[[column1, column2]].corr().iloc[0, 1]
            report.append({
                'Column 1': column1,
                'Column 2': column2,
                'Mean Difference': mean_diff,
                'Deviation Difference': deviation_diff,
                'PTP Difference': ptp_diff,
                'Skewness Difference': skewness_diff,
                'Correlation': correlation,
            })
    report_df = pd.DataFrame(report)
    return report_df
