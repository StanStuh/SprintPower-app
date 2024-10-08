import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events  # Importing plotly_events to capture interaction

# Function to calculate raw speed
def calculate_raw_speed(df):
    df['t'] = pd.to_numeric(df['t'], errors='coerce')
    df['s_sur'] = pd.to_numeric(df['s_sur'], errors='coerce')
    df = df.dropna(subset=['t', 's_sur'])
    df['vsur'] = df['s_sur'].diff() / df['t'].diff()
    return df

# Function for moving average smoothing
def moving_average_smoothing(data, A, B):
    for _ in range(A):
        data = np.convolve(data, np.ones((2 * B + 1,)) / (2 * B + 1), mode='same')
    return data

# Function to calculate distance from smoothed speed
def calculate_distance_from_speed(v2, delta_t):
    return v2 * delta_t

# Streamlit UI
st.title("SprintPower Data Processing with Interactive Selection")

# File upload
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Read the CSV file with appropriate separator and decimal settings
        df = pd.read_csv(uploaded_file, sep=';', decimal=',', header=None, names=['t', 's_sur'])
        
        # Ensure columns are numeric and clean data
        df = calculate_raw_speed(df)
        
        # Apply first-stage smoothing (A=9, B=9)
        df['v1'] = moving_average_smoothing(df['vsur'].fillna(0), A=9, B=9)
        
        # Apply second-stage smoothing (A=3, B=3)
        df['v2'] = moving_average_smoothing(df['vsur'].fillna(0), A=3, B=3)
        
        # Calculate distance s2 from smoothed speed v2
        df['s2'] = calculate_distance_from_speed(df['v2'], df['t'].diff().fillna(0))
        
        # Interactive Plot using Plotly
        fig = go.Figure()

        # Add raw speed plot
        fig.add_trace(go.Scatter(x=df['t'], y=df['vsur'], mode='lines', name='Raw Speed (vsur)'))
        
        # Add smoothed speed plot
        fig.add_trace(go.Scatter(x=df['t'], y=df['v1'], mode='lines', name='Smoothed Speed (v1)', line=dict(color='orange')))
        
        # Add second smoothed speed plot and distance
        fig.add_trace(go.Scatter(x=df['t'], y=df['v2'], mode='lines', name='Smoothed Speed (v2)', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=df['t'], y=df['s2'], mode='lines', name='Calculated Distance (s2)', line=dict(color='red', dash='dash')))

        fig.update_layout(
            title="Select a Region of Interest by Dragging",
            xaxis_title="Time (s)",
            yaxis_title="Speed/Distance (m/s or m)",
            hovermode="closest",
            dragmode="select"  # Enable selection mode
        )

        # Streamlit Plotly plot with event capturing
        selected_points = plotly_events(fig, select_event=True)

        # If points are selected, filter the data based on the selected region
        if selected_points:
            # Extract selected data points
            selected_indices = [point['pointIndex'] for point in selected_points]
            
            # Filter the DataFrame based on selected points
            filtered_df = df.iloc[selected_indices]
            
            st.write("Filtered Data (based on selection):")
            st.dataframe(filtered_df)

            # Clean the filtered data (e.g., drop NaNs)
            cleaned_df = filtered_df.dropna()
            st.write("Cleaned Data (after dropping NaN values):")
            st.dataframe(cleaned_df)

            # Create new charts for v1 and v2 from the cleaned data
            st.subheader("Cleaned Data: Smoothed Speed (v1, v2) and Calculated Distance (s2)")
            
            # New Plot for Smoothed Speeds v1 and v2
            fig_cleaned_speed = go.Figure()
            fig_cleaned_speed.add_trace(go.Scatter(x=cleaned_df['t'], y=cleaned_df['v1'], mode='lines', name='Smoothed Speed (v1)', line=dict(color='orange')))
            fig_cleaned_speed.add_trace(go.Scatter(x=cleaned_df['t'], y=cleaned_df['v2'], mode='lines', name='Smoothed Speed (v2)', line=dict(color='green')))
            fig_cleaned_speed.update_layout(title="Smoothed Speeds (v1 and v2)", xaxis_title="Time (s)", yaxis_title="Speed (m/s)")
            
            st.plotly_chart(fig_cleaned_speed, use_container_width=True)

            # New Plot for Calculated Distance (s2)
            fig_cleaned_distance = go.Figure()
            fig_cleaned_distance.add_trace(go.Scatter(x=cleaned_df['t'], y=cleaned_df['s2'], mode='lines', name='Calculated Distance (s2)', line=dict(color='red', dash='dash')))
            fig_cleaned_distance.update_layout(title="Calculated Distance (s2)", xaxis_title="Time (s)", yaxis_title="Distance (m)")
            
            st.plotly_chart(fig_cleaned_distance, use_container_width=True)

        else:
            st.write("No data points selected. Please drag over the plot to select a region.")

    except Exception as e:
        st.error(f"Pri obdelavi datoteke je prišlo do napake: {e}")
