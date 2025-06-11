# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# IMPORTANT CONSIDERATION FOR docx2pdf:
# docx2pdf typically requires LibreOffice or Microsoft Office to be installed
# This is a major hurdle in a basic Dockerfile.
# A simple 'pip install docx2pdf' is NOT enough for it to work.
# If you primarily convert DOCX/DOC, you will likely need to:
# 1. Use a base image that includes LibreOffice (e.g., 'ubuntu:22.04' and install libreoffice-writer-nogui)
#    This makes the Docker image much larger.
# 2. Use a different library that doesn't rely on external software.
#
# If you choose to try with LibreOffice:
# UNCOMMENT THE FOLLOWING LINES IF YOU NEED LIBREOFFICE FOR DOCX2PDF
# This will significantly increase your image size and build time.
# Also, change the base image to 'ubuntu:22.04' or similar.
# FROM ubuntu:22.04
# RUN apt-get update && apt-get install -y libreoffice-writer-nogui default-jre \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*

# Expose the port your Flask app will run on
# Render typically handles port mapping, but it's good practice to declare
EXPOSE 8000

# Define environment variable for Flask
# Render will use these and you should also set FLASK_SECRET_KEY in Render dashboard
ENV FLASK_APP=app.py

# Command to run the application using Gunicorn (recommended for production)
# Install gunicorn: pip install gunicorn
# Make sure gunicorn is in your requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
