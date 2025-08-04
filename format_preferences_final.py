import pandas as pd
import numpy as np
import streamlit as st
import os

st.title("Proposal Reviewer Assignment Generator")

# Number input for reviewers per proposal
reviewers_per_proposal = st.number_input(
    "Number of reviewers per proposal",
    min_value=1,
    max_value=20,
    value=3,
    step=1,
    format="%d"
)

# File uploader for preference files
uploaded_files = st.file_uploader(
    "Upload reviewer preference files",
    type=["xlsx"],
    accept_multiple_files=True
)

if st.button("Generate Assignments"):

    if not uploaded_files:
        st.warning("Please upload at least one reviewer preference file before generating assignments.")
    else:
        preference_data = {}
        pi_info = None
        proposal_ids = None
        error_occurred = False

        for uploaded in uploaded_files:
            reviewer_name = os.path.basename(uploaded.name).split("template")[-1].replace(".xlsx", "").strip()
            df = pd.read_excel(uploaded, header=None)

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
                error_occurred = True
                break

            preference_data[reviewer_name] = pd.Series(scores.values, index=ids)

        if not error_occurred:
            combined = pd.DataFrame(preference_data)
            combined.index.name = "Proposal ID"
            combined = combined.apply(pd.to_numeric, errors="coerce").fillna(10).astype(int)

            # Debug prints to verify combined DataFrame
            st.write("Combined preference matrix (sample):")
            st.write(combined.head())

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

            assignment_df = pd.DataFrame.from_dict(assignments, orient="index")
            assignment_df.index.name = "Proposal ID"
            assignment_df.columns = [f"Reviewer {i+1}" for i in range(assignment_df.shape[1])]
            assignment_df = assignment_df.reset_index()

            # Debug prints to verify assignment_df
            st.write("Assignment DataFrame (sample):")
            st.write(assignment_df.head())

            final_df = pi_info.reset_index().merge(assignment_df, on="Proposal ID")

            # Debug print for final_df
            st.write("Final merged DataFrame (sample):")
            st.write(final_df.head())
            # Add COI summary column listing all reviewers with COI=0 per proposal
coi_list = []
for proposal in final_df["Proposal ID"]:
    coi_reviewers = [r for r in combined.columns if proposal in combined.index and combined.at[proposal, r] == 0]
    coi_list.append(", ".join(coi_reviewers) if coi_reviewers else "")

final_df["COIs"] = coi_list

# Set Proposal ID as index for display
display_df = final_df.set_index("Proposal ID")

st.dataframe(display_df)


            display_df = final_df.copy()

            # Mark COIs robustly with debug outputs
            for i, row in display_df.iterrows():
                proposal = str(row["Proposal ID"]).strip()
                for col in assignment_df.columns[1:]:
                    reviewer = str(row[col]).strip()
                    if reviewer in combined.columns and proposal in combined.index:
                        score = combined.at[proposal, reviewer]
                        if pd.isna(score) or score == 0:
                            display_df.at[i, col] = "🚫 COI"

            # Set Proposal ID as index to avoid extra integer index column
            display_df = display_df.set_index("Proposal ID")

            st.success("✅ Reviewer assignments complete with COI marking.")
            st.dataframe(display_df)

            csv = final_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇️ Download Assignments CSV",
                csv,
                "assignments.csv",
                "text/csv",
                key="download_assignments_csv"
            )

