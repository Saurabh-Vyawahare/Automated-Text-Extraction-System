# Automated Text Extraction System - README

[Deployment link](https://18.188.86.27:8080)

[Video link](https://drive.google.com/drive/folders/1VozeLR1GTBusVJXih_fo1F7lMnY-L-HG?usp=drive_link)

[CodeLabs](https://codelabs-preview.appspot.com/?file_id=1-5QP7m-QK3vR2Jtv8-lNfvdp06IYvoHcKmNlVWzhRqU#0)

Authors:

	•	Aniket Patole
	•	Saurabh Vyawahare
	•	Shreya Bage

Introduction

This project automates the extraction of text from PDF documents and provides a user-friendly interface for querying the extracted data. By integrating modern cloud technologies, including Airflow, FastAPI, Streamlit, AWS S3, and Docker, the system streamlines the entire process of handling document-based information.

The application demonstrates how cloud-native tools can simplify the extraction and querying of textual content from large volumes of PDF documents, making it scalable, efficient, and easy to use, especially for non-technical users.

Technologies Used:

	1.	Airflow - Orchestrates the text extraction pipeline and automates workflows.
	2.	FastAPI - Backend API service that manages user authentication, file uploads, and query processing.
	3.	Streamlit - Provides an intuitive and interactive frontend for users to upload PDFs and query extracted data.
	4.	AWS S3 / SQL Database - For scalable data storage of extracted text.
	5.	Docker - Containerizes the application to ensure portability and ease of deployment.

Project Goal:

The primary objective is to create an end-to-end automated system that:

	•	Extracts text from PDF files.
	•	Stores the extracted data securely.
	•	Allows users to query and interact with the data through a simple web interface.

Expanded Technologies Overview:

	•	Airflow: Automates the text extraction workflow from PDF files using PyPDF or AWS Textract.
	•	FastAPI: Manages secure user authentication and handles file upload and query requests. Uses JWT tokens for securing access.
	•	Streamlit: Acts as the user-facing frontend where users can upload PDFs, view extracted text, and submit queries.
	•	AWS S3 / SQL Database: AWS S3 stores extracted text, while a SQL database stores metadata like user credentials.
	•	Docker: Ensures the application is consistent and easy to deploy across different environments.

Problem Statement:

Manually extracting information from PDFs is time-consuming and prone to errors. This project addresses the challenge of automating the process of text extraction and querying from large volumes of PDF files, making it more efficient, scalable, and user-friendly.

Expected Outcomes:

	1.	Automated Text Extraction: A pipeline capable of extracting text from PDFs without manual intervention.
	2.	User-Friendly Query Interface: A web interface for uploading PDFs, viewing extracted text, and querying information via natural language.
	3.	Cloud Integration: Scalable storage using AWS S3 for handling large datasets.
	4.	Secure Deployment: Containerized services (Airflow, FastAPI, Streamlit) using Docker for easy deployment and scaling.

Constraints and Limitations:

	•	The system relies on Docker for containerization, which may present challenges if Docker is not set up properly.
	•	AWS S3 integration is essential for large-scale storage, and improper configuration may lead to failures.
	•	Processing large PDFs may take additional time.
	•	The OpenAI API has limits in query understanding, especially for complex documents.

Architecture Overview:

The system comprises:

	1.	Frontend (Streamlit): Allows users to upload PDFs, query extracted text, and view the results.
	2.	Backend (FastAPI): Manages user authentication, file handling, and integration with the Airflow pipeline and OpenAI API.
	3.	Airflow: Automates the extraction process and ensures efficient execution of tasks.
	4.	AWS S3 / SQL Database: Provides scalable storage for extracted text and user data.
	5.	OpenAI: Processes user queries and provides AI-based responses from the extracted text.

Project Workflow:

	1.	User Authentication: Users log in or sign up via Streamlit, with FastAPI managing JWT-based authentication.
	2.	File Upload: Users upload PDFs through Streamlit, which are passed to FastAPI and processed by the Airflow pipeline.
	3.	Text Extraction: Airflow extracts text using PyPDF or AWS Textract and stores it in AWS S3 or a SQL database.
	4.	Querying: Users submit queries to FastAPI, which processes them via the OpenAI API and returns the results.
	5.	Download: Users can view or download the extracted text from the Streamlit interface.

Challenges and Solutions:

	•	Docker Configuration: Managing multiple containers (Airflow, FastAPI, Streamlit) using Docker Compose.
	•	JWT-based Authentication: Ensuring only authenticated users can interact with the backend.
	•	Handling Large PDFs: Airflow’s distributed architecture ensures that large PDFs are processed without overloading the system.

Initial Setup:

	1.	FastAPI Setup: FastAPI handles user authentication, file uploads, and querying.
	2.	Airflow Pipeline: Configured with DAGs to automate the PDF text extraction process.
	3.	Docker Containerization: Docker Compose is used to containerize all components, ensuring consistent environments and easy scaling.

How to Deploy the Application:

	1.	Clone the Repository:

git clone https://github.com/your-repo-url.git
cd Automated-Text-Extraction


	2.	Create Docker Images:
Build and create the Docker images using:

docker-compose build


	3.	Start the Services:
Use Docker Compose to start the services:

docker-compose up -d


	4.	Access the Application:
	•	Streamlit Frontend: Go to http://localhost:8501 to access the frontend.
	•	FastAPI API Documentation: Visit http://localhost:8000/docs to access FastAPI’s Swagger documentation.
	•	Airflow Dashboard: Access the Airflow interface at http://localhost:8080.

References:

	•	FastAPI Documentation
	•	Streamlit Documentation
	•	Airflow Documentation
	•	OpenAI API Documentation
	•	AWS S3 Documentation
	•	JWT Authentication Guide

This project provides an efficient solution for automated text extraction from PDFs and querying the extracted data using cloud-native technologies, making it scalable and easy to deploy for various use cases.
