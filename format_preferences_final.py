import pandas as pd
import numpy as np
import streamlit as st
import os
from io import BytesIO

st.set_page_config(page_title="Proposal Reviewer Assignment Generator")

# Custom CSS to expand Streamlit's default file uploader height
st.markdown("""
    <style>
    /* Make the file upload preview box taller so all files show */
    .stFileUploader > div > div {
        max-height: none !important;
    }
    </style>
""", unsafe_allow_html=True)

        .file-list-container {
        max-height: 600px;
        overflow-y: auto;
        padding-right: 10px;
    }

    .stFileUploader > div {
        max-width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Proposal Reviewer Assignment Generator")

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

            final_df = pi_info.reset_index().merge(assignment_df, on="Proposal ID")

            # Add COI summary column listing all reviewers with COI=0 per proposal
            coi_list = []
            for proposal in final_df["Proposal ID"]:
                coi_reviewers = [r for r in combined.columns if proposal in combined.index and combined.at[proposal, r] == 0]
                coi_list.append(", ".join(coi_reviewers) if coi_reviewers else "")
            final_df["COIs"] = coi_list

            # Style function to make COIs column bold and red
            def style_cois(val):
                if val:
                    return "color: red; font-weight: bold;"
                return ""

            # Set Proposal ID as index for display
            display_df = final_df.set_index("Proposal ID")

            st.success("✅ Reviewer assignments complete with COI listing.")

            st.dataframe(
                display_df.style.applymap(style_cois, subset=["COIs"])
            )

            # --- CSV download ---
            csv = final_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Assignments CSV",
                csv,
                "assignments.csv",
                "text/csv",
                key="download_assignments_csv"
            )

            # --- Excel download ---
            excel_output = BytesIO()
            with pd.ExcelWriter(excel_output, engine="openpyxl") as writer:
                final_df.to_excel(writer, index=False, sheet_name="Assignments")
            excel_output.seek(0)

            st.download_button(
                label="📥 Download Assignments Excel File",
                data=excel_output,
                file_name="assignments.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_assignments_excel"
            )


