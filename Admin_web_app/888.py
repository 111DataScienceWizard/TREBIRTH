import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
from google.cloud import firestore

# Initialize Firestore client
db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")

st.set_page_config(layout="wide")
st.title('Farm Analytics')

# Collection dates mapping
collection_dates = {
    'TechDemo': ['2024-02-28', '2024-02-29'],
    'Plot1': [],  # No dates
    'M1V6_SS_Testing': ['2024-06-08', '2024-06-10', '2024-06-11', '2024-06-12', '2024-06-13', '2024-06-14', 
                        '2024-06-15', '2024-06-18', '2024-06-19', '2024-06-20', '2024-06-21'],
    'Mr.Arjun': ['2024-03-04', '2024-03-05'],
    'M1V6_GoldStandad': ['2024-06-25', '2024-06-26', '2024-06-28', '2024-06-29', '2024-07-01', '2024-07-03', 
                         '2024-07-06', '2024-07-08'],
    'DevOps': ['2024-03-11', '2024-03-12', '2024-03-13', '2024-03-14', '2024-03-15', '2024-03-16', 
               '2024-06-04', '2024-06-05'],
    'DevMode': ['2024-02-22', '2024-02-23', '2024-02-24', '2024-02-25', '2024-02-26', '2024-02-28'],
    'debugging': ['2024-06-10', '2024-06-13', '2024-06-14']
}

# Generate dropdown options with collection names only
dropdown_options = sorted(collection_dates.keys())

# Multi-select dropdown for collection names
selected_collections = st.multiselect('Select Collection(s)', dropdown_options, default=['TechDemo', 'debugging'])

# Process selected options to retrieve data and plot
if selected_collections:
    total_healthy = 0
    total_infected = 0
    collection_scan_counts = {}
    device_data = defaultdict(lambda: defaultdict(lambda: {'Healthy': 0, 'Infected': 0}))

    # Fetch data and plot pie charts
    for collection in selected_collections:
        st.write(f"**{collection} Collection**")

        # Print unique dates of the selected collection
        unique_dates = collection_dates.get(collection, [])
        if unique_dates:
            st.write(f"Unique Dates: {', '.join(unique_dates)}")
        else:
            st.write("No dates available for this collection.")

        # Retrieve all data for the selected collection
        docs = list(db.collection(collection).stream())

        # Initialize counters
        healthy_count = 0
        infected_count = 0
        total_scans = 0

        # Process and analyze the retrieved documents
        for doc in docs:
            data = doc.to_dict()
            
            if 'InfStat' in data:
                if data['InfStat'] == 'Healthy':
                    healthy_count += 1
                elif data['InfStat'] == 'Infected':
                    infected_count += 1
                total_scans += 1
            else:
                st.warning(f"Skipping document {doc.id} due to missing 'InfStat' field.")
        
        # Debug prints
        st.write(f"Collection: {collection}")
        st.write(f"Total Scans: {total_scans}")
        st.write(f"Healthy Scans: {healthy_count}")
        st.write(f"Infected Scans: {infected_count}")

        total_healthy += healthy_count
        total_infected += infected_count
        collection_scan_counts[collection] = total_scans

        # Create columns for side-by-side plots
        col1, col2 = st.columns(2)

        # Plot individual pie chart for the collection
        if total_scans > 0:
            labels = ['Healthy', 'Infected']
            sizes = [healthy_count, infected_count]
            colors = ['#00FF00', '#FF0000']

            fig, ax = plt.subplots(figsize=(3, 3))  # Adjust plot size
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')

            with col1:
                st.write(f"**{collection} - Healthy vs Infected**")
                st.pyplot(fig)

        # Process data for line chart
        for doc in docs:
            data = doc.to_dict()
            
            if 'DeviceName' in data and 'timestamp' in data and 'InfStat' in data: 
                device_name = data['DeviceName']
                timestamp = data['timestamp']
                inf_stat = data['InfStat']

                # Aggregate data by device and date
                date_only = timestamp.date()
                device_data[device_name][date_only][inf_stat] += 1
            else:
                st.warning(f"Skipping document {doc.id} due to missing fields.")
                
    # Create columns for side-by-side plots
    col1, col2 = st.columns(2)

    # Plot combined pie chart for all selected collections
    if total_healthy + total_infected > 0:
        labels = ['Healthy', 'Infected']
        sizes = [total_healthy, total_infected]
        colors = ['#00FF00', '#FF0000']

        fig, ax = plt.subplots(figsize=(3, 3))  # Adjust plot size
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')

        with col1:
            st.write("**Combined Healthy vs Infected Scans Across Selected Collections**")
            st.pyplot(fig)

    # Pie chart showing data share by each collection
    if collection_scan_counts:
        total_scans_all_collections = sum(collection_scan_counts.values())

        if total_scans_all_collections > 0:
            scan_shares = [count / total_scans_all_collections * 100 for count in collection_scan_counts.values()]
            fig, ax = plt.subplots(figsize=(3, 3))  # Adjust plot size
            ax.pie(scan_shares, labels=collection_scan_counts.keys(), autopct='%1.1f%%', startangle=90)
            ax.axis('equal')

            with col2:
                st.write("**Data Share by Each Collection**")
                st.pyplot(fig)

    # Bar chart showing collections with most infected scans
    if total_infected > 0:
        sorted_collections = sorted(collection_scan_counts.items(), key=lambda item: item[1], reverse=True)
        collections = [item[0] for item in sorted_collections]
        infected_counts = [sum(1 for doc in db.collection(collection).stream() if doc.to_dict().get('InfStat') == 'Infected') for collection in collections]

        fig, ax = plt.subplots(figsize=(6, 3))  # Adjust plot size
        ax.barh(collections, infected_counts, color='#FF0000')
        ax.set_xlabel('Number of Infected Scans')
        ax.set_ylabel('Collection')
        ax.set_title('Infected Scans by Collection (Most to Least)')

        with col1:
            st.write("**Infected Scans by Collection**")
            st.pyplot(fig)

    # Line chart for device scan counts over time
    if device_data:
        fig, ax = plt.subplots(figsize=(8, 3))  # Adjust plot size
        colors = plt.cm.get_cmap('tab10', len(device_data) * 2)

        for i, (device, dates) in enumerate(device_data.items()):
            date_list = sorted(dates.keys())
            healthy_scans = [dates[date]['Healthy'] for date in date_list]
            infected_scans = [dates[date]['Infected'] for date in date_list]

            ax.plot(date_list, healthy_scans, label=f"{device} - Healthy", color=colors(i * 2))
            ax.plot(date_list, infected_scans, label=f"{device} - Infected", color=colors(i * 2 + 1))

        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Scans')
        ax.set_title('Device Scan Counts Over Time')
        ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%
