import pandas as pd
import streamlit as st
import zipfile
import os

# Function to load data with semicolon delimiter and comma as decimal separator
def load_data(file):
    return pd.read_csv(file, delimiter=';', decimal=',', header=None, names=['Time', 'Distance'])

# Upload multiple CSV files
uploaded_files = st.file_uploader("Upload your CSV files", type=['csv'], accept_multiple_files=True)

# Placeholder for the download button
download_button_placeholder = st.empty()

# Check if any files are uploaded
if uploaded_files:
    # Input for calibration and sprint length
    s_calibration = st.number_input("Enter calibration distance (m)", value=3.105)
    d_sprint = st.number_input("Enter sprint length (m)", value=30.0)

    # Create a temporary directory to store the trimmed files
    os.makedirs("trimmed_data", exist_ok=True)

    # Process each uploaded file
    for uploaded_file in uploaded_files:
        # Load the data
        data = load_data(uploaded_file)
        
        # Display raw data
        st.write(f"Raw Data from {uploaded_file.name}:")
        st.write(data)

        # Find the time point that is 1 second before the calibration distance
        try:
            time_before_calibration = data[data['Distance'] >= s_calibration]['Time'].iloc[0] - 1.0
        except IndexError:
            st.error(f"Error in {uploaded_file.name}: Could not find a point in the data where the distance is greater than or equal to the calibration distance.")
            continue

        # 32 meters of the sprint (s_calibration + d_sprint + 2)
        max_distance = s_calibration + d_sprint + 2

        # Keep data between these time points
        trimmed_data = data[(data['Time'] >= time_before_calibration) & (data['Distance'] <= max_distance)]

        st.write(f"Trimmed Data from {uploaded_file.name}:")
        st.write(trimmed_data)

        # Save the trimmed data to a CSV file
        trimmed_file_path = f"trimmed_data/trimmed_data_{uploaded_file.name}"
        trimmed_data.to_csv(trimmed_file_path, index=False, sep=';', decimal=',', header=False)

    # Create a ZIP file containing all the trimmed data
    zip_filename = "trimmed_data.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for uploaded_file in uploaded_files:
            trimmed_file_path = f"trimmed_data/trimmed_data_{uploaded_file.name}"
            zipf.write(trimmed_file_path, os.path.basename(trimmed_file_path))

    # Provide a download button for the ZIP file
    with open(zip_filename, "rb") as f:
        download_button_placeholder.download_button("Download All Trimmed Data as ZIP", f, zip_filename)

    # Optionally, you can clean up the temporary directory after download
    import shutil
    shutil.rmtree("trimmed_data")
