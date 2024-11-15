import boto3
import os
from datasets import load_dataset


ds = load_dataset("gaia-benchmark/GAIA", "2023_all")


print("Dataset Structure:", ds)

target_directories = ["test", "validation"]

s3_bucket_name = 'textextractionfrompdf'
s3_base_path = 'GAIA-Dataset/'

s3_client = boto3.client('s3')

def upload_pdf_files_to_s3(dataset, directories, bucket_name, base_path):
    for directory in directories:
        print(f"Processing directory: {directory}")
        
        if directory not in dataset:
            print(f"Directory {directory} not found in the dataset. Skipping...")
            continue

        for file in dataset[directory]:
            file_name = file['file_name']
            file_path = file['file_path']

            if file_name.lower().endswith(".pdf"):

                s3_file_path = os.path.join(base_path, directory, file_name)

                try:
                    s3_client.upload_file(file_path, bucket_name, s3_file_path)
                    print(f"Uploaded {file_name} to s3://{bucket_name}/{s3_file_path}")
                except FileNotFoundError:
                    print(f"File {file_path} not found. Skipping...")
            else:
                print(f"Skipping non-PDF file: {file_name}")

upload_pdf_files_to_s3(ds, target_directories, s3_bucket_name, s3_base_path)