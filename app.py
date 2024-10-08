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

# Initialize session state for handling data removal
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

# Button to remove the last 0.5 seconds of data
if st.button("Remove Last 0.5 Seconds"):
    # Check if dataframe is available in session state
    if not st.session_state.df.empty:
        max_time = st.session_state.df['t'].max()
        cutoff_time = max_time - 0.5  # Remove last 0.5 seconds
        st.session_state.df = st.session_state.df[st.session_state.df['t'] <= cutoff_time]

if uploaded_file is not None:
    try:
        # Read the CSV file with appropriate separator and decimal settings
        df = pd.read_csv(uploaded_file, sep=';', decimal=',', header=None, names=['t', 's_sur'])
        
        # Store raw data in session state
        st.session_state.df = df
        
        # Ensure columns are numeric and clean data
        df = calculate_raw_speed(st.session_state.df)
        
        # Apply calibration value to calculate s_reference
        df['s_reference'] = df['s_sur'] - calibration_value
        
        # Calculate raw v1 and v2 on the full dataset
        df['vsur'] = df['s_sur'].diff() / df['t'].diff()
        df['v1'] = moving_average_smoothing(df['vsur'].fillna(0), A=9, B=9)
        df['v2'] = moving_average_smoothing(df['vsur'].fillna(0), A=3, B=3)
        
        # Calculate distance s2 from smoothed speed v2
        df['s2'] = calculate_distance_from_speed(df['v2'], df['t'].diff().fillna(0))

        # Filter data for s_reference between 0 and the measured distance (30 meters)
        df_filtered = df[(df['s_reference'] >= 0) & (df['s_reference'] <= measured_distance)]

        # Interactive Plot using Plotly for all data
        fig = go.Figure()

        # Add raw speed plot for all data
        fig.add_trace(go.Scatter(x=df['t'], y=df['vsur'], mode='lines', name='Raw Speed (vsur)'))
        
        # Add smoothed speed plots for all data
        fig.add_trace(go.Scatter(x=df['t'], y=df['v1'], mode='lines', name='Smoothed Speed (v1)', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=df['t'], y=df['v2'], mode='lines', name='Smoothed Speed (v2)', line=dict(color='green')))
        
        # Add plot for calculated distance for all data
        fig.add_trace(go.Scatter(x=df['t'], y=df['s2'], mode='lines', name='Calculated Distance (s2)', line=dict(color='red')))
        
        # Add plot for s_reference for all data
        fig.add_trace(go.Scatter(x=df['t'], y=df['s_reference'], mode='lines', name='Reference Distance (s_reference)', line=dict(color='blue', dash='dot')))

        fig.update_layout(
            title="Speed and Distance (All Data)",
            xaxis_title="Time (s)",
            yaxis_title="Speed/Distance (m/s or m)",
            hovermode="closest"
        )

        # Plot the graph
        st.plotly_chart(fig)

        # Display filtered DataFrame for the range s_reference=0 to 30 meters
        st.write("Filtered Data (s_reference between 0 and 30 meters):")
        st.dataframe(df_filtered)

        # Clean the filtered data (e.g., drop NaNs)
        cleaned_df = df_filtered.dropna()
        st.write("Cleaned Data (after dropping NaN values):")
        st.dataframe(cleaned_df)

        # Adjust time so it starts from 0 for cleaned data
        cleaned_df['t_adjusted'] = cleaned_df['t'] - cleaned_df['t'].min()

        # Create new charts for v1 and v2 from the cleaned data
        st.subheader("Cleaned Data: Smoothed Speed (v1, v2) and Calculated Distance (s2)")
        
        # New Plot for Smoothed Speeds v1 and v2 with adjusted time
        fig_cleaned_speed = go.Figure()
        fig_cleaned_speed.add_trace(go.Scatter(x=cleaned_df['t_adjusted'], y=cleaned_df['v1'], mode='lines', name='Smoothed Speed (v1)', line=dict(color='orange')))
        fig_cleaned_speed.add_trace(go.Scatter(x=cleaned_df['t_adjusted'], y=cleaned_df['v2'], mode='lines', name='Smoothed Speed (v2)', line=dict(color='green')))
        fig_cleaned_speed.update_layout(title="Smoothed Speeds (v1 and v2)", xaxis_title="Time (s)", yaxis_title="Speed (m/s)")
        
        st.plotly_chart(fig_cleaned_speed, use_container_width=True)

        # New Plot for Calculated Distance (s2) with adjusted time
        fig_cleaned_distance = go.Figure()
        fig_cleaned_distance.add_trace(go.Scatter(
            x=cleaned_df['t_adjusted'],
            y=cleaned_df['s2'],
            mode='lines',  # Continuous line for s2
            name='Calculated Distance (s2)',
            line=dict(color='red')  # Changed to straight line
        ))
        fig_cleaned_distance.update_layout(
            title="Calculated Distance (s2)",
            xaxis_title="Time (s)",
            yaxis_title="Distance (m)"
        )
        
        st.plotly_chart(fig_cleaned_distance, use_container_width=True)

        # Create a new DataFrame for times and speeds at every 5 meters
        interval_distance = 5
        max_distance = measured_distance  # Use the measured distance as max

        # Create a new DataFrame for results
        results_list = []

        # Iterate over the range from 0 to max_distance in steps of interval_distance
        for d in range(0, int(max_distance) + 1, interval_distance):
            # Filter the DataFrame to get the first occurrence of each distance
            distance_data = df_filtered[df_filtered['s_reference'] >= d]

            if not distance_data.empty:
                # Get the first occurrence of distance data
                time_at_distance = distance_data['t'].iloc[0] - cleaned_df['t'].iloc[0]  # Adjust time to start from zero
                speed_at_distance = distance_data['v2'].iloc[0]  # Use v2 for speed

                # Append results for the distance
                results_list.append({
                    'Distance (m)': d,
                    'Time (s)': time_at_distance,
                    'Speed (m/s)': speed_at_distance
                })

        # Ensure the 30 m entry is correctly reflected
        if results_list and results_list[-1]['Distance (m)'] < max_distance:
            time_at_distance = cleaned_df['t'].iloc[-1] - cleaned_df['t'].iloc[0]  # Get last time for max distance
            speed_at_distance = cleaned_df['v2'].iloc[-1]  # Use last speed for max distance
            results_list.append({
                'Distance (m)': max_distance,
                'Time (s)': time_at_distance,
                'Speed (m/s)': speed_at_distance
            })

        # Create a new DataFrame from the results
        results_df = pd.DataFrame(results_list)

        # Remove duplicate rows based on distance, keeping the first
