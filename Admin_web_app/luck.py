import streamlit as st
import pandas as pd

# Define the collection file paths in your GitHub repository
GITHUB_REPO_URL = "https://github.com/111DataScienceWizard/TREBIRTH/tree/main/Admin_web_app"
collection_file_paths = {
    'collection_1': 'Admin_web_app/collection_1.xlsx',
    'collection_2': 'Admin_web_app/collection_2.xlsx',
    'collection_3': 'Admin_web_app/collection_3.xlsx',
    'collection_4': 'Admin_web_app/collection_4.xlsx',
    'collection_5': 'Admin_web_app/collection_5.xlsx',
    'collection_6': 'Admin_web_app/collection_6.xlsx',
    'collection_7': 'Admin_web_app/collection_7.xlsx',
    'collection_9': 'Admin_web_app/collection_9.xlsx',
    'collection_10': 'Admin_web_app/collection_10.xlsx',
    'collection_11': 'Admin_web_app/collection_11.xlsx',
    'collection_12': 'Admin_web_app/collection_12.xlsx',
}

# Function to load the data from the GitHub repository
@st.cache_data
def load_collection(collection_name):
    file_url = GITHUB_REPO_URL + collection_file_paths[collection_name]
    df = pd.read_excel(file_url)
    return df

# App title
st.title("Collection Data Viewer")

# Multiselect for collections (Dropdown 1)
collections = st.multiselect(
    "Select collection(s):", 
    options=list(collection_file_paths.keys()), 
    help="You can select one or multiple collections."
)

# Create a placeholder for the second dropdown
if collections:
    # Load data for all selected collections
    all_data = pd.DataFrame()

    for collection in collections:
        df = load_collection(collection)
        all_data = pd.concat([all_data, df])
    
    # Extract unique dates for the selected collections
    all_data['Date of Scans'] = pd.to_datetime(all_data['Date of Scans'])
    unique_dates = all_data['Date of Scans'].dt.date.unique()

    # Multiselect for unique dates (Dropdown 2)
    selected_dates = st.multiselect(
        "Select unique date(s):",
        options=sorted(unique_dates),
        help="Select one or more dates to filter data."
    )

    if selected_dates:
        # Filter the data by the selected dates
        filtered_data = all_data[all_data['Date of Scans'].dt.date.isin(selected_dates)]

        # Display the filtered data
        st.write("Filtered Data:")
        st.dataframe(filtered_data)

        # Print the columns based on the specific selection
        st.write("Filtered Collection Details:")
        st.write(filtered_data[['Device Name', 'Total Scan', 'Total Infected Scan', 'Total Healthy Scan', 
                                'Total Trees', 'Total Infected Trees', 'Total Healthy Trees', 'Date of Scans']])
