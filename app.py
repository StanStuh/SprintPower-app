import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Function to calculate raw speed
def calculate_raw_speed(df):
    df['t'] = pd.to_numeric(df['t'], errors='coerce')
    df['s_sur'] = pd.to_numeric(df['s_sur'], errors='coerce')
    df = df.dropna(subset=['t', 's_sur'])
    df['vsur'] = df['s_sur'].diff() / df['t'].diff()
    return df

# Function for moving average smoothing with edge handling
def moving_average_smoothing(data, A, B):
    # Apply moving average smoothing
    for _ in range(A):
        data = np.convolve(data, np.ones((2 * B + 1,)) / (2 * B + 1), mode='same')
    return data

# Function to calculate distance from smoothed speed
def calculate_distance_from_speed(v2, delta_t):
    return v2 * delta_t

# Streamlit UI
st.title("SprintPower Data Processing with Range Selection")

# Input for calibration value
calibration_value = st.number_input("Enter Calibration Value (in meters)", value=3.105, step=0.001)

# Input for measured distance value
measured_distance = st.number_input("Enter Measured Distance (in meters)", value=30.0, step=0.1)

# File upload
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read the CSV file with appropriate separator and decimal settings
        df = pd.read_csv(uploaded_file, sep=';', decimal=',', header=None, names=['t', 's_sur'])

        # Ensure columns are numeric and clean data
        df = calculate_raw_speed(df)

        # Apply calibration value to calculate s_reference
        df['s_reference'] = df['s_sur'] - calibration_value

        # Display initial plot for data selection
        st.write("Select the range of data you want to clean:")
        
        # Plot initial graph with raw data (vsur)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['t'], y=df['s_reference'], mode='lines', name='Reference Distance (s_reference)'))
        fig.update_layout(title="Raw Reference Distance Over Time", xaxis_title="Time (s)", yaxis_title="Reference Distance (m)")
        st.plotly_chart(fig, use_container_width=True)

        # Add slider to select range for time (you could also use s_reference as the range base)
        time_min = st.slider("Select minimum time (s)", min_value=float(df['t'].min()), max_value=float(df['t'].max()), value=float(df['t'].min()))
        time_max = st.slider("Select maximum time (s)", min_value=float(df['t'].min()), max_value=float(df['t'].max()), value=float(df['t'].max()))

        # Filter the DataFrame based on the selected range
        df_filtered = df[(df['t'] >= time_min) & (df['t'] <= time_max)]

        # Now process the filtered data
        df_filtered['vsur'] = df_filtered['s_sur'].diff() / df_filtered['t'].diff()
        df_filtered['v1'] = moving_average_smoothing(df_filtered['vsur'].fillna(0), A=9, B=9)
        df_filtered['v2'] = moving_average_smoothing(df_filtered['vsur'].fillna(0), A=3, B=3)
        df_filtered['s2'] = calculate_distance_from_speed(df_filtered['v2'], df_filtered['t'].diff().fillna(0))

        # Plot the filtered data
        fig_filtered = go.Figure()
        fig_filtered.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['vsur'], mode='lines', name='Raw Speed (vsur)'))
        fig_filtered.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['v1'], mode='lines', name='Smoothed Speed (v1)', line=dict(color='orange')))
        fig_filtered.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['v2'], mode='lines', name='Smoothed Speed (v2)', line=dict(color='green')))
        fig_filtered.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['s2'], mode='lines', name='Calculated Distance (s2)', line=dict(color='red')))
        fig_filtered.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['s_reference'], mode='lines', name='Reference Distance (s_reference)', line=dict(color='blue', dash='dot')))
        fig_filtered.update_layout(title="Filtered Data: Speed and Distance", xaxis_title="Time (s)", yaxis_title="Speed/Distance (m/s or m)")

        # Plot the graph
        st.plotly_chart(fig_filtered)

        # Display filtered DataFrame
        st.write("Filtered Data (based on selected time range):")
        st.dataframe(df_filtered)

        # Further processing for cleaned data
        cleaned_df = df_filtered.dropna()
        cleaned_df['t_adjusted'] = cleaned_df['t'] - cleaned_df['t'].min()

        # Create cleaned plots
        st.subheader("Cleaned Data: Smoothed Speed (v1, v2) and Calculated Distance (s2)")
        fig_cleaned_speed = go.Figure()
        fig_cleaned_speed.add_trace(go.Scatter(x=cleaned_df['t_adjusted'], y=cleaned_df['v1'], mode='lines', name='Smoothed Speed (v1)', line=dict(color='orange')))
        fig_cleaned_speed.add_trace(go.Scatter(x=cleaned_df['t_adjusted'], y=cleaned_df['v2'], mode='lines', name='Smoothed Speed (v2)', line=dict(color='green')))
        fig_cleaned_speed.update_layout(title="Cleaned Speeds (v1 and v2)", xaxis_title="Time (s)", yaxis_title="Speed (m/s)")
        st.plotly_chart(fig_cleaned_speed, use_container_width=True)

        fig_cleaned_distance = go.Figure()
        fig_cleaned_distance.add_trace(go.Scatter(x=cleaned_df['t_adjusted'], y=cleaned_df['s2'], mode='lines', name='Calculated Distance (s2)', line=dict(color='red')))
        fig_cleaned_distance.update_layout(title="Calculated Distance (s2)", xaxis_title="Time (s)", yaxis_title="Distance (m)")
        st.plotly_chart(fig_cleaned_distance, use_container_width=True)

    except Exception as e:
        st.error(f"Pri obdelavi datoteke je prišlo do napake: {e}")
