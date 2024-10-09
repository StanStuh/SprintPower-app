import pandas as pd
import streamlit as st

# Function to load data
def load_data(file):
    # Load CSV with specific delimiters and decimal separators
    return pd.read_csv(file, delimiter='\t', decimal=',')

# Upload CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

if uploaded_file is not None:
    # Load the data
    data = load_data(uploaded_file)
    
    # Display the column names to ensure they are correct
    st.write("Column names:", data.columns)

    # Assuming the first column is 'Time' and the second column is 'Distance'
    time_column = data.columns[0]  # Use the first column for time
    distance_column = data.columns[1]  # Use the second column for distance
    
    # Display raw data
    st.write("Raw Data:")
    st.write(data)

    # Input for calibration and sprint length
    s_calibration = st.number_input("Enter calibration distance (m)", value=3.105)
    d_sprint = st.number_input("Enter sprint length (m)", value=30.0)

    # Find the time point that is 1 second before the calibration distance
    try:
        time_before_calibration = data[data[distance_column] >= s_calibration][time_column].iloc[0] - 1.0
    except IndexError:
        st.error("Error: Could not find a point in the data where the distance is greater than or equal to the calibration distance.")
        time_before_calibration = None

    if time_before_calibration:
        # 32 meters of the sprint
        max_distance = s_calibration + d_sprint + 2

        # Keep data between these time points
        trimmed_data = data[(data[time_column] >= time_before_calibration) & (data[distance_column] <= max_distance)]

        st.write("Trimmed Data:")
        st.write(trimmed_data)

        # Optional: Allow the user to download the trimmed data
        st.download_button("Download Trimmed Data", trimmed_data.to_csv(index=False), "trimmed_data.csv")
