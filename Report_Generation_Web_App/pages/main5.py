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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Line
import tempfile
import base64
import plotly.io as pio
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

st.set_page_config(layout="wide")
# Redirect to login page if not authenticated
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Please log in first.")
    st.switch_page("main4.py")

st.write(f"Welcome, {st.session_state.username}!")

# Initialize Firestore
cred_path = "Report_Generation_Web_App/testdata1-20ec5-firebase-adminsdk-an9r6-d15c118c96.json"
db = firestore.Client.from_service_account_json(cred_path)
    # Your existing web app code starts here...
#st.title('Test Analysis Report')
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

# Function to preprocess radar data
def preprocess_radar_data(radar_raw):
    df_radar = pd.DataFrame(radar_raw, columns=['Radar'])
    df_radar.dropna(inplace=True)
    df_radar.fillna(df_radar.mean(), inplace=True)
    return df_radar

# Function to plot time domain radar data
def plot_time_domain(preprocessed_scan, device_name, timestamp, scan_duration, sampling_rate=100):
    #st.write("## Time Domain")
    fig = go.Figure()
    
    time_seconds = np.arange(len(preprocessed_scan)) / sampling_rate
    fig.add_trace(go.Scatter(
        x=time_seconds,
        y=preprocessed_scan['Radar'],
        mode='lines',
        name=f"{device_name} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        line=dict(color='blue')
    ))

    fig.update_layout(
        template='plotly_white',
        xaxis_title="Time (s)",
        yaxis_title="Signal",
        legend_title="Scan",
        font=dict(color="black"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=100, r=100, t=100, b=100),  # Add space for the border
        shapes=[dict(
            type='rect',
            x0=0,
            y0=0,
            x1=1,
            y1=1,
            xref='paper',
            yref='paper',
            line=dict(
                color="black",  # Border color
                width=2  # Border width
            )
        )]
    )
    # Save the figure as an image
    return fig  # Convert to an image file
    
      # Return the image file path
    #st.plotly_chart(fig)

    # Print additional metadata below the graph
    

  
def fetch_data():
    docs = query.stream()
    
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
    pdfmetrics.registerFont(TTFont('ARLRDBD', 'Report_Generation_Web_App/ARLRDBD.TTF'))
    pdfmetrics.registerFont(TTFont('ARIAL', 'Report_Generation_Web_App/ARIAL.TTF'))
    styles["Heading1"].fontName = 'ARLRDBD'
    styles["Normal"].fontName = 'ARIAL'
    
    heading_style_centered = ParagraphStyle(
        "HeadingStyleCentered", parent=styles["Heading1"], fontSize=20, textColor=colors.darkblue,
        alignment=1, spaceAfter=10, underline=True, bold=True,
    )

    heading_style_left = ParagraphStyle(
        "HeadingStyleLeft", parent=styles["Heading1"], fontSize=20, textColor=colors.darkblue,
        alignment=0, spaceAfter=10, underline=True, bold=True,  # alignment=0 for left alignment
    )

    heading_style_sub = ParagraphStyle(
        "HeadingStyleLeft", parent=styles["Heading1"], fontSize=16, textColor=colors.black,
        alignment=0, spaceAfter=10, underline=True, bold=True,  # alignment=0 for left alignment
    )
    
    body_style = styles["Normal"]
    body_style.fontSize = 12
    bold_style = ParagraphStyle("BoldStyle", parent=body_style, fontSize=12, fontName="ARLRDBD")

    
    elements = []
    elements.append(Paragraph("TERMATRAC TEST REPORT", heading_style_centered))
    elements.append(Paragraph("SUPPLEMENT TO TIMBER PEST REPORT", heading_style_centered))
    elements.append(Spacer(1, 16))
    
    desc_lines = [
        "This Trebirth test report is a supplementary report only, which MUST be read in",
        "conjunction with the full timber pest report. This report cannot be relied upon",
        "without the full timber pest report and is only a record of the test findings."
    ]
    
    for line in desc_lines:
        elements.append(Paragraph(line, body_style))
        elements.append(Spacer(1, 6))

    elements.append(Spacer(1, 20))  # Extra space before table
   
    
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
        # Table Data (Properly Aligned)
        data = [
            ["Tests were carried out by:", test_by],
            ["Date:", report_date],
            ["Report for building at:", report_loc],
            ["Report requested by:", requested_by]
        ]

        # Create the table
        table = Table(data, colWidths=[2.5 * inch, 3.5 * inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'ARIAL'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.darkblue),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        ]))

        elements.append(table)
        elements.append(PageBreak())

        area_scans = {}
        for scan in filtered_scans:
            area = scan.get("Area", "Unknown Area")
            if area not in area_scans:
                area_scans[area] = []
            area_scans[area].append(scan)
                
        
        for i, (area, scans) in enumerate(area_scans.items(), start=1):
            elements.append(Paragraph(f"{i} {area.upper()}", heading_style_left))
            
            for j, scan in enumerate(scans, start=1):
                elements.append(Paragraph(f"{i}.{j} Radar Scan", heading_style_sub))
                pest_details = scan.get("Pest details", "N/A")
                
                radar_raw = scan.get('RadarRaw', [])
                if radar_raw:
                    processed_scan = preprocess_radar_data(radar_raw)
                    device_name = scan.get('DeviceName', 'Unknown Device')
                    timestamp = scan.get('timestamp', datetime.now())
                    scan_duration = scan.get("Scan Duration", "Unknown")
                    
                    # Generate the time domain plot
                    fig = plot_time_domain(processed_scan, device_name, timestamp, scan_duration)
                
                    # Save the plot as an image
                    img_path = f"{tempfile.gettempdir()}/time_domain_plot.png"
                    pio.write_image(fig, img_path, format="png")

                    # Add the image to the PDF
                    elements.append(Image(img_path, width=400, height=300))
                    elements.append(Spacer(1, 20))  # Space after image

                    # Add additional device info below the graph
                    elements.append(Paragraph(f"Device Name: {device_name}", body_style))
                    elements.append(Spacer(1, 3))
                    elements.append(Paragraph(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}", body_style))
                    elements.append(Spacer(1, 3))
                    elements.append(Paragraph(f"Scan Duration: {scan_duration} seconds", body_style))
                    elements.append(Spacer(1, 12))
                
                    data = [
                        ["Scan Location:", filtered_scans[0].get("Scan Location", "N/A")],
                        ["Scan Date:", filtered_scans[0].get("scan_date", "Unknown Date")],
                        ["Termatrac device was:", filtered_scans[0].get("Termatrac device was", "N/A")],
                        ["Termatrac device position:", filtered_scans[0].get("Termatrac device position", "N/A")],
                        ["Damage Visible:", filtered_scans[0].get("Damage visible", "N/A")],
                    ]
                    table = Table(data, colWidths=[2.5 * inch, 3.5 * inch])
                    table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), 'ARLRDBD'),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (1, 0), (-1, -1), 'ARIAL'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))

                    elements.append(table)
                    elements.append(Spacer(1, 20))
                
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
    
    doc.build(elements)
    # Remove temporary image file after generating PDF
    os.remove(img_path)
    return pdf_path
    return
if st.button("Generate PDF Report"):
    pdf_file = generate_pdf()
    
    with open(pdf_file, "rb") as file:
        st.download_button(
            label="Download PDF",
            data=file,
            file_name="Trebirth_Termatrac_Test_Report.pdf",
            mime="application/pdf",
        )

