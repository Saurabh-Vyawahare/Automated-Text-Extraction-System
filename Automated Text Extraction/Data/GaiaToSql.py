import boto3
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()

# S3 and Database configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
GAIA_TEST_CSV_PATH = os.getenv('GAIA_TEST_CSV_PATH')
GAIA_VALIDATION_CSV_PATH = os.getenv('GAIA_VALIDATION_CSV_PATH')
AWS_REGION = os.getenv('AWS_REGION')

# RDS configuration
RDS_HOST = os.getenv('DB_HOST')
RDS_PORT = os.getenv('DB_PORT')
RDS_DATABASE = os.getenv('DB_NAME')
RDS_USER = os.getenv('DB_USER')
RDS_PASSWORD = os.getenv('DB_PASSWORD')

# AWS Credentials
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# S3 Client with the provided credentials
s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# Function to fetch PDF file names from the S3 bucket
def get_s3_filenames(bucket_name):
    """Fetch the list of PDF file names from the S3 bucket."""
    file_names = []
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.pdf'):  # Include only PDF files
                    file_names.append(obj['Key'].split("/")[-1])  # Only get file name
        print(f"Files in S3 bucket: {file_names}")
    except s3_client.exceptions.NoSuchBucket:
        print(f"Bucket {bucket_name} does not exist.")
    except s3_client.exceptions.ClientError as e:
        print(f"Error fetching S3 filenames: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return file_names

# Function to load GAIA dataset and match with S3 filenames
def match_filenames_with_gaia(s3_filenames, gaia_dataset_csv):
    """Load GAIA dataset, and match file names with the file_name column in the dataset."""
    try:
        gaia_df = pd.read_csv(gaia_dataset_csv)
        print(f"GAIA dataset loaded from {gaia_dataset_csv}.")
        
        # Check if the file_name column exists
        if 'file_name' not in gaia_df.columns:
            raise KeyError("The 'file_name' column is not present in the GAIA dataset.")
        
        # Filter rows that have matching filenames
        matched_files_df = gaia_df[gaia_df['file_name'].isin(s3_filenames)]
        print(f"Filtered GAIA Dataset: {len(matched_files_df)} rows matched.")
        return matched_files_df
    except FileNotFoundError:
        print(f"File not found: {gaia_dataset_csv}")
    except Exception as e:
        print(f"Error processing GAIA dataset: {e}")

import pymysql

def save_to_rds(matched_df, rds_host, rds_port, rds_db, rds_user, rds_password):
    """Save the matched DataFrame to the RDS SQL table."""
    try:
        # Create the RDS connection string for MySQL using SQLAlchemy and pymysql
        rds_connection_str = f"mysql+pymysql://{rds_user}:{rds_password}@{rds_host}:{rds_port}/{rds_db}"

        # Create the SQLAlchemy engine
        engine = create_engine(rds_connection_str)

        # Print connection string for verification
        print(f"RDS Connection String: {rds_connection_str}")

        # Write the DataFrame to a SQL table named 'matched_files'
        matched_df.to_sql('matched_files', con=engine, if_exists='replace', index=False)

        print("Data successfully saved to RDS!")
    except Exception as e:
        print(f"Error saving data to RDS: {e}")

def main():
    # Get the list of PDF files from the S3 bucket
    s3_filenames = get_s3_filenames(S3_BUCKET_NAME)

    # Match S3 file names with GAIA test dataset
    matched_test_df = match_filenames_with_gaia(s3_filenames, GAIA_TEST_CSV_PATH)

    # Save matched data to RDS if there are matches
    if matched_test_df is not None and not matched_test_df.empty:
        save_to_rds(matched_test_df, RDS_HOST, RDS_PORT, RDS_DATABASE, RDS_USER, RDS_PASSWORD)
    else:
        print("No matching files found in the GAIA test dataset.")

    # Match S3 file names with GAIA validation dataset
    matched_validation_df = match_filenames_with_gaia(s3_filenames, GAIA_VALIDATION_CSV_PATH)

    # Save matched data to RDS if there are matches
    if matched_validation_df is not None and not matched_validation_df.empty:
        save_to_rds(matched_validation_df, RDS_HOST, RDS_PORT, RDS_DATABASE, RDS_USER, RDS_PASSWORD)
    else:
        print("No matching files found in the GAIA validation dataset.")

if __name__ == "__main__":
    main()