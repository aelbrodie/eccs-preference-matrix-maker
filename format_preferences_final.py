import pandas as pd
import numpy as np
import streamlit as st
import os

st.title("Proposal Reviewer Assignment Generator")

# Numeric input for number of reviewers per proposal (min=1, max=20 for example)
reviewers_per_proposal = st.number_input(
    "Number of reviewers per proposal",
    min_value=1,
    max_value=20,
    value=3,
    step=1,
    format="%d"
)

uploaded_files = st.file_uploader(
    "Upload reviewer preference files",
    type=["xlsx"],
    accept_multiple_files=True
)

# Generate Assignments button always visible
if st.button("Generate Assignments"):

    if not uploaded_files:
        st.warning("Please upload at least one reviewer preference file before generating assignments.")
    else:
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
                st.stop()

            preference_data[reviewer_name] = pd.Series(scores.values, index=ids)

        # Combine all reviewers' preferences into a DataFrame
        combined = pd.DataFrame(preference_data)
        combined.index.name = "Proposal ID"
        # Convert all values to numeric, treat missing as 10 (low preference)
        combined = combined.apply(pd.to_numeric, errors="coerce").fillna(10).astype(int)

        # Build cost matrix: replace 0 (COI) with very high cost (e.g., 1000) to avoid assignment
        cost_matrix = combined.copy()
        cost_matrix[cost_matrix == 0] = 1000

        # Initialize assignments and reviewer load
        assignments = {proposal: [] for proposal in combined.index}
        reviewer_load = {r: 0 for r in combined.columns}

        total_reviews = reviewers_per_proposal * len(assignments)
        max_reviews = (total_reviews // len(reviewer_load)) + 1

        # Assign reviewers to proposals based on cost matrix and load
        for proposal in assignments:
            scores = cost_matrix.loc[proposal]
            sorted_reviewers = scores.sort_values().index

            count = 0
            for r in sorted_reviewers:
                if scores[r] >= 1000:
                    continue  # skip COI
                if reviewer_load[r] < max_reviews:
                    assignments[proposal].append(r)
                    reviewer_load[r] += 1
                    count += 1
                if count >= reviewers_per_proposal:
                    break

        # Build assignment DataFrame
        assignment_df = pd.DataFrame.from_dict(assignments, orient="index")
        assignment_df.index.name = "Proposal ID"
        assignment_df.columns = [f"Reviewer {i+1}" for i in range(assignment_df.shape[1])]
        assignment_df = assignment_df.reset_index()

        # Merge with PI and Institution info
        final_df = pi_info.reset_index().merge(assignment_df, on="Proposal ID")

      # Mark COI in red if a reviewer had score 0 (conflict)
display_df = final_df.copy()
for i, row in display_df.iterrows():
    proposal = row["Proposal ID"]
    for col in assignment_df.columns[1:]:
        reviewer = row[col]
        # Only check if reviewer is a string and a valid column
        if isinstance(reviewer, str) and reviewer in combined.columns:
            if combined.at[proposal, reviewer] == 0:
                display_df.at[i, col] = "COI"


        # ... [everything else same as before] ...

    def highlight_coi(val):
        if val == "COI":
            return "color: red; font-weight: bold;"
        return "COI"

st.success("✅ Reviewer assignments complete.")

# Show debug info for COI marking - optional, remove after confirming
# st.write(display_df)  

# Use st.table with style to show COI in red (may depend on Streamlit version)
try:
    st.table(display_df.style.applymap(highlight_coi, subset=assignment_df.columns[1:]))
except Exception as e:
    st.write("Failed to apply styling, showing plain table instead.")
    st.table(display_df)

# Prepare CSV download
csv = final_df.to_csv(index=False).encode("utf-8")
st.write(f"CSV bytes type: {type(csv)}")  # Debug line - remove after confirmed

st.download_button(
    "⬇️ Download Assignments CSV",
    csv,
    "assignments.csv",
    "text/csv",
    key="download_assignments_csv"
)









