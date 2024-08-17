import streamlit as st
from google.cloud import firestore
import matplotlib.pyplot as plt
import pandas as pd

# Initialize Firestore
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

# Set page layout and title
st.set_page_config(layout="wide")
st.title('Farm Analytics')

# Dropdown for selecting a Firestore collection
collection_name = st.selectbox('Select Collection', [
    'testing', 'TechDemo', 'Plot1', 'Mr.Arjun', 'M1V6_SS_Testing', 
    'M1V6_GoldStandard', 'DevOps', 'DevMode', 'debugging'
])

# Dropdown for selecting a row number
row_number = st.text_input('Enter Row number', '')

# Ensure that a collection and row number are selected
if collection_name and row_number:
    try:
        # Query Firestore based on selected collection and row number
        query = db.collection(collection_name).where('RowNo', '==', int(row_number))
        query_results = [doc.to_dict() for doc in query.stream()]
    except Exception as e:
        st.error(f"Failed to retrieve data: {e}")
        st.stop()

    if not query_results:
        st.write("No data found matching the specified criteria.")
    else:
        # Initialize counters for Infected and Healthy statuses
        infected_count = 0
        healthy_count = 0

        # Count the number of Infected and Healthy scans
        for doc in query_results:
            inf_status = doc.get('InfStat', 'Healthy')
            if inf_status == 'Infected':
                infected_count += 1
            elif inf_status == 'Healthy':
                healthy_count += 1

        # Prepare data for pie chart
        labels = ['Infected', 'Healthy']
        sizes = [infected_count, healthy_count]
        colors = ['#ff9999','#66b3ff']
        
        # Plot the pie chart
        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.title(f'Infection Status for Row {row_number} in {collection_name} Collection')

        # Display the pie chart
        st.pyplot(fig)

        # Display the counts
        st.write(f"Total Scans: {infected_count + healthy_count}")
        st.write(f"Infected: {infected_count}")
        st.write(f"Healthy: {healthy_count}")
else:
    st.write("Please select a collection and enter a plot number.")
