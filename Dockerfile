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

# Copy only the requirements file (this will be used in Stage 2 as well)
COPY requirements.txt .

# No need to install pip dependencies in build-env anymore as they will be installed in stage 2
# RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Stage 2: Production Environment - Install LibreOffice, Python, and then Python dependencies
# Use a fresh, clean base image for the final app
FROM ubuntu:22.04

# Set environment variables for non-interactive apt-get and for LibreOffice path
ENV DEBIAN_FRONTEND=noninteractive
ENV LIBREOFFICE_PATH=/usr/bin/libreoffice

# Install LibreOffice and other necessary system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fontconfig \
    libxrender1 \
    libfontconfig1 \
    unzip \
    wget \
    # Explicitly install python3.11 and its venv module in the final stage
    # This ensures python3.11 executable is available in the final image
    python3.11 \
    python3.11-venv \
    # Symlink python3 to python3.11 for broader compatibility
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for the application
WORKDIR /app

# Create a virtual environment and activate it
RUN python3.11 -m venv .venv
ENV PATH="/app/.venv/bin:${PATH}"

# Copy requirements.txt from the build-env stage to the final stage
COPY --from=build-env /app/requirements.txt .

# Install Python dependencies into the newly created virtual environment
# Ensure pip is upgraded within this venv before installing packages
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Create ephemeral directories for uploads and converted files and ensure they are writable
RUN mkdir -p uploads converted && chmod -R 777 uploads converted

# Expose the port your Flask app (Gunicorn) will listen on
# Render typically expects port 10000
EXPOSE 10000

# Command to run your Flask application using Gunicorn
# Using 'python3.11 -m gunicorn' is robust as it explicitly calls Python 3.11
# and finds the gunicorn module within the site-packages of the active venv.
CMD ["python3.11", "-m", "gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
