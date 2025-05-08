# python -m streamlit run finalproject.py

# Import necessary libraries
import pandas as pd
import streamlit as st
import altair as alt
import io

st.set_page_config(page_title="VA Student Program Analysis", layout="wide")
st.header("📁 VA Dual Objective Tool")
   
# File uploader widget
uploaded_file = st.file_uploader(
        "Choose a file to upload (CSV or Excel)",
        type=['csv', 'xlsx', 'xls'],
        accept_multiple_files=False
    )
   
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_ext = uploaded_file.name.split('.')[-1].lower()

    try:
        # Handle different file types
        if file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:  # CSV files
            decoded = file_bytes.decode('latin1', errors='ignore')
            df = pd.read_csv(io.StringIO(decoded), on_bad_lines='skip')
        
        # Verify required columns exist
        required_columns = ['ID', 'PROGRAMS', 'Actual Title']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"File missing required columns: {', '.join(missing_columns)}")
            st.stop()
            
        st.success("File successfully loaded!")
    except Exception as e:
        st.error(f"File upload failed: {e}")
        st.stop()

    def prepare_data(df):
        """
        Prepare the data for analysis:
        - Handle missing values
        - Convert IDs to string format
        - Keep only rows with IDs in multiple programs
        """
        try:
            # Create a copy to avoid modifying the original
            df_processed = df.copy()
            
            # Find columns that exist in the dataframe
            cols_to_drop = []
            for col in ['Current Status', 'Status Date', 'Current End Date', 'Advisor', 'Primary E-Mail', 
                        'Smv Vetben Benefit ', 'Smv Vetben End Date ']:
                if col in df_processed.columns:
                    cols_to_drop.append(col)
                
            # Drop unneeded columns if they exist
            if cols_to_drop:
                df_processed = df_processed.drop(columns=cols_to_drop)
        
            # Convert IDs to string safely
            try:
                df_processed['ID'] = df_processed['ID'].apply(
                    lambda x: str(int(float(x))) if pd.notna(x) and str(x).strip() != '' else ''
                )
            except Exception as e:
                st.warning(f"Some IDs could not be converted properly: {e}")
                # Fallback to safer conversion
                df_processed['ID'] = df_processed['ID'].astype(str)

            # Drop rows where ID or program is blank
            df_processed = df_processed.dropna(subset=['ID'])
            df_processed = df_processed.dropna(subset=['PROGRAMS'])
            
            # Find duplicated IDs (students with multiple programs)
            if not df_processed.empty:
                repeated_ids = df_processed['ID'][df_processed['ID'].duplicated(keep=False)]
                
                # Only filter if we found duplicates
                if len(repeated_ids) > 0:
                    # Filter original DF to only rows with repeated IDs
                    df_processed = df_processed[df_processed['ID'].isin(repeated_ids)]
                else:
                    st.warning("No students with multiple programs found. Analysis may be limited.")
            else:
                st.warning("No valid data remains after filtering.")

            if df_processed.empty:
                st.error("No valid data to analyze after preparation.")
                
            return df_processed
        except Exception as e:
            st.error(f"Error preparing data: {e}")
            return df.copy()  # Return a copy of original data in case of error

    def associate_combos(df):
        """
        Find combinations of Associate degrees with Certificates/Diplomas
        or combinations of multiple Associate degrees
        """
        try:
            if df.empty:
                st.warning("Empty dataframe provided to associate_combos")
                return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])
                
            # Create full program descriptions
            df['Program_Desc'] = df['PROGRAMS'] + ' - ' + df['Actual Title']

            # Group programs by student ID
            student_programs = df.groupby('ID')['Program_Desc'].unique().reset_index()
            student_program_codes = df.groupby('ID')['PROGRAMS'].unique().reset_index()

            # Merge descriptions and codes
            student_programs['Program_Codes'] = student_program_codes['PROGRAMS']

            # Define who qualifies: must have at least one Associate and one Certificate or Diploma
            def qualifies(programs):
                try:
                    has_associate = any(str(p).startswith('A') for p in programs)
                    has_cert_or_diploma = any(str(p).startswith(('C', 'D')) for p in programs)
                    return has_associate and (has_cert_or_diploma or len([p for p in programs if str(p).startswith('A')]) > 1)
                except Exception:
                    # If there's any error in the program codes, be safe and exclude
                    return False

            # Filter to only qualifying students
            qualifying_students = student_programs[student_programs['Program_Codes'].apply(qualifies)]

            if qualifying_students.empty:
                st.warning("No qualifying Associate + Certificate/Diploma combinations found")
                return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])

            # Sort programs alphabetically for consistency
            qualifying_students['Program_Combo'] = qualifying_students['Program_Desc'].apply(
                lambda programs: ', '.join(sorted(programs))
            )

            # Group by program combo and collect IDs
            combo_to_ids = qualifying_students.groupby('Program_Combo')['ID'].apply(list).reset_index()
            combo_to_ids['Count'] = combo_to_ids['ID'].apply(len)
            combo_to_ids = combo_to_ids.sort_values(by='Count', ascending=False)
            
            # Save to CSV
            combo_to_ids.to_csv('program_combinations_with_ids.csv', index=False)

            return combo_to_ids
        except Exception as e:
            st.error(f"Error analyzing Associate combinations: {e}")
            return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])

    def cert_dip_combos(df):
        """
        Find combinations of Certificate/Diploma programs (excluding students with Associate degrees)
        """
        try:
            if df.empty:
                st.warning("Empty dataframe provided to cert_dip_combos")
                return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])
                
            # Identify IDs of students who have any Associate's program
            associate_ids = df[df['PROGRAMS'].fillna('').str.startswith('A')]['ID'].unique()

            # Remove all records for those IDs
            filtered_df = df[~df['ID'].isin(associate_ids)]
            
            if filtered_df.empty:
                st.warning("No Certificate/Diploma programs found after filtering out Associate degrees")
                return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])

            # Create full program descriptions
            filtered_df['Program_Desc'] = filtered_df['PROGRAMS'] + ' - ' + filtered_df['Actual Title']

            # Group remaining programs by student ID
            student_programs = filtered_df.groupby('ID')['Program_Desc'].unique().reset_index()
            student_program_codes = filtered_df.groupby('ID')['PROGRAMS'].unique().reset_index()

            # Merge descriptions and codes
            student_programs['Program_Codes'] = student_program_codes['PROGRAMS']

            # Define who qualifies: must have at least two non-Associate programs
            def qualifies(programs):
                try:
                    return len(programs) >= 2 and all(str(p).startswith(('C', 'D')) for p in programs)
                except Exception:
                    # If there's any error in the program codes, be safe and exclude
                    return False

            # Filter to only qualifying students
            qualifying_students = student_programs[student_programs['Program_Codes'].apply(qualifies)]
            
            if qualifying_students.empty:
                st.warning("No qualifying Certificate/Diploma combinations found")
                return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])

            # Create sorted combo string
            qualifying_students['Program_Combo'] = qualifying_students['Program_Desc'].apply(
                lambda programs: ', '.join(sorted(programs))
            )

            # Group by program combo and collect IDs
            combo_to_ids = qualifying_students.groupby('Program_Combo')['ID'].apply(list).reset_index()
            combo_to_ids['Count'] = combo_to_ids['ID'].apply(len)
            combo_to_ids = combo_to_ids.sort_values(by='Count', ascending=False)

            # Save to CSV
            combo_to_ids.to_csv('cert_dip_combinations_with_ids.csv', index=False)

            return combo_to_ids
        except Exception as e:
            st.error(f"Error analyzing Certificate/Diploma combinations: {e}")
            return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])

    def all_combos(df):
        """
        Find all combinations of programs (Associates, Certificates, Diplomas)
        """
        try:
            if df.empty:
                st.warning("Empty dataframe provided to all_combos")
                return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])
                
            # Create full program descriptions
            df['Program_Desc'] = df['PROGRAMS'] + ' - ' + df['Actual Title']

            # Group programs by student ID
            student_programs = df.groupby('ID')['Program_Desc'].unique().reset_index()
            student_program_codes = df.groupby('ID')['PROGRAMS'].unique().reset_index()

            # Merge descriptions and codes
            student_programs['Program_Codes'] = student_program_codes['PROGRAMS']

            # Define who qualifies: must have at least two programs from A/C/D
            def qualifies(programs):
                try:
                    return len(programs) >= 2 and all(str(p).startswith(('A', 'C', 'D')) for p in programs)
                except Exception:
                    # If there's any error in the program codes, be safe and exclude
                    return False

            # Filter to only qualifying students
            qualifying_students = student_programs[student_programs['Program_Codes'].apply(qualifies)]
            
            if qualifying_students.empty:
                st.warning("No qualifying program combinations found")
                return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])

            # Create sorted combo string
            qualifying_students['Program_Combo'] = qualifying_students['Program_Desc'].apply(
                lambda programs: ', '.join(sorted(programs))
            )

            # Group by combo and count
            combo_to_ids = qualifying_students.groupby('Program_Combo')['ID'].apply(list).reset_index()
            combo_to_ids['Count'] = combo_to_ids['ID'].apply(len)
            combo_to_ids = combo_to_ids.sort_values(by='Count', ascending=False)

            # Save to CSV
            combo_to_ids.to_csv('all_program_combinations_with_ids.csv', index=False)

            return combo_to_ids
        except Exception as e:
            st.error(f"Error analyzing all program combinations: {e}")
            return pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])

    # Prepare the dataframe
    df = prepare_data(df)

    # Show preview
    st.write("File preview:")
    st.dataframe(df.head())
    
    # Create download button for original file
    st.download_button(
        label="⬇️ Download This File",
        data=uploaded_file.getvalue(),
        file_name=uploaded_file.name,
        mime='text/csv'
    )
    
    st.title("VA Student Program Combination Analysis")
    st.markdown("Analyze common combinations of Associate, Certificate, and Diploma programs.")

    # Create tabs for different analyses
    tab1, tab2, tab3 = st.tabs(["Associate + Certificate/Diploma", "Certificate/Diploma", "Both"])

    # Load data safely
    try:
        with st.spinner("Analyzing Associate + Certificate/Diploma combinations..."):
            associates_df = associate_combos(df)

        with st.spinner("Analyzing Certificate/Diploma combinations..."):
            cert_dip_df = cert_dip_combos(df)

        with st.spinner("Analyzing All Valid Combinations..."):
            all_df = all_combos(df)
    except Exception as e:
        st.error(f"Error during data analysis: {e}")
        associates_df = pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])
        cert_dip_df = pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])
        all_df = pd.DataFrame(columns=['Program_Combo', 'ID', 'Count'])

    # Tab 1: Associate + Certificate/Diploma
    with tab1:
        st.subheader("Associate + Certificate/Diploma Combos")
        if not associates_df.empty:
            try:
                max_count = int(associates_df["Count"].max()) if len(associates_df) > 0 else 1
                default_min = min(5, max_count)
                min_count = st.slider("Minimum # of Students in Combo", 1, max_count, default_min)
                filtered = associates_df[associates_df["Count"] >= min_count]
                st.write(f"Showing {len(filtered)} combinations")
                st.dataframe(filtered)

                if not filtered.empty:
                    st.subheader("Top 10 Combinations")
                    top10 = filtered.sort_values(by="Count", ascending=False).head(10)
                    if len(top10) > 0:
                        chart = alt.Chart(top10).mark_bar().encode(
                            x=alt.X('Count:Q'),
                            y=alt.Y('Program_Combo:N', sort='-x'),
                            tooltip=['Program_Combo', 'Count']
                        ).properties(height=400)
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.info("Not enough data to display chart")
                else:
                    st.info("No combinations match the minimum count filter")
            except Exception as e:
                st.error(f"Error displaying Associate + Certificate combinations: {e}")
        else:
            st.warning("No Associate + Certificate/Diploma combinations found in the data.")

    # Tab 2: Certificate/Diploma
    with tab2:
        st.subheader("Certificate/Diploma Combos")
        if not cert_dip_df.empty:
            try:
                max_count = int(cert_dip_df["Count"].max()) if len(cert_dip_df) > 0 else 1
                default_min = min(5, max_count)
                min_count = st.slider("Minimum # of Students in Combo", 1, max_count, default_min, key="cert")
                filtered = cert_dip_df[cert_dip_df["Count"] >= min_count]
                st.write(f"Showing {len(filtered)} combinations")
                st.dataframe(filtered)

                if not filtered.empty:
                    st.subheader("Top 10 Combinations")
                    top10 = filtered.sort_values(by="Count", ascending=False).head(10)
                    if len(top10) > 0:
                        chart = alt.Chart(top10).mark_bar().encode(
                            x=alt.X('Count:Q'),
                            y=alt.Y('Program_Combo:N', sort='-x'),
                            tooltip=['Program_Combo', 'Count']
                        ).properties(height=400)
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.info("Not enough data to display chart")
                else:
                    st.info("No combinations match the minimum count filter")
            except Exception as e:
                st.error(f"Error displaying Certificate/Diploma combinations: {e}")
        else:
            st.warning("No Certificate/Diploma combinations found in the data.")

    # Tab 3: All program combinations
    with tab3:
        st.subheader("All Program Combos (A/C/D)")
        if not all_df.empty:
            try:
                max_count = int(all_df["Count"].max()) if len(all_df) > 0 else 1
                default_min = min(5, max_count)
                min_count = st.slider("Minimum # of Students in Combo", 1, max_count, default_min, key="all")
                filtered = all_df[all_df["Count"] >= min_count]
                st.write(f"Showing {len(filtered)} combinations")
                st.dataframe(filtered)

                if not filtered.empty:
                    st.subheader("Top 10 Combinations")
                    top10 = filtered.sort_values(by="Count", ascending=False).head(10)
                    if len(top10) > 0:
                        chart = alt.Chart(top10).mark_bar().encode(
                            x=alt.X('Count:Q'),
                            y=alt.Y('Program_Combo:N', sort='-x'),
                            tooltip=['Program_Combo', 'Count']
                        ).properties(height=400)
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.info("Not enough data to display chart")
                else:
                    st.info("No combinations match the minimum count filter")
            except Exception as e:
                st.error(f"Error displaying All Program combinations: {e}")
        else:
            st.warning("No valid program combinations found in the data.")

    # Download buttons for processed data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Only enable download if data exists
        if not associates_df.empty:
            st.download_button(
                label="⬇️ Download Associate + Certificate/Diploma Data",
                data=associates_df.to_csv(index=False),
                file_name='assoc_cert_dip_combinations.csv',
                mime='text/csv'
            )
        else:
            st.button("⬇️ Download Associate + Certificate/Diploma Data", disabled=True)

    with col2:
        if not cert_dip_df.empty:
            st.download_button(
                label="⬇️ Download Certificate/Diploma Combinations Data",
                data=cert_dip_df.to_csv(index=False),
                file_name='cert_diploma_combinations.csv',
                mime='text/csv'
            )
        else:
            st.button("⬇️ Download Certificate/Diploma Combinations Data", disabled=True)
    
    with col3:
        if not all_df.empty:
            st.download_button(
                label="⬇️ Download All Program Combinations Data",
                data=all_df.to_csv(index=False),
                file_name='all_program_combinations.csv',
                mime='text/csv'
            )
        else:
            st.button("⬇️ Download All Program Combinations Data", disabled=True)
            
    # Add footer with info about the tool
    st.markdown("---")
    st.markdown("""
    **VA Dual Objective Tool** - Analyze program enrollment combinations for VA students
    
    This tool identifies common combinations of degrees and certificates to assist with VA funding eligibility.
    """)
