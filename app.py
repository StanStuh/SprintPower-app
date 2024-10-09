import pandas as pd
import streamlit as st

# Function to load data with semicolon delimiter and comma as decimal separator
def load_data(file):
    return pd.read_csv(file, delimiter=';', decimal=',', header=None)

# Upload CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

if uploaded_file is not None:
    # Load the data
    data = load_data(uploaded_file)

    # Display raw data without header and without the first data row
    st.write("Raw Data:")
    st.write(data.iloc[1:].to_string(index=False, header=False))  # Skip first row of data

    # Input for calibration and sprint length
    s_calibration = st.number_input("Enter calibration distance (m)", value=3.105)
    d_sprint = st.number_input("Enter sprint length (m)", value=30.0)

    # Find the time point that is 1 second before the calibration distance
    try:
        time_before_calibration = data[data[1] >= s_calibration][0].iloc[1] - 1.0  # Adjust to get the second row's value
    except IndexError:
        st.error("Error: Could not find a point in the data where the distance is greater than or equal to the calibration distance.")
        time_before_calibration = None

    if time_before_calibration is not None:
        # 32 meters of the sprint (s_calibration + d_sprint + 2)
        max_distance = s_calibration + d_sprint + 2

        # Keep data between these time points
        trimmed_data = data[(data[0] >= time_before_calibration) & (data[1] <= max_distance)]

        st.write("Trimmed Data:")
        # Display trimmed data without header and without the first data row
        st.write(trimmed_data.iloc[1:].to_string(index=False, header=False))  # Skip first row of data

        # Optional: Allow the user to download the trimmed data in the same format (semicolon and comma)
        csv_data = trimmed_data.to_csv(index=False, sep=';', decimal=',')
        st.download_button("Download Trimmed Data", csv_data, "trimmed_data.csv")
