# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import streamlit as st
import pandas as pd
import io

st.title("Proposal Preferences Formatter")

# Upload preference files
uploaded_files = st.file_uploader("Upload preference files (multiple allowed)", type=["xlsx"], accept_multiple_files=True)

# Upload the formatting template
template_file = st.file_uploader("Upload template Excel file", type=["xlsx"], help="This is the format used to generate the preference matrix.")

if uploaded_files and template_file:
    # Read all input Excel files
    dfs = [pd.read_excel(f) for f in uploaded_files]
    df_combined = pd.concat(dfs, ignore_index=True)

    # Read the template file to get the correct column structure
    template = pd.read_excel(template_file)
    template_columns = template.columns.tolist()

    # Clean and prepare the input data
    df_combined.columns = df_combined.columns.str.strip()
    if 'COI' in df_combined.columns:
        df_combined['COI'] = df_combined['COI'].fillna(0).astype(int)
        df_combined.loc[df_combined['COI'] == 0, 'COI'] = ""

    # Match columns to the template structure
    df_template = pd.DataFrame(columns=template_columns)
    for col in template_columns:
        if col in df_combined.columns:
            df_template[col] = df_combined[col]
        else:
            df_template[col] = ""

    # Save to an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_template.to_excel(writer, index=False, sheet_name='Formatted')

    # Success message and download
    st.success("Formatting complete! Download your file below:")
    st.download_button(
        label="Download Formatted Excel",
        data=output.getvalue(),
        file_name="formatted_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Link to Step 2
    st.markdown("---")
    st.markdown("### ➡️ Ready for Step 2?")
    st.markdown(
        "[**Go to Step 2: Preference Matrix Generator**](https://ds.nsf.gov:8890/user/hkhosrav/streamlit-dashboard-panel-solver/) "
        "to complete the assignment process using your formatted sheet."
    )
#yay me text delete to run#


