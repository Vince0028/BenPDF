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

# Install LibreOffice, unoconv, Python 3.11, its venv module, and critical headless dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    fontconfig \
    libxrender1 \
    libfontconfig1 \
    unzip \
    wget \
    unoconv \
    xvfb \
    # Explicitly install python3.11 and its venv module in the final stage
    python3.11 \
    python3.11-venv \
    # Link python3 to python3.11 for broader compatibility if needed
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    # Clean up apt caches to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Set working directory for the application
WORKDIR /app

# Create a virtual environment using python3.11
RUN python3.11 -m venv .venv

# Activate the virtual environment by adding its bin directory to PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Copy requirements.txt from the build-env stage to the final stage's WORKDIR
COPY --from=build-env /app/requirements.txt .

# Install Python dependencies into the newly created virtual environment
# The ENV PATH above means 'pip' here will refer to '/app/.venv/bin/pip'
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# --- Debugging Steps (These will appear in your Render build logs) ---
# Check if gunicorn executable exists in the venv's bin directory
RUN echo "DEBUG: Checking for /app/.venv/bin/gunicorn:" && ls -l /app/.venv/bin/gunicorn || echo "DEBUG ERROR: gunicorn executable NOT found in venv bin"
# Check if gunicorn module is discoverable by Python using the venv's python
RUN echo "DEBUG: Checking for gunicorn module discoverability:" && /app/.venv/bin/python -c "import gunicorn; print('DEBUG SUCCESS: gunicorn module found using venv python')" || echo "DEBUG ERROR: gunicorn module NOT found using venv python"
# Test unoconv itself during build
RUN echo "DEBUG: Testing unoconv command:" && \
    echo "This is a test document." > test.txt && \
    xvfb-run -a unoconv -f pdf test.txt || echo "DEBUG ERROR: unoconv test failed!"
# --- End Debugging Steps ---


# Copy the rest of your application code
COPY . .

# Create ephemeral directories for uploads and converted files and ensure they are writable
RUN mkdir -p uploads converted && chmod -R 777 uploads converted

# Expose the port your Flask app (Gunicorn) will listen on
# Render typically expects port 10000
EXPOSE 10000

# Command to run your Flask application using Gunicorn
# Explicitly use the Python interpreter from within the virtual environment
CMD ["/app/.venv/bin/python", "-m", "gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
