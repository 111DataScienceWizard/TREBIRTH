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

def stats_radar(df):
    result_df = pd.DataFrame()

    for column in df.columns:
        std_list, ptp_list, mean_list, rms_list = [], [], [], []

        std_value = np.std(df[column])
        ptp_value = np.ptp(df[column])
        mean_value = np.mean(df[column])
        rms_value = np.sqrt(np.mean(df[column]**2))

        std_list.append(std_value)
        ptp_list.append(ptp_value)
        mean_list.append(mean_value)
        rms_list.append(rms_value)

        column_result_df = pd.DataFrame({
            "STD": std_list,
            "PTP": ptp_list,
            "Mean": mean_list,
            "RMS": rms_list
        })
        result_df = pd.concat([result_df, column_result_df], axis=0)
    return result_df

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

# Define filtering functions
def process(coef, in_signal):
    FILTERTAPS = len(coef)
    values = in_signal[:FILTERTAPS].copy()
    k = 0
    out_signal = []
    gain = 1.0
    for in_value in in_signal:
        out = 0.0
        values[k] = in_value
        for i in range(len(coef)):
            out += coef[i] * values[(i + k) % FILTERTAPS]
        out /= gain
        k = (k + 1) % FILTERTAPS
        out_signal.append(out)
    return out_signal

def allfiltering(input_signal):
    LPF_outputs = {}
    HPF_outputs = {}

    LPF_outputs['LPF5Hz'] = process(coefLPF5Hz, input_signal)
    LPF_outputs['LPF10Hz'] = process(coefLPF10Hz, input_signal)
    LPF_outputs['LPF15Hz'] = process(coefLPF15Hz, input_signal)
    LPF_outputs['LPF20Hz'] = process(coefLPF20Hz, input_signal)
    LPF_outputs['LPF25Hz'] = process(coefLPF25Hz, input_signal)
    LPF_outputs['LPF30Hz'] = process(coefLPF30Hz, input_signal)
    LPF_outputs['LPF35Hz'] = process(coefLPF35Hz, input_signal)
    LPF_outputs['LPF40Hz'] = process(coefLPF40Hz, input_signal)
    LPF_outputs['LPF45Hz'] = process(coefLPF45Hz, input_signal)
    LPF_outputs['LPF50Hz'] = process(coefLPF50Hz, input_signal)

    HPF_outputs['HPF5Hz'] = process(coefHPF5Hz, input_signal)
    HPF_outputs['HPF10Hz'] = process(coefHPF10Hz, input_signal)
    HPF_outputs['HPF15Hz'] = process(coefHPF15Hz, input_signal)
    HPF_outputs['HPF20Hz'] = process(coefHPF20Hz, input_signal)
    HPF_outputs['HPF25Hz'] = process(coefHPF25Hz, input_signal)
    HPF_outputs['HPF30Hz'] = process(coefHPF30Hz, input_signal)
    HPF_outputs['HPF35Hz'] = process(coefHPF35Hz, input_signal)
    HPF_outputs['HPF40Hz'] = process(coefHPF40Hz, input_signal)
    HPF_outputs['HPF45Hz'] = process(coefHPF45Hz, input_signal)
    HPF_outputs['HPF50Hz'] = process(coefHPF50Hz, input_signal)

    all_outputs = pd.DataFrame({**LPF_outputs, **HPF_outputs})
    return all_outputs

def apply_allfiltering_to_columns(df):
    output_dfs = []
    for column in df.columns:
        input_signal = df[column]
        filtered_output = allfiltering(input_signal)
        filtered_output.columns = [f"{column}_{col}" for col in filtered_output.columns]
        output_dfs.append(filtered_output)
    return pd.concat(output_dfs, axis=1)
