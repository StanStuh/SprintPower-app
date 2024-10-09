import pandas as pd
import streamlit as st
import io

# Function to load data with semicolon delimiter and comma as decimal separator
def load_data(file):
    return pd.read_csv(file, delimiter=';', decimal=',', header=None, names=['Time', 'Distance'])

# Upload multiple CSV files
uploaded_files = st.file_uploader("Upload your CSV files", type=['csv'], accept_multiple_files=True)

# Placeholder for the download button
download_button_placeholder = st.empty()

# List to hold all trimmed data
all_trimmed_data = []

if uploaded_files:
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
            all_trimmed_data.append(trimmed_data)

            st.write(f"Trimmed Data from {uploaded_file.name}:")
            st.write(trimmed_data)

    # Combine all trimmed data into a single DataFrame
    if all_trimmed_data:
        combined_trimmed_data = pd.concat(all_trimmed_data, ignore_index=True)

        # Allow the user to download the combined trimmed data
        csv_data = combined_trimmed_data.to_csv(index=False, sep=';', decimal=',', header=False)
        
        # Show download button at the top
        download_button_placeholder.download_button("Download All Trimmed Data", csv_data, "trimmed_data_combined.csv")
