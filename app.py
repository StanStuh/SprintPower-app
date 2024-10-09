import pandas as pd
import streamlit as st
import zipfile
import io

# Function to load data with semicolon delimiter and comma as decimal separator
def load_data(file):
    return pd.read_csv(file, delimiter=';', decimal=',', header=None, names=['Time', 'Distance'])

# Upload multiple CSV files
uploaded_files = st.file_uploader("Upload your CSV files", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    # List to hold all trimmed data and their filenames for the zip
    trimmed_data_files = []
    filenames = []

    for uploaded_file in uploaded_files:
        # Load the data
        data = load_data(uploaded_file)

        # Display raw data for each file
        st.write(f"Raw Data from {uploaded_file.name}:")
        st.write(data)

        # Input for calibration and sprint length
        s_calibration = st.number_input("Enter calibration distance (m)", value=3.105, key=f"calibration_{uploaded_file.name}")
        d_sprint = st.number_input("Enter sprint length (m)", value=30.0, key=f"sprint_{uploaded_file.name}")

        # Find the time point that is 1 second before the calibration distance
        try:
            time_before_calibration = data[data['Distance'] >= s_calibration]['Time'].iloc[0] - 1.0
        except IndexError:
            st.error(f"Error in {uploaded_file.name}: Could not find a point in the data where the distance is greater than or equal to the calibration distance.")
            continue  # Skip this file if an error occurs

        if time_before_calibration:
            # 32 meters of the sprint (s_calibration + d_sprint + 2)
            max_distance = s_calibration + d_sprint + 2

            # Keep data between these time points
            trimmed_data = data[(data['Time'] >= time_before_calibration) & (data['Distance'] <= max_distance)]
            
            st.write(f"Trimmed Data from {uploaded_file.name}:")
            st.write(trimmed_data)

            # Save the trimmed data to a CSV file in memory
            csv_data = trimmed_data.to_csv(index=False, sep=';', decimal=',', header=False)
            trimmed_data_files.append(csv_data.encode())  # Store bytes in list
            filenames.append(f"trimmed_data_{uploaded_file.name}.csv")

    if trimmed_data_files:
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for file_data, filename in zip(trimmed_data_files, filenames):
                zip_file.writestr(filename, file_data)

        # Move to the beginning of the BytesIO buffer
        zip_buffer.seek(0)

        # Provide a button to download the ZIP file
        st.download_button("Download All Trimmed Data as ZIP", zip_buffer, "trimmed_data.zip", file_name="trimmed_data.zip")
