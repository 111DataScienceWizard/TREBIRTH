import streamlit as st
from google.cloud import firestore
import pandas as pd
from google.cloud.firestore import FieldFilter
from io import BytesIO
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import time
import zipfile
import os
import pytz
import random
from scipy import signal
from scipy.stats import skew, kurtosis
from collections import defaultdict
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go
from google.api_core.exceptions import ResourceExhausted, RetryError
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Line
import tempfile
from reportlab.lib.units import inch



st.set_page_config(layout="wide")
st.title('Test Analysis Report')
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def exponential_backoff(retries):
    base_delay = 1
    max_delay = 60
    delay = base_delay * (2 ** retries) + random.uniform(0, 1)
    return min(delay, max_delay)

def get_firestore_data(query):
    retries = 0
    max_retries = 10
    while retries < max_retries:
        try:
            results = query.stream()
            return list(results)
        except ResourceExhausted as e:
            st.warning(f"Quota exceeded, retrying... (attempt {retries + 1})")
            time.sleep(exponential_backoff(retries))
            retries += 1
        except RetryError as e:
            st.warning(f"Retry error: {e}, retrying... (attempt {retries + 1})")
            time.sleep(exponential_backoff(retries))
            retries += 1
        except Exception as e:
            st.error(f"An error occurred: {e}")
            break
    raise Exception("Max retries exceeded")

db = firestore.Client.from_service_account_json("WEBB_APP_TREBIRTH/testdata1-20ec5-firebase-adminsdk-an9r6-a87cacba1d.json")
query = db.collection('demo_db') 

def convert_to_local_time(timestamp, timezone='Asia/Kolkata'):
    local_tz = pytz.timezone(timezone)
    # Convert to UTC and then localize to the given timezone
    return timestamp.astimezone(local_tz)
    
def fetch_data():
    collection_ref = query
    docs = collection_ref.stream()
    
    locations = set()
    companies = set()
    scans_data = []
    
    for doc in docs:
        data = doc.to_dict()
        if "Report Location" in data and "Tests were carried out by" in data:
            locations.add(data["Report Location"].strip())
            companies.add(data["Tests were carried out by"].strip())
            
            # Extracting date from timestamp
            timestamp = data.get("timestamp")
            scan_date = datetime.utcfromtimestamp(timestamp.timestamp()).strftime('%Y-%m-%d') if timestamp else "Unknown Date"
            
            data["scan_date"] = scan_date  # Add extracted date to data
            scans_data.append(data)
    
    return sorted(locations), sorted(companies), scans_data

locations, companies, scans_data = fetch_data()

st.title("Scan Report Viewer")

selected_locations = st.multiselect("Select Report Location:", locations)
selected_companies = st.multiselect("Select Company:", companies)

def generate_pdf():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_path = tmpfile.name
    
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()

    # Apply Times New Roman font
    styles["Heading1"].fontName = 'Times-Roman'
    styles["Normal"].fontName = 'Times-Roman'
    
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading1"], fontSize=20, textColor=colors.blue,
        alignment=1, spaceAfter=10, underline=True, bold=True,
    )
    body_style = styles["Normal"]
    body_style.fontSize = 12
    
    elements = []
    elements.append(Paragraph("TERMATRAC TEST REPORT", heading_style))
    elements.append(Paragraph("SUPPLEMENT TO TIMBER PEST REPORT", heading_style))
    elements.append(Spacer(1, 10))
    
    desc = """This Trebirth test report is a supplementary report only, which MUST be read in conjunction with 
    the full timber pest report. This report cannot be relied upon without the full timber pest report and is 
    only a record of the test findings."""
    elements.append(Paragraph(desc, body_style))
    elements.append(Spacer(1, 10))
    
    filtered_scans = [scan for scan in scans_data if 
        (not selected_locations or scan["Report Location"].strip() in selected_locations) and
        (not selected_companies or scan["Tests were carried out by"].strip() in selected_companies)
    ]
    
    if not filtered_scans:
        elements.append(Paragraph("No data found.", body_style))
    else:
        test_by = filtered_scans[0]["Tests were carried out by"]
        report_loc = filtered_scans[0]["Report Location"]
        requested_by = filtered_scans[0]["Report requested by"]
        report_date = filtered_scans[0]["scan_date"]
        
        # Split the general information into multiple lines and add a Spacer after each line
        general_info = [
            f"Tests were carried out by: {test_by}",
            f"Date: {report_date}",
            f"Report for building at: {report_loc}",
            f"Report requested by: {requested_by}"
        ]
        
        for info in general_info:
            elements.append(Paragraph(info, body_style))
            elements.append(Spacer(1, 12))  # Leave space between lines

        # Page Break and continuing content for further pages
        elements.append(PageBreak())
        
        area_scans = {}
        for scan in filtered_scans:
            area = scan.get("Area", "Unknown Area")
            if area not in area_scans:
                area_scans[area] = []
            area_scans[area].append(scan)
                
        # Loop over the areas and scans and add them to the document
        page_num = 1
        total_pages = len(area_scans)  # Calculate the total number of pages
        for i, (area, scans) in enumerate(area_scans.items(), start=1):
            elements.append(Paragraph(f"{i} {area.upper()}", heading_style))
            
            for j, scan in enumerate(scans, start=1):
                pest_details = scan.get("Pest details", "N/A")
                scan_location = scan.get("Scan Location", "N/A")
                termatrac_status = scan.get("Termatrac device was", "N/A")
                termatrac_position = scan.get("Termatrac device position", "N/A")
                damage_visible = scan.get("Damage visible", "N/A")
                scan_date = scan.get("scan_date", "Unknown Date")
                
                scan_info = f"""<b>{i}.{j} Radar Scan</b> <br/>
                {pest_details} <br/>
                Scan Location: {scan_location} <br/>
                Scan Date: {scan_date} <br/>
                Termatrac device was: {termatrac_status} <br/>
                Termatrac device position: {termatrac_position} <br/>
                Damage Visible: {damage_visible}"""
                
                elements.append(Paragraph(scan_info, body_style))
                elements.append(Spacer(1, 10))
                
                if j % 3 == 0:
                    page_num += 1
                    elements.append(Spacer(1, 10))  # Leave space before page number
                    # Add a line before the page number
                    elements.append(Line(50, 80, 550, 80))  # X1, Y1, X2, Y2 for line
                    # Add page number to the bottom left
                    elements.append(Paragraph(f"pg.no: {page_num}/{total_pages}", body_style))
                    elements.append(Spacer(1, 10))
                    elements.append(PageBreak())  # Start a new page for the next set of scans
    
    # Final page line and page number
    elements.append(Spacer(1, 10))  # Leave space before the line
    elements.append(Paragraph(f"pg.no: {page_num}/{total_pages}", body_style))
    
    doc.build(elements)
    return pdf_path

if st.button("Generate PDF Report"):
    pdf_file = generate_pdf()
    
    with open(pdf_file, "rb") as file:
        st.download_button(
            label="Download PDF",
            data=file,
            file_name="Trebirth_Termatrac_Test_Report.pdf",
            mime="application/pdf",
        )

