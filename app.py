import pandas as pd
import streamlit as st

# Function to load data with semicolon delimiter and comma as decimal separator
def load_data(file):
    return pd.read_csv(file, delimiter=';', decimal=',', header=None, names=['Time', 'Distance'])

# Upload multiple CSV files
uploaded_files = st.file_uploader("Upload your CSV files", type=['csv'], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"Processing file: {uploaded_file.name}")
        
        # Load the data
        data = load_data(uploaded_file)
        
        # Display raw data
        st.write("Raw Data:")
        st.write(data)

        # Input for calibration and sprint length
        s_calibration = st.number_input("Enter calibration distance (m)", value=3.105)
        d_sprint = st.number_input("Enter sprint length (m)", value=30.0)

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

            # Optional: Allow the user to download the trimmed data in the same format (semicolon and comma)
            csv_data = trimmed_data.to_csv(index=False, sep=';', decimal=',')
            st.download_button(f"Download Trimmed Data for {uploaded_file.name}", csv_data, f"trimmed_{uploaded_file.name}")
