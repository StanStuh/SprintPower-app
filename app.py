import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

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
            hovermode="closest"
        )

        # Streamlit Plotly plot
        selected_points = st.plotly_chart(fig, use_container_width=True)

        # Allow user to select a range of data for cleaning
        st.subheader("Clean Data Selection")
        st.write("Drag over the plot above to select a portion of the data. This will be shown below.")
        
        # Retrieve the selected data (we assume a user selected a region of interest)
        if selected_points:
            selection = selected_points["points"]
            if len(selection) > 0:
                # Extract selected data points
                selected_indices = [point["pointIndex"] for point in selection]
                selected_df = df.iloc[selected_indices]
                
                # Display the selected data
                st.write("Selected Data:")
                st.dataframe(selected_df)
                
                # You can now apply further data cleaning, for example:
                st.write("Cleaned Data (after dropping NaN values):")
                cleaned_df = selected_df.dropna()
                st.dataframe(cleaned_df)

    except Exception as e:
        st.error(f"Pri obdelavi datoteke je prišlo do napake: {e}")
