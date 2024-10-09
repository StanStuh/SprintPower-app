import pandas as pd
import streamlit as st
import zipfile
import io

# Function to load data with semicolon delimiter and comma as decimal separator
def load_data(file):
    return pd.read_csv(file, delimiter=';', decimal=',', header=None, names=['Time', 'Distance'])

# Function to create a zip file containing multiple CSVs
def create_zip_file(files):
    zip_buffer = io.BytesIO()  # In-memory buffer
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_name, csv_data in files:
            zf.writestr(file_name, csv_data)
    zip_buffer.seek(0)  # Reset the buffer position to the beginning
    return zip_buffer

# Initialize session state
if 'trimmed_files' not in st.session_state:
    st.session_state.trimmed_files = []

# Upload multiple CSV files
uploaded_files = st.file_uploader("Upload your CSV files", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    # Clear previous trimmed files before processing new uploads
    st.session_state.trimmed_files.clear()

    for idx, uploaded_file in enumerate(uploaded_files):
        st.write(f"Processing file: {uploaded_file.name}")
        
        # Load the data
        data = load_data(uploaded_file)
        
        # Display raw data
        st.write("Raw Data:")
        st.write(data)

        # Input for calibration and sprint length, with unique keys for each file
        s_calibration = st.number_input(f"Enter calibration distance (m) for {uploaded_file.name}", value=3.105, key=f"calibration_{idx}")
        d_sprint = st.number_input(f"Enter sprint length (m) for {uploaded_file.name}", value=30.0, key=f"sprint_{idx}")

        # Find the time point that is 1 second before the calibration distance
        try:
            time_before_calibration = data[data['Distance'] >= s_calibration]['Time'].iloc[0] - 1.0
        except IndexError:
            st.error(f"Error in {uploaded_file.name}: Could not find a point in the data where the distance is greater than or equal to the calibration distance.")
            time_before_calibration = None

        if time_before_calibration:
            # 32 meters of the sprint (s_calibration + d_sprint + 2)
            max_distance = s_calibration + d_sprint + 2

            # Keep data between these time points
            trimmed_data = data[(data['Time'] >= time_before_calibration) & (data['Distance'] <= max_distance)]

            st.write(f"Trimmed Data for {uploaded_file.name}:")
            st.write(trimmed_data)

            # Prepare CSV data for download
            csv_data = trimmed_data.to_csv(index=False, sep=';', decimal=',')
            st.session_state.trimmed_files.append((f"trimmed_{uploaded_file.name}", csv_data))  # Add to the list of files for the ZIP

# If there are trimmed files, add a download button for the ZIP file at the top
if st.session_state.trimmed_files:
    zip_buffer = create_zip_file(st.session_state.trimmed_files)
    st.download_button("Download All Trimmed Files", zip_buffer, "trimmed_files.zip", mime="application/zip")
