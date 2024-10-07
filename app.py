import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Funkcija za izračun surove hitrosti
def calculate_raw_speed(df):
    df['vsur'] = df['s_sur'].diff() / df['t'].diff()
    return df

# Funkcija za glajenje s drsečim povprečjem
def moving_average_smoothing(data, A, B):
    for _ in range(A):
        data = np.convolve(data, np.ones((2 * B + 1,)) / (2 * B + 1), mode='same')
    return data

# Funkcija za izračun distance iz glajene hitrosti
def calculate_distance_from_speed(v2, delta_t):
    return v2 * delta_t

# Streamlit UI
st.title("SprintPower Data Processing")

# Nalaganje datoteke
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Branje CSV datoteke z ločilom eno ali več presledkov/tabulatorjev in decimalnim vejico
        df = pd.read_csv(uploaded_file, sep='\s+', decimal=',', header=None, names=['t', 's_sur'])
        
        # Pretvorba stolpcev v float
        df['t'] = df['t'].astype(float)
        df['s_sur'] = df['s_sur'].astype(float)
        
        # Sortiranje po času, če ni že urejeno
        df = df.sort_values('t').reset_index(drop=True)
        
        # Izračun surove hitrosti
        df = calculate_raw_speed(df)
        
        # Preverjanje in odstranjevanje vrstic z NaN vrednostmi
        df = df.dropna(subset=['vsur'])
        
        # Prva stopnja glajenja (A=9, B=9)
        df['v1'] = moving_average_smoothing(df['vsur'], A=9, B=9)
        
        # Druga stopnja glajenja (A=3, B=3)
        df['v2'] = moving_average_smoothing(df['v1'], A=3, B=3)
        
        # Izračun distance s2 iz glajene hitrosti v2
        delta_t = df['t'].diff().fillna(0)
        df['s2'] = calculate_distance_from_speed(df['v2'], delta_t)
        
        # Prikaz podatkovne tabele
        st.write(df)
        
        # Risanje grafov
        fig, ax = plt.subplots(3, 1, figsize=(10, 12))
        
        # Graf surove hitrosti
        ax[0].plot(df['t'], df['vsur'], label='Raw Speed (vsur)', color='blue')
        ax[0].set_title('Raw Speed')
        ax[0].set_xlabel('Time (s)')
        ax[0].set_ylabel('Speed (m/s)')
        ax[0].legend()
        
        # Graf prve stopnje glajenja
        ax[1].plot(df['t'], df['v1'], label='Smoothed Speed (v1)', color='orange')
        ax[1].set_title('Smoothed Speed (A=9, B=9)')
        ax[1].set_xlabel('Time (s)')
        ax[1].set_ylabel('Speed (m/s)')
        ax[1].legend()
        
        # Graf druge stopnje glajenja in izračunane distance
        ax[2].plot(df['t'], df['v2'], label='Smoothed Speed (v2)', color='green')
        ax[2].plot(df['t'], df['s2'], label='Calculated Distance (s2)', color='red', linestyle='--')
        ax[2].set_title('Smoothed Speed (A=3, B=3) and Calculated Distance')
        ax[2].set_xlabel('Time (s)')
        ax[2].set_ylabel('Speed/Distance (m/s or m)')
        ax[2].legend()
        
        plt.tight_layout()
        st.pyplot(fig)
        
    except Exception as e:
        st.error(f"Pri obdelavi datoteke je prišlo do napake: {e}")
