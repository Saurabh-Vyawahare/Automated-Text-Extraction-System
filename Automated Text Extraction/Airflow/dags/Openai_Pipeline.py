from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import boto3
import openai
import json
import pdfplumber
import pandas as pd
from io import BytesIO
import os

# AWS S3 Configuration
s3BucketName = 'textextractionfrompdf'
s3InputPrefix = 'GAIA-Dataset/'
outputPrefix = 'openai_extracts/'  # Output folder for extracted files in S3

# Set up AWS S3 client
s3Client = boto3.client('s3')

# Set OpenAI API key (ensure the key is stored securely)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Default DAG arguments
defaultArgs = {
    'owner': 'airflow',
    'start_date': datetime(2024, 10, 1),
    'retries': 1,
}

# Define the DAG
dag = DAG(
    dag_id='s3_openai_extraction_pipeline',
    default_args=defaultArgs,
    description='A pipeline to extract data from PDF files using pdfplumber and OpenAI API',
    schedule='@daily',
    catchup=False,
)


# Task 1: List and Select PDF Files from S3
def list_pdf_files_from_s3(**kwargs):
    """List PDF files from both 'test' and 'validation' subfolders in the S3 bucket."""
    pdf_files = []
    for subfolder in ['test/', 'validation/']:
        response = s3Client.list_objects_v2(Bucket=s3BucketName, Prefix=f"{s3InputPrefix}{subfolder}")
        folder_files = [content['Key'] for content in response.get('Contents', []) if content['Key'].endswith('.pdf')]
        pdf_files.extend(folder_files)

    print(f"Found {len(pdf_files)} PDF files in S3.")
    kwargs['ti'].xcom_push(key='pdf_files', value=pdf_files)


# Task 2: Extract Text and Table Data using pdfplumber
def extract_data_with_pdfplumber(**kwargs):
    """Extract text and table data from the PDF using pdfplumber and send text to OpenAI for further extraction."""
    pdf_files = kwargs['ti'].xcom_pull(key='pdf_files', task_ids='list_pdf_files_from_s3')

    for s3_file in pdf_files:
        # Read PDF file directly from S3 into memory using BytesIO
        response = s3Client.get_object(Bucket=s3BucketName, Key=s3_file)
        pdf_content = response['Body'].read()

        # To store cumulative text and table data
        cumulative_text = ""
        all_tables = []

        # Open the PDF with pdfplumber
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Check if the page contains tables
                tables = page.extract_tables()
                if tables and len(tables) > 0:
                    for i, table in enumerate(tables):
                        # Extract tables and append to the list
                        df = pd.DataFrame(table[1:], columns=table[0])
                        df['page_num'] = page_num  # Track the page number in the CSV
                        all_tables.append(df)
                else:
                    # Extract text and accumulate for OpenAI structured extraction
                    text = page.extract_text()
                    if text:
                        cumulative_text += f"\nPage {page_num}:\n{text}\n"

        # After processing all pages, save cumulative data
        if all_tables:
            # Concatenate all tables into one DataFrame and save as a single CSV
            save_combined_table_as_csv(all_tables, s3_file)

        if cumulative_text:
            # Save accumulated text into a single TXT file
            save_combined_text_as_txt(cumulative_text, s3_file)

def save_combined_table_as_csv(df_list, s3_file):
    """Save all extracted table data for the entire PDF as a single CSV file in S3."""
    # Ensure that all dataframes have unique indices and non-conflicting columns before concatenation
    cleaned_dfs = []
    
    for df in df_list:
        # Reset index to ensure no duplicate index issues
        df = df.reset_index(drop=True)
        
        # Rename columns to avoid potential duplicate names by adding a prefix with the dataframe index
        df.columns = [f"{i}_{col}" if col in df.columns[df.columns.duplicated()] else col for i, col in enumerate(df.columns)]
        
        # Collect cleaned dataframe
        cleaned_dfs.append(df)

    # Concatenate the cleaned dataframes into a single DataFrame
    full_table_df = pd.concat(cleaned_dfs, ignore_index=True)

    # Save concatenated table data as a single CSV
    csv_data = full_table_df.to_csv(index=False, header=True)
    csvFileName = s3_file.split('/')[-1].replace('.pdf', '_tables_combined.csv')
    s3Client.put_object(Bucket=s3BucketName, Key=f"{outputPrefix}{csvFileName}", Body=csv_data)
    print(f"All tables for file {s3_file} saved as a single CSV.")


# Save entire PDF text as a single TXT file
def save_combined_text_as_txt(text, s3_file):
    """Save all extracted text for the entire PDF as a single TXT file in S3."""
    txtFileName = s3_file.split('/')[-1].replace('.pdf', '_text_combined.txt')
    s3Client.put_object(Bucket=s3BucketName, Key=f"{outputPrefix}{txtFileName}", Body=text.encode('utf-8'))
    print(f"All text for file {s3_file} saved as a single TXT file.")


# Define Airflow Tasks
listFilesTask = PythonOperator(task_id='list_pdf_files_from_s3', python_callable=list_pdf_files_from_s3, dag=dag)
extractDataTask = PythonOperator(task_id='extract_data_with_pdfplumber', python_callable=extract_data_with_pdfplumber, dag=dag)

# Set Task Dependencies
listFilesTask >> extractDataTask