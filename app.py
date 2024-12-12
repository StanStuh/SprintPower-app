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
    v_avg = v_sur.copy()  # Make sure we don't modify v_sur
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

    # Create a new column for v_znotraj_tol in the 7th column
    data['v_znotraj_tol'] = data['v_sur']  # This will be moved to the 7th column later

    # Replace out-of-tolerance values with the nearest previous value
    for index in range(1, len(data)):
        if data['v_sur'].iloc[index] > data['v_sur_nad'].iloc[index]:
            data['v_znotraj_tol'].iloc[index] = data['v_znotraj_tol'].iloc[index - 1]
        elif data['v_sur'].iloc[index] < data['v_sur_pod'].iloc[index]:
            data['v_znotraj_tol'].iloc[index] = data['v_znotraj_tol'].iloc[index - 1]

    return data

# Function to calculate distance from speed
def calculate_distance_from_speed(data):
    # Calculate the time differences
    delta_time = data['Time'].diff()
    # Calculate the distance based on the speed in the 9th column (v_znotraj_tol_filtered_3_3)
    distance_covered = data['v_znotraj_tol_filtered_3_3'] * delta_time
    return distance_covered.cumsum()  # Cumulative sum to get the total distance covered

# Function to calculate acceleration from speed
def calculate_acceleration(data, speed_column):
    # Calculate the time differences
    delta_time = data['Time'].diff()
    # Calculate the acceleration (change in speed over change in time)
    acceleration = data[speed_column].diff() / delta_time
    return acceleration

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

    # Initialize a list to store the trimmed data for plotting
    all_trimmed_data = []

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

        # Calculate raw speed (v_sur)
        trimmed_data['v_sur'] = calculate_raw_speed(trimmed_data)

        # Apply the moving average filter to v_sur and store in the fourth column (v_avg58)
        trimmed_data['v_avg58'] = moving_average_filter(trimmed_data['v_sur'])

        # Copy the first value of v_sur from the second value
        if not trimmed_data['v_sur'].isnull().all():  # Ensure there are no NaN values in v_sur
            trimmed_data['v_sur'].iloc[0] = trimmed_data['v_sur'].iloc[1]  # Copy the second value to the first

        # Initialize the 7th column (v_znotraj_tol) with the original v_sur values
        tolerance = st.number_input(f"Enter tolerance value for {uploaded_file.name}", value=2, min_value=0, key=f"tolerance_{uploaded_file.name}")
        trimmed_data = replace_out_of_tolerance(trimmed_data, tolerance)

        # Shift the v_znotraj_tol column to the 7th position
        columns_order = ['Time', 'Distance', 'v_sur', 'v_avg58', 'v_sur_nad', 'v_sur_pod', 'v_znotraj_tol']
        trimmed_data = trimmed_data[columns_order]

        # Apply the moving average filter (A=9, B=9) to the 7th column and store in the 8th column
        trimmed_data['v_znotraj_tol_filtered_9_9'] = filter_column(trimmed_data['v_znotraj_tol'], A=9, B=9)

        # Apply the moving average filter (A=3, B=3) to the 7th column and store in the 9th column
        trimmed_data['v_znotraj_tol_filtered_3_3'] = filter_column(trimmed_data['v_znotraj_tol'], A=3, B=3)

        # Calculate the distance covered based on the speed in the 9th column and store in the 10th column
        trimmed_data['Distance_Covered'] = calculate_distance_from_speed(trimmed_data)

        # Ensure the first value of Distance_Covered is a copy of the second value
        if not trimmed_data['Distance_Covered'].isnull().all():  # Ensure there are no NaN values
            trimmed_data['Distance_Covered'].iloc[0] = trimmed_data['Distance_Covered'].iloc[1]  # Copy the second value to the first

        # Ensure the last value of Distance_Covered is a copy of the second last value
        if not trimmed_data['Distance_Covered'].isnull().all():  # Ensure there are no NaN values
            trimmed_data['Distance_Covered'].iloc[-1] = trimmed_data['Distance_Covered'].iloc[-2]  # Copy the second last value to the last

        # Append the trimmed data to the list for plotting
        all_trimmed_data.append(trimmed_data)

        # Save the trimmed data to a new CSV file
        trimmed_file_path = os.path.join("trimmed_data", f"trimmed_{uploaded_file.name}")
        trimmed_data.to_csv(trimmed_file_path, sep=';', decimal=',', index=False)

    # Create a download button for the trimmed files
    download_files = [f"trimmed_{uploaded_file.name}" for uploaded_file in uploaded_files]
    zip_file_path = "trimmed_data.zip"
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        for trimmed_file in download_files:
            zip_file.write(os.path.join("trimmed_data", trimmed_file), trimmed_file)

    # Provide the download link
    with download_button_placeholder:
        st.download_button("Download Trimmed Data", zip_file_path, file_name="trimmed_data.zip")

    # Plot all speed curves together for distances from 0 to 30 meters
    plt.figure(figsize=(12, 6))
    for uploaded_file, trimmed_data in zip(uploaded_files, all_trimmed_data):
        # Adjust distance by subtracting the calibration distance
        adjusted_distance = trimmed_data['Distance'] - s_calibration
        plt.plot(adjusted_distance, trimmed_data['v_znotraj_tol_filtered_9_9'], label=f'Speed for {uploaded_file.name}')

    plt.title('Speed Curves for All Files')
    plt.xlabel('Distance (m)')
    plt.ylabel('Speed (m/s)')
    plt.xlim(0, d_sprint)  # Set x-axis limit from 0 to sprint length
    plt.ylim(0, max(trimmed_data['v_znotraj_tol_filtered_9_9'].max() for trimmed_data in all_trimmed_data) * 1.1)  # Set y-axis limit
    plt.axhline(0, color='black', linewidth=0.5, linestyle='--')
    plt.axvline(0, color='black', linewidth=0.5, linestyle='--')
    plt.grid()
    plt.legend()  # Include the legend with unique labels
    plt.tight_layout()

    # Display the combined plot in Streamlit below the download button
    st.pyplot(plt)
    plt.clf()  # Clear the plot for the next files
