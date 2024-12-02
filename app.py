import streamlit as st
from PyPDF2 import PdfReader
import pandas as pd
from datetime import datetime
import io

# Streamlit UI
st.title("PDF Data Extraction to Excel")
st.write("Upload a PDF file to extract specific data and save it in an Excel format.")

# File uploader
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file:
    # Read the uploaded PDF
    reader = PdfReader(uploaded_file)
    
    # Prepare the extracted data
    data = {"ID naročila": [], "Ime panoge": [], "Začetek meritve": [], "Cena vseh meritev skupaj": []}
    
    # Define keywords for extraction
    keywords = {
        "ID naročila:": "ID naročila",
        "Ime panoge:": "Ime panoge",
        "Začetek meritve:": "Začetek meritve",
        "Cena vseh meritev skupaj:": "Cena vseh meritev skupaj"
    }
    
    # Extract data from each page
    for page in reader.pages:
        text = page.extract_text()
        page_data = {key: None for key in keywords.values()}  # Initialize with None
        
        for key, column in keywords.items():
            if key in text:
                start_idx = text.find(key) + len(key)
                extracted = text[start_idx:].split("\n")[0].strip()
                page_data[column] = extracted
        
        for column, value in page_data.items():
            data[column].append(value)
    
    # Convert to DataFrame
    df_sheet1 = pd.DataFrame(data)
    
    # Process "Cena vseh meritev skupaj" for numerical calculations
    df_sheet1["Cena vseh meritev skupaj"] = (
        df_sheet1["Cena vseh meritev skupaj"]
        .str.replace("€", "")
        .str.replace(",", "")
        .astype(float, errors='ignore')
    )
    
    # Summary for Sheet 2
    df_sheet2 = df_sheet1.groupby("Ime panoge", as_index=False)["Cena vseh meritev skupaj"].sum()
    
    # File name with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    excel_file_name = f"{timestamp}_Extracted_Data.xlsx"
    
    # Save to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_sheet1.to_excel(writer, index=False, sheet_name="Sheet1")
        df_sheet2.to_excel(writer, index=False, sheet_name="Sheet2")
    output.seek(0)
    
    # Provide download link
    st.download_button(
        label="Download Excel file",
        data=output,
        file_name=excel_file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
