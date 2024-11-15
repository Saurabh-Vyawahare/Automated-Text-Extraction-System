# pdf_routes.py
from fastapi import APIRouter, HTTPException
import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_TEST_PREFIX = os.getenv('S3_TEST_PREFIX')
S3_VALIDATION_PREFIX = os.getenv('S3_VALIDATION_PREFIX')


# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

# Create the PDF router
pdf_router = APIRouter()  # <-- You need to define `pdf_router` here

# Route to list all PDF files from the specified prefixes
@pdf_router.get("/list-pdfs")
def list_pdfs():
    try:
        if not S3_BUCKET_NAME:
            raise HTTPException(status_code=400, detail="S3_BUCKET_NAME is missing or not configured.")

        pdf_files = []
        # Loop through both prefixes: test and validation
        for prefix in [S3_TEST_PREFIX, S3_VALIDATION_PREFIX]:
            if not prefix:
                print(f"Skipping empty prefix: {prefix}")
                continue
            
            # Print the prefix being used for debugging
            print(f"Listing objects in S3 bucket '{S3_BUCKET_NAME}' with prefix '{prefix}'")

            response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)

            # Print the raw S3 response for debugging
            print("S3 Response:", response)

            if 'Contents' in response:
                folder_files = [item['Key'] for item in response['Contents'] if item['Key'].endswith('.pdf')]
                pdf_files.extend(folder_files)

        return {"pdf_files": pdf_files}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))