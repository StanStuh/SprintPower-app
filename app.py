import pandas as pd
import streamlit as st
import zipfile
import os
import numpy as np
import matplotlib.pyplot as plt

# Function to load data with semicolon delimiter and comma as decimal separator
def load_data(file):
    return pd.read_csv(file, delimiter=';', decimal=',', header=None, names=['Time', 'Distance'])

# Function to calculate raw speed (v_sur)
def calculate_raw_speed(data):
    delta_distance = data['Distance'].diff()
    delta_time = data['Time'].diff()
    v_sur = delta_distance / delta_time
    return v_sur

# Function to apply moving average filter (two-step smoothing)
def moving_average_filter(v_sur, A=5, B=8):
    v_avg = v_sur.copy()
    for _ in range(A):
        v_avg = v_avg.rolling(window=2 * B + 1, min_periods=1, center=True).mean()
    return v_avg

# Function to apply a new moving average filter for a given column
def filter_column(data, A, B):
    v_filtered = data.copy()
    for _ in range(A):
        v_filtered = v_filtered.rolling(window=2 * B + 1, min_periods=1, center=True).mean()
    return v_filtered

# Function to replace out-of-tolerance values
def replace_out_of_tolerance(data, tolerance):
    data['v_sur_nad'] = data['v_avg58'] + tolerance
    data['v_sur_pod'] = data['v_avg58'] - tolerance
    data['v_znotraj_tol'] = data['v_sur']

    for index in range(1, len(data)):
        if data['v_sur'].iloc[index] > data['v_sur_nad'].iloc[index]:
            data['v_znotraj_tol'].iloc[index] = data['v_znotraj_tol'].iloc[index - 1]
        elif data['v_sur'].iloc[index] < data['v_sur_pod'].iloc[index]:
            data['v_znotraj_tol'].iloc[index] = data['v_znotraj_tol'].iloc[index - 1]

    return data

# Function to calculate distance from speed
def calculate_distance_from_speed(data):
    delta_time = data['Time'].diff()
    distance_covered = data['v_znotraj_tol_filtered_3_3'] * delta_time
    return distance_covered.cumsum()

# Function to calculate acceleration from speed
def calculate_acceleration(data, speed_column):
    delta_time = data['Time'].diff()
    acceleration = data[speed_column].diff() / delta_time
    return acceleration

# Upload multiple CSV files
uploaded_files = st.file_uploader("Upload your CSV files", type=['csv'], accept_multiple_files=True)

# Placeholder for the download button
download_button_placeholder = st.empty()

# Initialize a variable to control the legend visibility
show_legend = st.checkbox("Show Legend", value=True)

# Check if any files are uploaded
if uploaded_files:
    s_calibration = st.number_input("Enter calibration distance (m)", value=3.105)
    d_sprint = st.number_input("Enter sprint length (m)", value=30.0)

    os.makedirs("trimmed_data", exist_ok=True)
    all_trimmed_data = []

    for uploaded_file in uploaded_files:
        data = load_data(uploaded_file)

        st.write(f"Raw Data from {uploaded_file.name}:")
        st.write(data)

        try:
            time_before_calibration = data[data['Distance'] >= s_calibration]['Time'].iloc[0] - 1.0
        except IndexError:
            st.error(f"Error in {uploaded_file.name}: Could not find a point in the data where the distance is greater than or equal to the calibration distance.")
            continue

        max_distance = s_calibration + d_sprint + 2
        trimmed_data = data[(data['Time'] >= time_before_calibration) & (data['Distance'] <= max_distance)]

        trimmed_data['v_sur'] = calculate_raw_speed(trimmed_data)
        trimmed_data['v_avg58'] = moving_average_filter(trimmed_data['v_sur'])

        if not trimmed_data['v_sur'].isnull().all():
            trimmed_data['v_sur'].iloc[0] = trimmed_data['v_sur'].iloc[1]

        tolerance = st.number_input(f"Enter tolerance value for {uploaded_file.name}", value=2, min_value=0, key=f"tolerance_{uploaded_file.name}")
        trimmed_data = replace_out_of_tolerance(trimmed_data, tolerance)

        columns_order = ['Time', 'Distance', 'v_sur', 'v_avg58', 'v_sur_nad', 'v_sur_pod', 'v_znotraj_tol']
        trimmed_data = trimmed_data[columns_order]

        trimmed_data['v_znotraj_tol_filtered_9_9'] = filter_column(trimmed_data['v_znotraj_tol'], A=9, B=9)
        trimmed_data['v_znotraj_tol_filtered_3_3'] = filter_column(trimmed_data['v_znotraj_tol'], A=3, B=3)
        trimmed_data['Distance_Covered'] = calculate_distance_from_speed(trimmed_data)

        if not trimmed_data['Distance_Covered'].isnull().all():
            trimmed_data['Distance_Covered'].iloc[0] = trimmed_data['Distance_Covered'].iloc[1]
            trimmed_data['Distance_Covered'].iloc[-1] = trimmed_data['Distance_Covered'].iloc[-2]

        trimmed_data['Acceleration_8'] = calculate_acceleration(trimmed_data, 'v_znotraj_tol_filtered_9_9')
        trimmed_data['Acceleration_9'] = calculate_acceleration(trimmed_data, 'v_znotraj_tol_filtered_3_3')

        columns_order_with_filtered = ['Time', 'Distance', 'v_sur', 'v_avg58', 'v_sur_nad', 'v_sur_pod', 'v_znotraj_tol', 'v_znotraj_tol_filtered_9_9', 'v_znotraj_tol_filtered_3_3', 'Distance_Covered', 'Acceleration_8', 'Acceleration_9']
        trimmed_data = trimmed_data[columns_order_with_filtered]

        trimmed_data['Adjusted_Distance'] = trimmed_data['Distance'] - s_calibration
        all_trimmed_data.append(trimmed_data)

    # Plot all speed curves together for distances from 0 to 30 meters
    plt.figure(figsize=(12, 6))
    for trimmed_data, uploaded_file in zip(all_trimmed_data, uploaded_files):
        plt.plot(trimmed_data['Adjusted_Distance'], trimmed_data['v_znotraj_tol_filtered_9_9'], label=f'Speed for {uploaded_file.name}')
    
    plt.title('Speed Curves for All Files')
    plt.xlabel('Distance (m)')
    plt.ylabel('Speed (m/s)')
    plt.xlim(0, 30)
    plt.ylim(0, max(trimmed_data['v_znotraj_tol_filtered_9_9'].max() for trimmed_data in all_trimmed_data) * 1.1)
    plt.axhline(0, color='black', linewidth=0.5, linestyle='--')
    plt.axvline(0, color='black', linewidth=0.5, linestyle='--')
    plt.grid()

    # Display legend based on the checkbox
    if show_legend:
        plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2)

    plt.tight_layout()

    # Display the combined plot in Streamlit below the download button
    st.pyplot(plt)
    plt.clf()

    # Create a ZIP file containing all the trimmed data
    zip_filename = "trimmed_data.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for uploaded_file in uploaded_files:
            trimmed_file_path = f"trimmed_data/trimmed_data_{uploaded_file.name}"
            zipf.write(trimmed_file_path, os.path.basename(trimmed_file_path))

    # Provide a download button for the ZIP file
    with open(zip_filename, "rb") as f:
        download_button_placeholder.download_button("Download All Trimmed Data as ZIP", f, file_name=zip_filename, mime="application/zip")
