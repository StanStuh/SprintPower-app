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
    st.write("Raw Data:")
    st.write(data)

    # Input for calibration and sprint length
    s_calibration = st.number_input("Enter calibration distance (m)", value=3.105)
    d_sprint = st.number_input("Enter sprint length (m)", value=30.0)

    # Trim data based on the conditions
    # 1 second before calibration
    time_before_calibration = data[data['Distance'] >= s_calibration]['Time'].iloc[0] - 1.0
    # 32 meters of the sprint
    max_distance = s_calibration + d_sprint + 2

    # Keep data between these time points
    trimmed_data = data[(data['Time'] >= time_before_calibration) & (data['Distance'] <= max_distance)]

    st.write("Trimmed Data:")
    st.write(trimmed_data)

    # Optional: Allow the user to download the trimmed data
    st.download_button("Download Trimmed Data", trimmed_data.to_csv(index=False), "trimmed_data.csv")
