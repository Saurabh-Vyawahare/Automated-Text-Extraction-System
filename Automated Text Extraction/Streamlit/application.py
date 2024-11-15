import streamlit as st
import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up Streamlit page configuration and title
st.set_page_config(page_title="PDF Text Extraction Application", layout="centered")
st.title("PDF Text Extraction Application")

# Base URL for FastAPI
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")
PDF_LIST_ENDPOINT = f"{FASTAPI_URL}/files/list-pdfs"

# Check if the user is logged in and JWT token is present
if 'access_token' not in st.session_state or not st.session_state['access_token']:
    st.warning("You need to login first. Please return to the main page and login.")
    st.stop()

# Initialize session state variables
if 'selected_pdf' not in st.session_state:
    st.session_state['selected_pdf'] = None
if 'selected_extractor' not in st.session_state:
    st.session_state['selected_extractor'] = None
if 'pdf_files' not in st.session_state:
    st.session_state['pdf_files'] = []
    st.session_state['files_loaded'] = False  # Track if files are loaded

# Function to fetch PDF files from the FastAPI endpoint
def get_pdf_list():
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = requests.get(PDF_LIST_ENDPOINT, headers=headers)
        if response.status_code == 200:
            pdf_files = response.json().get("pdf_files", [])
            return pdf_files
        else:
            st.error(f"Failed to fetch PDF list from FastAPI. Status code: {response.status_code}.")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to FastAPI: {e}")
        return []

# Fetch PDF files only if they haven't been loaded already
if not st.session_state['files_loaded']:
    st.session_state['pdf_files'] = get_pdf_list()
    st.session_state['files_loaded'] = True

# Check if PDF files were successfully retrieved
if not st.session_state['pdf_files']:
    st.warning("No PDF files found in the specified S3 bucket.")
    st.stop()

# Define callbacks to update session state based on dropdown selections
def on_pdf_select():
    st.session_state['selected_pdf'] = st.session_state['pdf_dropdown']
    st.write(f"PDF Selected: {st.session_state['selected_pdf']}")

def on_extractor_select():
    st.session_state['selected_extractor'] = st.session_state['extractor_dropdown']
    st.write(f"Extractor Selected: {st.session_state['selected_extractor']}")

# Dropdown for selecting a PDF file
st.selectbox(
    "Select a PDF file:", 
    st.session_state['pdf_files'], 
    help="Choose the PDF file you want to process.",
    key="pdf_dropdown",
    index=0 if st.session_state['selected_pdf'] is None else st.session_state['pdf_files'].index(st.session_state['selected_pdf']),
    on_change=on_pdf_select  # Call this function whenever the selection changes
)

# Dropdown for selecting an extractor method
extractor_options = ["OpenAI", "PyPDF"]
st.selectbox(
    "Select an Extractor:", 
    extractor_options, 
    help="Choose the extraction method to use.",
    key="extractor_dropdown",
    index=0 if st.session_state['selected_extractor'] is None else extractor_options.index(st.session_state['selected_extractor']),
    on_change=on_extractor_select
)

# Debugging outputs
st.write(f"You selected PDF: {st.session_state['selected_pdf']}")
st.write(f"You selected Extractor: {st.session_state['selected_extractor']}")

# Text area for inputting a question
select_question = st.text_area("Enter your question here (Optional):")

# Buttons to trigger actions
summary_button = st.button("Generate Summary")
generate_response = st.button("Generate Response")

# Logic for Generate Summary Button
if summary_button:
    if st.session_state['selected_pdf'] and st.session_state['selected_extractor']:
        st.success(f"Generating summary for {st.session_state['selected_pdf']} using {st.session_state['selected_extractor']}...")
        # Placeholder for API call to generate summary
    else:
        st.warning("Please select both a PDF file and an extractor method before generating a summary.")

# Logic for Generate Response Button
if generate_response:
    if st.session_state['selected_pdf'] and st.session_state['selected_extractor'] and select_question:
        st.success(f"Generating response for the question: '{select_question}' using {st.session_state['selected_extractor']}...")
        # Placeholder for API call to generate response
    else:
        st.warning("Please select a PDF file, an extractor method, and enter a question before generating a response.")
