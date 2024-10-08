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
        
        # Calculate raw v1 and v2 on the full dataset
        df['vsur'] = df['s_sur'].diff() / df['t'].diff()
        df['v1'] = moving_average_smoothing(df['vsur'].fillna(0), A=9, B=9)
        df['v2'] = moving_average_smoothing(df['vsur'].fillna(0), A=3, B=3)
        
        # Filter data for s_reference between 0 and the measured distance (30 meters)
        df_filtered = df[(df['s_reference'] >= 0) & (df['s_reference'] <= measured_distance)]
        
        # Calculate distance s2 from smoothed speed v2
        df_filtered['s2'] = calculate_distance_from_speed(df_filtered['v2'], df_filtered['t'].diff().fillna(0))

        # Interactive Plot using Plotly
        fig = go.Figure()

        # Add raw speed plot
        fig.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['vsur'], mode='lines', name='Raw Speed (vsur)'))
        
        # Add smoothed speed plots
        fig.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['v1'], mode='lines', name='Smoothed Speed (v1)', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['v2'], mode='lines', name='Smoothed Speed (v2)', line=dict(color='green')))
        
        # Add plot for calculated distance
        fig.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['s2'], mode='lines', name='Calculated Distance (s2)', line=dict(color='red', dash='dash')))
        
        # Add plot for s_reference
        fig.add_trace(go.Scatter(x=df_filtered['t'], y=df_filtered['s_reference'], mode='lines', name='Reference Distance (s_reference)', line=dict(color='blue', dash='dot')))

        fig.update_layout(
            title="Speed and Distance (s_reference = 0 to 30 meters)",
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
        fig_cleaned_distance.add_trace(go.Scatter(x=cleaned_df['t_adjusted'], y=cleaned_df['s2'], mode='lines', name='Calculated Distance (s2)', line=dict(color='red', dash='dash')))
        fig_cleaned_distance.update_layout(title="Calculated Distance (s2)", xaxis_title="Time (s)", yaxis_title="Distance (m)")
        
        st.plotly_chart(fig_cleaned_distance, use_container_width=True)

    except Exception as e:
        st.error(f"Pri obdelavi datoteke je prišlo do napake: {e}")
        # Create a new DataFrame for times and speeds at every 5 meters
interval_distance = 5
max_distance = df_filtered['s_reference'].max()

# Create lists to store times and speeds
times = []
speeds = []

# Iterate over the range from 0 to max_distance in steps of interval_distance
for d in range(0, int(max_distance) + 1, interval_distance):
    # Filter the DataFrame to get the first occurrence of each distance
    distance_data = df_filtered[df_filtered['s_reference'] == d]
    
    if not distance_data.empty:
        # Get the first time and speed for this distance
        times.append(distance_data['t'].iloc[0])
        speeds.append(distance_data['v2'].iloc[0])  # Use v2 for speed
    else:
        # If no data is found for this distance, append NaN
        times.append(np.nan)
        speeds.append(np.nan)

# Create a new DataFrame for the results
results_df = pd.DataFrame({
    'Distance (m)': np.arange(0, max_distance + 1, interval_distance),
    'Time (s)': times,
    'Speed (m/s)': speeds
})

# Display the new DataFrame in the Streamlit app
st.write("Times and Speeds at Every 5 Meters:")
st.dataframe(results_df)

