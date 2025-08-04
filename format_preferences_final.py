import pandas as pd
import numpy as np
import streamlit as st
import os

st.title("Proposal Reviewer Assignment Generator")

uploaded_files = st.file_uploader("Upload reviewer preference files", type=["xlsx"], accept_multiple_files=True)

reviewers_per_proposal = st.slider("How many reviewers per proposal?", 1, 5, 3)

if uploaded_files:
    preference_data = {}
    pi_info = {}
    proposal_ids = None

    for uploaded in uploaded_files:
        reviewer_name = os.path.basename(uploaded.name).split("template")[-1].replace(".xlsx", "").strip()
        df = pd.read_excel(uploaded, header=None)

        # Extract from row 4 onward
        scores = df.iloc[3:, 0].reset_index(drop=True)
        ids = df.iloc[3:, 1].astype(str).reset_index(drop=True)
        pi_last = df.iloc[3:, 2].astype(str).reset_index(drop=True)
        institution = df.iloc[3:, 4].astype(str).reset_index(drop=True)

        if proposal_ids is None:
            proposal_ids = ids
            pi_info = pd.DataFrame({
                "Proposal ID": ids,
                "PI Last Name": pi_last,
                "Institution": institution
            }).set_index("Proposal ID")
        elif not proposal_ids.equals(ids):
            st.error("⚠️ Proposal IDs do not match across reviewer files.")
            st.stop()

        preference_data[reviewer_name] = pd.Series(scores.values, index=ids)

    # Combine preferences
    combined = pd.DataFrame(preference_data)
    combined.index.name = "Proposal ID"
    combined = combined.apply(pd.to_numeric, errors="coerce").fillna(10).astype(int)

    # Build cost matrix
    cost_matrix = combined.copy()
    cost_matrix[cost_matrix == 0] = 1000

    # Assignment logic
    assignments = {proposal: [] for proposal in combined.index}
    reviewer_load = {r: 0 for r in combined.columns}
    total_reviews = reviewers_per_proposal * len(assignments)
    max_reviews = (total_reviews // len(reviewer_load)) + 1

    for proposal in assignments:
        scores = cost_matrix.loc[proposal]
        sorted_reviewers = scores.sort_values().index

        count = 0
        for r in sorted_reviewers:
            if scores[r] >= 1000:
                continue
            if reviewer_load[r] < max_reviews:
                assignments[proposal].append(r)
                reviewer_load[r] += 1
                count += 1
            if count >= reviewers_per_proposal:
                break

    # Create assignment DataFrame
    assignment_df = pd.DataFrame.from_dict(assignments, orient="index")
    assignment_df.index.name = "Proposal ID"
    assignment_df.columns = [f"Reviewer {i+1}" for i in range(assignment_df.shape[1])]
    assignment_df = assignment_df.reset_index()

    # Merge PI and institution info
    final_df = pi_info.reset_index().merge(assignment_df, on="Proposal ID")

    # Mark COIs for display
    display_df = final_df.copy()
    for i, row in display_df.iterrows():
        proposal = row["Proposal ID"]
        for col in assignment_df.columns[1:]:
            reviewer = row[col]
            if combined.at[proposal, reviewer] == 0:
                display_df.at[i, col] = "COI"

    def highlight_coi(val):
        if val == "COI":
            return "color: red; font-weight: bold;"
        return ""

    st.success("✅ Reviewer assignments complete.")
    st.dataframe(display_df.style.applymap(highlight_coi, subset=assignment_df.columns[1:]))

    # CSV download (without COI substitutions)
    csv = final_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "assignments.csv", "text/csv")


    for uploaded in uploaded_files:
        # Extract reviewer name from filename
        reviewer_name = os.path.basename(uploaded.name).split("template")[-1].replace(".xlsx", "").strip()
        
        # Read Excel and skip instructions
        df = pd.read_excel(uploaded, header=None)

        # Preferences start from row 4 (index 3), Proposal ID in col 1
        scores = df.iloc[3:, 0].reset_index(drop=True)
        ids = df.iloc[3:, 1].astype(str).reset_index(drop=True)

        if proposal_ids is None:
            proposal_ids = ids
        elif not proposal_ids.equals(ids):
            st.error("⚠️ Proposal IDs do not match across reviewer files.")
            st.stop()

        preference_data[reviewer_name] = pd.Series(scores.values, index=ids)

    combined = pd.DataFrame(preference_data)
    combined.index.name = "Proposal ID"
    combined = combined.apply(pd.to_numeric, errors="coerce").fillna(10).astype(int)

    # COIs = 0 → set to very high cost
    cost_matrix = combined.copy()
    cost_matrix[cost_matrix == 0] = 1000

    assignments = {proposal: [] for proposal in combined.index}
    reviewer_load = {r: 0 for r in combined.columns}
    total_reviews = reviewers_per_proposal * len(assignments)
    max_reviews = (total_reviews // len(reviewer_load)) + 1

    for proposal in assignments:
        scores = cost_matrix.loc[proposal]
        sorted_reviewers = scores.sort_values().index

        count = 0
        for r in sorted_reviewers:
            if scores[r] >= 1000:
                continue
            if reviewer_load[r] < max_reviews:
                assignments[proposal].append(r)
                reviewer_load[r] += 1
                count += 1
            if count >= reviewers_per_proposal:
                break

    # Final result
    assignment_df = pd.DataFrame.from_dict(assignments, orient="index")
    assignment_df.index.name = "Proposal ID"
    assignment_df.columns = [f"Reviewer {i+1}" for i in range(assignment_df.shape[1])]
    
    st.success("✅ Reviewer assignments complete.")
    st.dataframe(assignment_df)

    csv = assignment_df.to_csv(index=True).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "assignments.csv", "text/csv")

