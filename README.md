# VA Dual Objective Tool

A Streamlit application that analyzes program enrollment combinations for VA students. This tool helps identify common combinations of degree and certificate programs to assist with VA funding eligibility.

## Features

- Upload and analyze student program enrollment data
- Identify common program combinations:
  - Associate degree + Certificate/Diploma combinations
  - Certificate/Diploma combinations (without Associates)
  - All valid program combinations
- Interactive filtering by minimum number of students
- Data visualizations for the most common combinations
- Download analyzed data in CSV format

## Prerequisites

- Python 3.8+
- Required packages listed in `requirements.txt`

## Local Deployment

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/groupB_VA_tool.git
   cd groupB_VA_tool
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run finalproject.py
   ```

4. The application will open in your default web browser at `http://localhost:8501`

## Deploying to Streamlit Community Cloud

1. Create an account on [Streamlit Community Cloud](https://streamlit.io/cloud)

2. Connect your GitHub repository:
   - Log in to Streamlit Community Cloud
   - Click "New app"
   - Connect your GitHub account and select this repository
   - Select the main branch and enter the path to the main file: `finalproject.py`
   - Click "Deploy"

3. Your app will be available at a public URL provided by Streamlit

## Data Format

The tool expects a CSV file with the following columns:
- ID: Student identifier
- PROGRAMS: Program code (A for Associates, C for Certificate, D for Diploma)
- Actual Title: Program name/description
- Additional demographic information (optional)

## Usage

1. Upload your CSV file through the file uploader
2. View the analysis in the three tabs:
   - Associate + Certificate/Diploma
   - Certificate/Diploma
   - Both (All combinations)
3. Use the sliders to filter by minimum number of students
4. Download the processed data as needed

## License

[Add license information here]