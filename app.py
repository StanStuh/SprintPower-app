import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Function to calculate raw speed
def calculate_raw_speed(df):
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
st.title("SprintPower Data Processing")

# File upload
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file, sep='\t', decimal=',', header=None, names=['t', 's_sur'])
    
    # Calculate raw speed
    df = calculate_raw_speed(df)
    
    # Apply first-stage smoothing (A=9, B=9)
    df['v1'] = moving_average_smoothing(df['vsur'].fillna(0), A=9, B=9)
    
    # Apply second-stage smoothing (A=3, B=3)
    df['v2'] = moving_average_smoothing(df['vsur'].fillna(0), A=3, B=3)
    
    # Calculate distance s2 from smoothed speed v2
    df['s2'] = calculate_distance_from_speed(df['v2'], df['t'].diff().fillna(0))
    
    # Display data table
    st.write(df)
    
    # Plotting the results
    fig, ax = plt.subplots(3, 1, figsize=(10, 8))
    
    # Plot raw speed
    ax[0].plot(df['t'], df['vsur'], label='Raw Speed (vsur)')
    ax[0].set_title('Raw Speed')
    ax[0].set_xlabel('Time (s)')
    ax[0].set_ylabel('Speed (m/s)')
    
    # Plot first-stage smoothed speed
    ax[1].plot(df['t'], df['v1'], label='Smoothed Speed (v1)', color='orange')
    ax[1].set_title('Smoothed Speed (A=9, B=9)')
    ax[1].set_xlabel('Time (s)')
    ax[1].set_ylabel('Speed (m/s)')
    
    # Plot second-stage smoothed speed and calculated distance
    ax[2].plot(df['t'], df['v2'], label='Smoothed Speed (v2)', color='green')
    ax[2].plot(df['t'], df['s2'], label='Calculated Distance (s2)', color='red', linestyle='--')
    ax[2].set_title('Smoothed Speed (A=3, B=3) and Calculated Distance')
    ax[2].set_xlabel('Time (s)')
    ax[2].set_ylabel('Speed/Distance (m/s or m)')
    
    # Show legend
    for a in ax:
        a.legend()
    
    # Display the plot
    st.pyplot(fig)
