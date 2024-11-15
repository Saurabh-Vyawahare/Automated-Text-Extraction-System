import streamlit as st
import requests
from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import Error
from generate_summary import generate_summary  # Updated import for the renamed `generate_summary` file
from generate_response import ask_chatgpt  # Import the ask_chatgpt function

# Load environment variables
load_dotenv()

# FastAPI endpoint URLs for user login and PDF list retrieval
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")
REGISTER_URL = f"{FASTAPI_URL}/auth/register"
LOGIN_URL = f"{FASTAPI_URL}/auth/login"
PDF_LIST_URL = f"{FASTAPI_URL}/files/list-pdfs"

# RDS Database Configuration loaded from .env file
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Set up Streamlit page configuration
st.set_page_config(page_title="PDF Text Extraction Application", layout="centered")

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'access_token' not in st.session_state:
    st.session_state['access_token'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'
if 'pdf_files' not in st.session_state:
    st.session_state['pdf_files'] = []
    st.session_state['files_loaded'] = False
if 'selected_pdf' not in st.session_state:
    st.session_state['selected_pdf'] = None
if 'selected_extractor' not in st.session_state:
    st.session_state['selected_extractor'] = None
if 'pdf_question' not in st.session_state:
    st.session_state['pdf_question'] = None
if 'summary_result' not in st.session_state:
    st.session_state['summary_result'] = None
if 'response_result' not in st.session_state:
    st.session_state['response_result'] = None

# Function to connect to the RDS MySQL database
def create_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        return None

# Signup function to create new users
def signup(username, email, password):
    response = requests.post(REGISTER_URL, json={
        "username": username,
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        st.success("Account created successfully! Please login now.")
    else:
        st.error(response.json().get("detail", "An error occurred during signup."))

# Login function to authenticate existing users
def login(username, password):
    response = requests.post(LOGIN_URL, json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        token_data = response.json()
        st.session_state['access_token'] = token_data['access_token']
        st.session_state['logged_in'] = True
        st.session_state['page'] = 'application'
        st.success("Logged in successfully!")
    else:
        st.error("Invalid username or password. Please try again.")

# Fetch the list of PDFs from the FastAPI endpoint
def get_pdf_list():
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    try:
        response = requests.get(PDF_LIST_URL, headers=headers)
        if response.status_code == 200:
            pdf_files = response.json().get("pdf_files", [])
            return pdf_files
        else:
            st.error(f"Failed to fetch PDF list from FastAPI. Status code: {response.status_code}.")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to FastAPI: {e}")
        return []

# Fetch the question associated with the selected PDF from RDS database
def get_pdf_question_from_db(pdf_filename):
    connection = create_db_connection()
    if connection is None:
        return "Database connection failed."
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT Question FROM merged_pdf WHERE file_name = %s"
        cursor.execute(query, (pdf_filename,))
        result = cursor.fetchone()
        return result['Question'] if result else "No question found for this PDF."
    except Error as e:
        st.error(f"Error fetching question from database: {e}")
        return "Error fetching question from database."
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Main Interface: Login/Signup or Application depending on state
if st.session_state['logged_in']:
    st.title("PDF Text Extraction Application")

    # Fetch PDF files only if they haven't been loaded already
    if not st.session_state['files_loaded']:
        st.session_state['pdf_files'] = get_pdf_list()
        st.session_state['files_loaded'] = True

    # Check if PDF files were successfully retrieved
    if not st.session_state['pdf_files']:
        st.warning("No PDF files found in the specified S3 bucket.")
        st.stop()

    # Define dropdowns and their session state handling
    def on_pdf_select():
        st.session_state['selected_pdf'] = st.session_state['pdf_dropdown']
        pdf_filename = st.session_state['selected_pdf'].split('/')[-1]  # Get just the file name
        st.session_state['pdf_question'] = get_pdf_question_from_db(pdf_filename)

    def on_extractor_select():
        st.session_state['selected_extractor'] = st.session_state['extractor_dropdown']

    # Dropdown for selecting a PDF file
    st.selectbox(
        "Select a PDF file:", 
        st.session_state['pdf_files'], 
        help="Choose the PDF file you want to process.",
        key="pdf_dropdown",
        index=0 if st.session_state['selected_pdf'] is None else st.session_state['pdf_files'].index(st.session_state['selected_pdf']),
        on_change=on_pdf_select
    )

    # Display the associated question after PDF selection
    if st.session_state['pdf_question']:
        st.write(f"**Associated Question:** {st.session_state['pdf_question']}")

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

    # Generate Summary button
    summary_button = st.button("Generate Summary")

    # Logic for Generate Summary Button
    if summary_button:
        if st.session_state['selected_pdf'] and st.session_state['selected_extractor']:
            pdf_filename = st.session_state['selected_pdf'].split('/')[-1]
            st.session_state['summary_result'] = generate_summary(pdf_filename, st.session_state['selected_extractor'])
            st.success("Summary generated successfully!")
        else:
            st.warning("Please select both a PDF file and an extractor method before generating a summary.")

    # Display the summary result if available
    if st.session_state['summary_result']:
        st.write("**Summary Result:**")
        st.write(st.session_state['summary_result'])

    # Text area for inputting a question (optional)
    select_question = st.text_area("Enter your question here (Optional):")

    # Button to trigger response generation
    generate_response = st.button("Generate Response")

    if generate_response:
        if st.session_state['summary_result'] and select_question:
            st.session_state['response_result'] = ask_chatgpt(st.session_state['summary_result'], select_question)
            st.write("**ChatGPT's Answer:**")
            st.write(st.session_state['response_result'])
        else:
            st.warning("Please generate a summary and enter a question before generating a response.")

else:
    option = st.selectbox("Select Login or Signup", ("Login", "Signup"))

    if option == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login(username, password)

    elif option == "Signup":
        st.subheader("Signup")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Signup"):
            signup(username, email, password)
