import pandas as pd
import numpy as np
import streamlit as st
import os

st.title("Proposal Reviewer Assignment Generator")

uploaded_files = st.file_uploader("Upload reviewer preference files", type=["xlsx"], accept_multiple_files=True)

reviewers_per_proposal = st.slider("How many reviewers per proposal?", 1, 5, 3)

# Add a button to trigger processing
if uploaded_files:
    if st.button("Generate Assignments"):
        preference_data = {}
        pi_info = None
        proposal_ids = None

        # Read and parse each uploaded file
        for uploaded in uploaded_files:
            # Extract reviewer name from filename
            reviewer_name = os.path.basename(uploaded.name).split("template")[-1].replace(".xlsx", "").strip()

            # Read Excel file, no header
            df = pd.read_excel(uploaded, header=None)

            # Extract relevant columns starting from row 4 (index 3)
            scores = df.iloc[3:, 0].reset_index(drop=True)
            ids = df.iloc[3:, 1].astype(str).reset_index(drop=True)
            pi_last = df.iloc[3:, 2].astype(str).reset_index(drop=True)
            institution = df.iloc[3:, 4].astype(str).reset_index(drop=True)

            # Validate that Proposal IDs are consistent across files
            if proposal_ids is None:
                proposal_ids = ids
                # Save PI and Institution info for display
                pi_info = pd.DataFrame({
                    "Proposal ID": ids,
                    "PI Last Name": pi_last,
                    "Institution": institution
                }).set_index("Proposal ID")
            elif not proposal_ids.equals(ids):
                st.error("⚠️ Proposal IDs do not match across reviewer files.")
