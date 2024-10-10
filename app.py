import pandas as pd
import streamlit as st
import zipfile
import os
import numpy as np

# Function to load data with semicolon delimiter and comma as decimal separator
def load_data(file):
    return pd.read_csv(file, delimiter=';', decimal=',', header=None, names=['Time', 'Distance'])

# Function to calculate raw speed
def calculate_raw_speed(data):
    data['v_sur'] = data['Distance'].diff() / data['Time'].diff()
    return data

# Function to smooth speed with moving average filter
def moving_average_smoothing(data, A, B):
    for _ in range(A):
        data['v_sur'] = data['v_sur'].rolling(window=2*B+1, min_periods=1, center=True).mean()
    return data

# Function to replace out-of-tolerance values
def replace_out_of_tolerance(data, tolerance):
    v_sur_plus = data['v_sur'].mean() + tolerance
    v_sur_minus = data['v_sur'].mean() - tolerance
    
    for i in range(1, len(data)):
        if data.loc[i, 'v_sur'] > v_sur_plus or data.loc[i, 'v_sur'] < v_sur_minus:
            data.loc[i, 'v_sur'] = data.loc[i-1, 'v_sur']  # Replace with the previous in-tolerance value
    
    return data

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

    processed_files = []
    
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
        
        processed_files.append(trimmed_data)

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

    # Button to calculate raw speed after trimming
    if st.button("izračunaj surovo hitrost za vse odprte"):
        for i, data in enumerate(processed_files):
            processed_files[i] = calculate_raw_speed(data)
            # Smoothing
            processed_files[i] = moving_average_smoothing(processed_files[i], A=5, B=8)
            st.write(f"Processed Data with Raw Speed from file {uploaded_files[i].name}:")
            st.write(processed_files[i])
        
    # Tolerance input and button to replace out-of-tolerance values after trimming
    tolerance = st.number_input("Vnesite toleranco", value=2)
    if st.button("nadomesti vse izven tolerance"):
        for i, data in enumerate(processed_files):
            processed_files[i] = replace_out_of_tolerance(processed_files[i], tolerance)
            st.write(f"Data with Tolerance Applied from file {uploaded_files[i].name}:")
            st.write(processed_files[i])
