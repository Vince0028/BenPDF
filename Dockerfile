# Stage 1: Build Environment - Install Python dependencies first
# Using a specific Python base image for better reliability and smaller size
FROM python:3.11-slim-buster AS build-env

# Set working directory inside the container
WORKDIR /app

# Install build dependencies for Python packages (if any native extensions)
# and for LibreOffice (even if installed in a later stage, some system tools might be needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir to save space
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production Environment - Install LibreOffice and copy app
# Use a fresh, clean base image for the final app
FROM ubuntu:22.04

# Set environment variables for non-interactive apt-get and for LibreOffice path
ENV DEBIAN_FRONTEND=noninteractive
ENV LIBREOFFICE_PATH=/usr/bin/libreoffice

# Install LibreOffice and other necessary system packages
# - libreoffice: The main LibreOffice suite
# - fontconfig: For font rendering, often required by LibreOffice
# - libxrender1, libfontconfig1: Common display-related dependencies
# - unzip, wget: Often useful utilities, though not strictly required for conversion itself
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fontconfig \
    libxrender1 \
    libfontconfig1 \
    unzip \
    wget \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy Python and installed dependencies from the build-env stage
# This ensures we get the exact Python version and libraries installed previously
COPY --from=build-env /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build-env /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=build-env /usr/local/bin/pip /usr/local/bin/pip
# Ensure Python 3.11 is explicitly used
ENV PATH="/usr/local/bin:${PATH}"

# Set working directory for the application
WORKDIR /app

# Copy the rest of your application code
COPY . .

# Create ephemeral directories for uploads and converted files
# It's good practice to declare these, but Render's /tmp is also good for temporary files
# Ensure these directories exist and are writable by the user Gunicorn runs as
RUN mkdir -p uploads converted && chmod -R 777 uploads converted

# Expose the port your Flask app (Gunicorn) will listen on
# Render typically expects port 10000
EXPOSE 10000

# Command to run your Flask application using Gunicorn
# This is the entry point when the container starts
# The first 'app' refers to app.py, the second 'app' refers to the Flask instance variable
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
