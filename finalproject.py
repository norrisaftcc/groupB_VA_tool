# python -m streamlit run finalproject.py

# Read in a csv file as a pandas dataframe
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="VA Student Program Analysis", layout="wide")
st.header("📁 VA Dual Objective Tool")
   
# File uploader widget
uploaded_file = st.file_uploader(
        "Choose a CSV file to make available for download",
        type=['csv'],
        accept_multiple_files=False
    )
   
if uploaded_file is not None:
    import io

    file_bytes = uploaded_file.getvalue()

    # Check if it's a ZIP-like file (XLSX)
    if file_bytes[:2] == b'PK':
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            st.error(f"Excel file upload failed: {e}")
            st.stop()
    else:
        try:
            decoded = file_bytes.decode('latin1', errors='ignore')
            df = pd.read_csv(io.StringIO(decoded), on_bad_lines='skip')
        except Exception as e:
            st.error(f"CSV file upload failed: {e}")
            st.stop()

    st.success("File successfully loaded!")

    def manage_df(df):
        # drop unneeded columns
        df = df.drop(columns=['Current Status', 'Status Date', 'Current End Date','Advisor', 'Primary E-Mail', 'Smv Vetben Benefit ', 'Smv Vetben End Date '])
    
        # convert IDs to string
        df['ID'] = df['ID'].apply(lambda x: str(int(float(x))) if pd.notna(x) else '')

        # drop rows where ID or program is blank
        df = df.dropna(subset=['ID'])
        df = df.dropna(subset=['PROGRAMS'])
        
        # find duplicated IDs
        repeated_ids = df['ID'][df['ID'].duplicated(keep=False)]
    
        # filter original DF to only rows with repeated IDs
        df = df[df['ID'].isin(repeated_ids)]

        return df

    def associate_combos(df):

        # Create full program descriptions
        df['Program_Desc'] = df['PROGRAMS'] + ' - ' + df['Actual Title']

        # Group programs by student ID
        student_programs = df.groupby('ID')['Program_Desc'].unique().reset_index()
        student_program_codes = df.groupby('ID')['PROGRAMS'].unique().reset_index()

        # Merge descriptions and codes
        student_programs['Program_Codes'] = student_program_codes['PROGRAMS']

        # Define who qualifies: must have at least one Associate and one Certificate or Diploma
        def qualifies(programs):
            has_associate = any(p.startswith('A') for p in programs)
            has_cert_or_diploma = any(p.startswith(('C', 'D')) for p in programs)
            return has_associate and (has_cert_or_diploma or len([p for p in programs if p.startswith('A')]) > 1)

        # Filter to only qualifying students
        qualifying_students = student_programs[student_programs['Program_Codes'].apply(qualifies)]

        # Sort programs alphabetically for consistency
        qualifying_students['Program_Combo'] = qualifying_students['Program_Desc'].apply(
            lambda programs: ', '.join(sorted(programs))
        )

        # Group by program combo and collect IDs
        combo_to_ids = qualifying_students.groupby('Program_Combo')['ID'].apply(list).reset_index()
        combo_to_ids['Count'] = combo_to_ids['ID'].apply(len)
        combo_to_ids = combo_to_ids.sort_values(by='Count', ascending=False)

        print("Most common Associate + Certificate/Diploma combinations (with multiple Associates allowed):")
        
        combo_to_ids.to_csv('program_combinations_with_ids.csv', index=False)

        return combo_to_ids

    def cert_dip_combos(df):
        # Identify IDs of students who have any Associate's program
        associate_ids = df[df['PROGRAMS'].fillna('').str.startswith('A')]['ID'].unique()

        # Remove all records for those IDs
        df = df[~df['ID'].isin(associate_ids)]

        # Create full program descriptions
        df['Program_Desc'] = df['PROGRAMS'] + ' - ' + df['Actual Title']

        # Group remaining programs by student ID
        student_programs = df.groupby('ID')['Program_Desc'].unique().reset_index()
        student_program_codes = df.groupby('ID')['PROGRAMS'].unique().reset_index()

        # Merge descriptions and codes
        student_programs['Program_Codes'] = student_program_codes['PROGRAMS']

        # Define who qualifies: must have at least two non-Associate programs
        def qualifies(programs):
            return len(programs) >= 2 and all(p.startswith(('C', 'D')) for p in programs)

        # Filter to only qualifying students
        qualifying_students = student_programs[student_programs['Program_Codes'].apply(qualifies)]

        # Create sorted combo string
        qualifying_students.loc[:, 'Program_Combo'] = qualifying_students['Program_Desc'].apply(
            lambda programs: ', '.join(sorted(programs))
        )


        # Group by program combo and collect IDs
        combo_to_ids = qualifying_students.groupby('Program_Combo')['ID'].apply(list).reset_index()
        combo_to_ids['Count'] = combo_to_ids['ID'].apply(len)
        combo_to_ids = combo_to_ids.sort_values(by='Count', ascending=False)

        print("Most common Certificate + Certificate/Diploma combinations (excluding Associates):")

        combo_to_ids.to_csv('cert_dip_combinations_with_ids.csv', index=False)
        print(combo_to_ids)

        return combo_to_ids  

    def all_combos(df):
        # Create full program descriptions
        df['Program_Desc'] = df['PROGRAMS'] + ' - ' + df['Actual Title']

        # Group programs by student ID
        student_programs = df.groupby('ID')['Program_Desc'].unique().reset_index()
        student_program_codes = df.groupby('ID')['PROGRAMS'].unique().reset_index()

        # Merge descriptions and codes
        student_programs['Program_Codes'] = student_program_codes['PROGRAMS']

        # Define who qualifies: must have at least two programs from A/C/D
        def qualifies(programs):
            return len(programs) >= 2 and all(p.startswith(('A', 'C', 'D')) for p in programs)

        # Filter to only qualifying students
        qualifying_students = student_programs[student_programs['Program_Codes'].apply(qualifies)]

        # Create sorted combo string
        qualifying_students['Program_Combo'] = qualifying_students['Program_Desc'].apply(
            lambda programs: ', '.join(sorted(programs))
        )

        # Group by combo and count
        combo_to_ids = qualifying_students.groupby('Program_Combo')['ID'].apply(list).reset_index()
        combo_to_ids['Count'] = combo_to_ids['ID'].apply(len)
        combo_to_ids = combo_to_ids.sort_values(by='Count', ascending=False)

        print("Most common overall program combinations (any A/C/D):")
        combo_to_ids.to_csv('all_program_combinations_with_ids.csv', index=False)

        return combo_to_ids

    # Show preview
    st.write("File preview:")

    # Show the dataframe preview
    st.dataframe(df.head())
        
        # Create download button
    st.download_button(
        label="⬇️ Download This File",
        data=uploaded_file.getvalue(),
        file_name=uploaded_file.name,
        mime='text/csv'
    )
    

    st.title("VA Student Program Combination Analysis")
    st.markdown("Analyze common combinations of Associate, Certificate, and Diploma programs.")



    tab1, tab2, tab3 = st.tabs([ "Associate + Certificate/Diploma", "Certificate/Diploma", "Both"])

    # Load data
    with st.spinner("Analyzing Associate + Certificate/Diploma combinations..."):
        associates_df = associate_combos(df)

    with st.spinner("Analyzing Certificate/Diploma combinations..."):
        cert_dip_df = cert_dip_combos(df)

    with st.spinner("Analyzing All Valid Combinations..."):
        all_df = all_combos(df)


    with tab1:
        st.subheader("Associate + Certificate/Diploma Combos")
        min_count = st.slider("Minimum # of Students in Combo", 1, int(associates_df["Count"].max()), 5)
        filtered = associates_df[associates_df["Count"] >= min_count]
        st.write(f"Showing {len(filtered)} combinations")
        st.dataframe(filtered)

        st.subheader("Top 10 Combinations")
        top10 = filtered.sort_values(by="Count", ascending=False).head(10)
        chart = alt.Chart(top10).mark_bar().encode(
            x=alt.X('Count:Q'),
            y=alt.Y('Program_Combo:N', sort='-x'),
            tooltip=['Program_Combo', 'Count']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)

    with tab2:
        st.subheader("Certificate/Diploma Combos")
        min_count = st.slider("Minimum # of Students in Combo", 1, int(cert_dip_df["Count"].max()), 5, key="cert")
        filtered = cert_dip_df[cert_dip_df["Count"] >= min_count]
        st.write(f"Showing {len(filtered)} combinations")
        st.dataframe(filtered)

        st.subheader("Top 10 Combinations")
        top10 = filtered.sort_values(by="Count", ascending=False).head(10)
        chart = alt.Chart(top10).mark_bar().encode(
            x=alt.X('Count:Q'),
            y=alt.Y('Program_Combo:N', sort='-x'),
            tooltip=['Program_Combo', 'Count']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)

    with tab3:
        st.subheader("All Program Combos (A/C/D)")
        min_count = st.slider("Minimum # of Students in Combo", 1, int(all_df["Count"].max()), 5, key="all")
        filtered = all_df[all_df["Count"] >= min_count]
        st.write(f"Showing {len(filtered)} combinations")
        st.dataframe(filtered)

        st.subheader("Top 10 Combinations")
        top10 = filtered.sort_values(by="Count", ascending=False).head(10)
        chart = alt.Chart(top10).mark_bar().encode(
            x=alt.X('Count:Q'),
            y=alt.Y('Program_Combo:N', sort='-x'),
            tooltip=['Program_Combo', 'Count']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)

    # Add download button for the data
    st.download_button(
         label="⬇️ Download Associate + Certificate/Diploma Data",
        data=associates_df.to_csv(index=False),
         file_name='assoc_cert/dip_combinations.csv',
        mime='text/csv'
        )


    # Add download button for the data
    st.download_button(
        label="⬇️ Download Certificate/Diploma Combinations Data",
        data=cert_dip_df.to_csv(index=False),
        file_name='cert_diploma_combinations.csv',
        mime='text/csv'
        )  
    

    # Add download button for the data
    st.download_button(
         label="⬇️ Download All Program Combinations Data",
        data=all_df.to_csv(index=False),
         file_name='all_program_combinations.csv',
        mime='text/csv'
        )
