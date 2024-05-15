# Function to export filtered column values to Excel
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
                plot_time_domain_with_filter(data, filter_type, cutoff_freq)
                export_filtered_data(filtered_data, "time_domain_filtered_data")
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
                plot_frequency_domain_with_filter(data, filter_type, cutoff_freq)
                export_filtered_data(filtered_data, "frequency_domain_filtered_data")
            else:
                plot_frequency_domain(data)
