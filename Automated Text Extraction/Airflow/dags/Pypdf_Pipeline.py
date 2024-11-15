from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import boto3
import json
import pdfplumber
import pandas as pd
from io import BytesIO

# AWS S3 Configuration
s3BucketName = 'textextractionfrompdf'  # Replace with your S3 bucket name
s3InputPrefix = 'GAIA-Dataset/'         # Base folder in S3 (contains both 'test' and 'validation' subfolders)
outputPrefix = 'pypdf2_folder/'         # Output folder for extracted files in S3 (for both CSV and JSON)

# Set up AWS S3 client
s3Client = boto3.client('s3')

# Default DAG arguments
defaultArgs = {
    'owner': 'airflow',
    'start_date': datetime(2024, 10, 1),
    'retries': 1,
}

# Define the DAG
dag = DAG(
    dag_id='s3_pdf_extraction_pipeline',
    default_args=defaultArgs,
    description='A pipeline to extract data from PDF files in S3, determine format, and store in S3',
    schedule='@daily',
    catchup=False,
)


# Task 1: List and Select PDF Files from S3
def list_pdf_files_from_s3(**kwargs):
    """List PDF files from both 'test' and 'validation' subfolders in the S3 bucket."""
    pdf_files = []
    
    # List all PDF files in the 'test' and 'validation' folders under the specified prefix
    for subfolder in ['test/', 'validation/']:
        response = s3Client.list_objects_v2(Bucket=s3BucketName, Prefix=f"{s3InputPrefix}{subfolder}")
        folder_files = [content['Key'] for content in response.get('Contents', []) if content['Key'].endswith('.pdf')]
        pdf_files.extend(folder_files)

    print(f"Found {len(pdf_files)} PDF files in S3.")
    kwargs['ti'].xcom_push(key='pdf_files', value=pdf_files)


# Task 2: Analyze PDF Layout
def analyze_pdf_layout(**kwargs):
    """Analyze the layout of the PDF to determine if it contains tables or plain text."""
    pdf_files = kwargs['ti'].xcom_pull(key='pdf_files', task_ids='list_pdf_files_from_s3')
    
    for s3_file in pdf_files:
        # Read PDF file directly from S3 into memory using BytesIO
        response = s3Client.get_object(Bucket=s3BucketName, Key=s3_file)
        pdfContent = response['Body'].read()

        # Use pdfplumber to open and analyze the PDF layout
        with pdfplumber.open(BytesIO(pdfContent)) as pdf:
            for page in pdf.pages:
                tables = page.find_tables()
                if tables:
                    print(f"Detected tables in {s3_file}. Using CSV format.")
                    kwargs['ti'].xcom_push(key=s3_file, value="CSV")
                else:
                    text = page.extract_text()
                    if text:
                        print(f"Detected paragraphs in {s3_file}. Using JSON format.")
                        kwargs['ti'].xcom_push(key=s3_file, value="JSON")
                    else:
                        print(f"Defaulting to JSON format for {s3_file}.")
                        kwargs['ti'].xcom_push(key=s3_file, value="JSON")


# Task 3: Extract Text Using pdfplumber and Store in Appropriate Format
def extract_and_store_data(**kwargs):
    pdf_files = kwargs['ti'].xcom_pull(key='pdf_files', task_ids='list_pdf_files_from_s3')

    for s3_file in pdf_files:
        file_format = kwargs['ti'].xcom_pull(key=s3_file, task_ids='analyze_pdf_layout')

        # Read PDF from S3 for extraction
        response = s3Client.get_object(Bucket=s3BucketName, Key=s3_file)
        pdfContent = response['Body'].read()

        # Extract content using pdfplumber
        with pdfplumber.open(BytesIO(pdfContent)) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()

        # Store the extracted data in the chosen format
        if file_format == "CSV":
            store_as_csv(text, s3_file)
        else:
            store_as_json(text, s3_file)


def store_as_csv(text, s3_file):
    """Store extracted data in CSV format in the same output folder."""
    lines = text.splitlines()
    data = [line.split() for line in lines if len(line.split()) > 1]  # Only include lines with more than 1 word
    df = pd.DataFrame(data)
    csv_data = df.to_csv(index=False, header=False)
    csvFileName = s3_file.split('/')[-1].replace('.pdf', '.csv')
    s3Client.put_object(Bucket=s3BucketName, Key=f"{outputPrefix}{csvFileName}", Body=csv_data)


def store_as_json(text, s3_file):
    """Store extracted text in JSON format in the same output folder."""
    extracted_data = {'fileName': s3_file, 'text': text, 'metadata': {}}
    json_data = json.dumps(extracted_data, indent=4)
    jsonFileName = s3_file.split('/')[-1].replace('.pdf', '.json')
    s3Client.put_object(Bucket=s3BucketName, Key=f"{outputPrefix}{jsonFileName}", Body=json_data)


# Define Airflow Tasks
listFilesTask = PythonOperator(task_id='list_pdf_files_from_s3', python_callable=list_pdf_files_from_s3, dag=dag)
analyzeLayoutTask = PythonOperator(task_id='analyze_pdf_layout', python_callable=analyze_pdf_layout, dag=dag)
extractDataTask = PythonOperator(task_id='extract_and_store_data', python_callable=extract_and_store_data, dag=dag)

# Set Task Dependencies
listFilesTask >> analyzeLayoutTask >> extractDataTask