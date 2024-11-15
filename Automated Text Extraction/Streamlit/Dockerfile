# Streamlit Dockerfile
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app files into the container
COPY . .

# Add execute permissions for entrypoint.sh if present
RUN chmod +x entrypoint.sh

# Expose the default Streamlit port
EXPOSE 8501

# Run the Streamlit application using entrypoint.sh script
ENTRYPOINT ["./entrypoint.sh"]

# Command to run Streamlit application
CMD ["streamlit", "run", "application.py", "--server.port=8501", "--server.address=0.0.0.0"]