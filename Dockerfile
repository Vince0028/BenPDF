# Stage 1: Build Environment - Just copy requirements.txt
FROM python:3.11-slim-buster AS build-env

# Set working directory
WORKDIR /app

# Copy only the requirements file (this will be used in Stage 2)
COPY requirements.txt .

# Stage 2: Production Environment - Install LibreOffice, Python, and all Python dependencies
FROM ubuntu:22.04

# Set environment variables for non-interactive apt-get and for LibreOffice path
ENV DEBIAN_FRONTEND=noninteractive
ENV LIBREOFFICE_PATH=/usr/bin/libreoffice

# Install LibreOffice, Python 3.11, its venv module, and other necessary system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fontconfig \
    libxrender1 \
    libfontconfig1 \
    unzip \
    wget \
    # Explicitly install python3.11 and its venv module in the final stage
    python3.11 \
    python3.11-venv \
    # Link python3 to python3.11 for broader compatibility if needed, though CMD uses python3.11 explicitly
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Set working directory for the application
WORKDIR /app

# Create a virtual environment using python3.11
RUN python3.11 -m venv .venv

# Activate the virtual environment by setting the PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Copy requirements.txt from the build-env stage to the final stage's WORKDIR
COPY --from=build-env /app/requirements.txt .

# Install Python dependencies into the newly created virtual environment
# Ensure pip is upgraded within this venv before installing packages
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# --- Debugging Steps (Optional, but helpful for build logs) ---
# Check if gunicorn executable exists in the venv's bin directory
RUN ls -l /app/.venv/bin/gunicorn || echo "gunicorn executable not found where expected"
# Check if gunicorn module is discoverable by Python
RUN python3.11 -c "import gunicorn; print('gunicorn module found')" || echo "gunicorn module not found"
# --- End Debugging Steps ---

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
