def spectrogram_plot(data):
    columns = data.columns
    plots = []  # List to store plots

    for i, column in enumerate(columns):
        fig, ax = plt.subplots()
        sensor_name = column.split()[0]
        f, t, Sxx = spectrogram(data[column], fs=100, window='hamming', nperseg=256, noverlap=128, scaling='density')
        pcm = ax.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud')  # Applying logarithmic scale
        ax.set_ylabel('Frequency [Hz]')
        ax.set_xlabel('Time [s]')
        ax.set_title(f'Spectrogram of {column}')
        plt.colorbar(pcm, ax=ax, label='Intensity [dB]')  # Set color scale
        plots.append(fig)  # Append the plot to the list

    for plot in plots:
        st.pyplot(plot)
        save_button(plot, f"{sensor_name}_Spectrogram.png")
