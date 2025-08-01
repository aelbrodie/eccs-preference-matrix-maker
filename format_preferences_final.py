import streamlit as st
import pandas as pd
import io

st.title("Proposal Preferences Formatter")

uploaded_files = st.file_uploader("Upload preference files (multiple allowed)", type=["xlsx"], accept_multiple_files=True)
template_file = st.file_uploader("Upload template Excel file", type=["xlsx"])

if uploaded_files and template_file:
    st.write(f"Uploaded {len(uploaded_files)} files")
    if st.button("Format Preference Files"):
        try:
            dfs = [pd.read_excel(f) for f in uploaded_files]
            df_combined = pd.concat(dfs, ignore_index=True)
            st.write(f"Combined data rows: {df_combined.shape[0]}")

            template = pd.read_excel(template_file)
            template_columns = template.columns.tolist()

            df_combined.columns = df_combined.columns.str.strip()
            if 'COI' in df_combined.columns:
                df_combined['COI'] = df_combined['COI'].fillna(0).astype(int)
                df_combined.loc[df_combined['COI'] == 0, 'COI'] = ""

            df_template = pd.DataFrame(columns=template_columns)
            for col in template_columns:
                if col in df_combined.columns:
                    df_template[col] = df_combined[col]
                else:
                    df_template[col] = ""

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False, sheet_name='Formatted')

            st.success("Formatting complete! Download your file below:")
            st.download_button(
                label="Download Formatted Excel",
                data=output.getvalue(),
                file_name="formatted_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.markdown("---")
            st.markdown("### ➡️ Ready for Step 2?")
            st.markdown(
                "[**Go to Step 2: Preference Matrix Generator**](https://ds.nsf.gov:8890/user/hkhosrav/streamlit-dashboard-panel-solver/)"
            )

        except Exception as e:
            st.error(f"Error processing files: {e}")
