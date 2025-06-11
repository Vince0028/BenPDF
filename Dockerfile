# Stage 1: Build Environment - Install Python dependencies first
# Using a specific Python base image for better reliability and smaller size
FROM python:3.11-slim-buster AS build-env

# Set working directory inside the container
WORKDIR /app

# Install build dependencies for Python packages (if any native extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir to save space, --upgrade pip for good measure (though not strictly necessary for this error)
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Stage 2: Production Environment - Install LibreOffice and copy app
# Use a fresh, clean base image for the final app
FROM ubuntu:22.04

# Set environment variables for non-interactive apt-get and for LibreOffice path
ENV DEBIAN_FRONTEND=noninteractive
ENV LIBREOFFICE_PATH=/usr/bin/libreoffice

# Install LibreOffice and other necessary system packages
# - libreoffice: The main LibreOffice suite
# - fontconfig, libxrender1, libfontconfig1: For font rendering, often required by LibreOffice headless operation
# - unzip, wget: Common utilities
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
# We no longer explicitly copy /usr/local/bin/gunicorn or /usr/local/bin/pip
# as python -m gunicorn will find the module within site-packages.
COPY --from=build-env /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Ensure Python 3.11's bin directory is in the PATH.
# The python3.11 executable itself is typically in /usr/bin/
ENV PATH="/usr/local/bin:${PATH}"

# Set working directory for the application
WORKDIR /app

# Copy the rest of your application code
COPY . .

# Create ephemeral directories for uploads and converted files and ensure they are writable
RUN mkdir -p uploads converted && chmod -R 777 uploads converted

# Expose the port your Flask app (Gunicorn) will listen on
# Render typically expects port 10000
EXPOSE 10000

# Command to run your Flask application using Gunicorn
# Using 'python -m gunicorn' is generally more robust as it explicitly uses Python's module runner
CMD ["python3.11", "-m", "gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
