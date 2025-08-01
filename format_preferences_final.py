import streamlit as st
import pandas as pd

st.title("Proposal Preferences Formatter")

# Upload preference files (multiple allowed)
uploaded_files = st.file_uploader(
    "Upload preference files (multiple allowed)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

# Upload the formatting template file (optional)
template_file = st.file_uploader("Upload the formatting template file (optional)", type=["xlsx"])

# "Go" button to trigger processing
if st.button("Go"):
    # Check if at least one input is provided
    if not uploaded_files and not template_file:
        st.error("Please upload at least one preference file or a formatting template.")
    else:
        # Process preference files if any
        if uploaded_files:
            st.write(f"Processing {len(uploaded_files)} preference file(s)...")
            for uploaded_file in uploaded_files:
                df = pd.read_excel(uploaded_file)
                # Your processing logic here, for example:
                st.write(f"Preview of {uploaded_file.name}:")
                st.dataframe(df.head())

        # Process template file if provided
        if template_file:
            st.write("Processing the formatting template file...")
            template_df = pd.read_excel(template_file)
            # Your processing logic here
            st.write("Template preview:")
            st.dataframe(template_df.head())
import pandas as pd

try:
    xls = pd.ExcelFile(uploaded_file)
    if len(xls.sheet_names) == 0:
        st.error(f"The file {uploaded_file.name} contains no sheets.")
    else:
        df = pd.read_excel(uploaded_file)  # defaults to first sheet
        st.write(df.head())
except Exception as e:
    st.error(f"Error reading {uploaded_file.name}: {e}")



