import streamlit as st
import pandas as pd

# Initialize session state for handling data removal
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

# File upload
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

# Button to remove the last 0.5 seconds of data
if st.button("Remove Last 0.5 Seconds"):
    # Check if dataframe is available in session state
    if not st.session_state.df.empty:
        max_time = st.session_state.df['t'].max()
        cutoff_time = max_time - 0.5  # Remove last 0.5 seconds
        st.session_state.df = st.session_state.df[st.session_state.df['t'] <= cutoff_time]
        st.success("Last 0.5 seconds of data removed.")
    else:
        st.warning("No data available to remove.")

if uploaded_file is not None:
    try:
        # Read the CSV file with appropriate separator and decimal settings
        df = pd.read_csv(uploaded_file, sep=';', decimal=',', header=None, names=['t', 's_sur'])
        
        # Store raw data in session state
        st.session_state.df = df
        
        # Display the original DataFrame
        st.write("Original Data:")
        st.dataframe(df)
    
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
