# app.py

import os
import io
import logging
import zipfile
import glob
import tempfile
import secrets

from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify # jsonify added
from PIL import Image
from pdf2docx import Converter as PdfToDocxConverter
from docx2pdf import convert as docx_to_pdf_convert
from werkzeug.utils import secure_filename # Added this import
from flask_cors import CORS # Added this import
from dotenv import load_dotenv # Added this import

# Load environment variables from .env file
load_dotenv() # Added this call

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app) # Added CORS initialization

# Configuration for upload and converted folders
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CONVERTED_FOLDER'] = 'converted'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Set the SECRET_KEY from environment variable, with a development fallback
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Ensure upload and converted directories exist if running locally,
# (These local directories are less critical now as tempfile.TemporaryDirectory will manage isolated spaces)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['CONVERTED_FOLDER']):
    os.makedirs(app.config['CONVERTED_FOLDER'])

# Allowed image extensions for image conversion
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# Allowed document extensions for document conversion
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/convert-image', methods=['POST'])
def convert_image_api():
    logger.info("Received request for image conversion.")
    file = None
    image_url = None

    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        logger.info(f"File uploaded: {file.filename}")
        if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            logger.warning(f"Invalid image file extension: {file.filename}")
            return jsonify({'error': 'Invalid image file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
    elif 'url' in request.form and request.form['url'].strip() != '':
        image_url = request.form['url'].strip()
        logger.info(f"Image URL provided: {image_url}")
        # Basic URL validation
        if not (image_url.startswith('http://') or image_url.startswith('https://')):
            logger.warning(f"Invalid URL format: {image_url}")
            return jsonify({'error': 'Invalid URL format. Must start with http:// or https://'}), 400
    else:
        logger.warning("No file or URL provided for image conversion.")
        return jsonify({'error': 'No image file uploaded or URL provided.'}), 400

    input_path = None
    output_buffer = io.BytesIO()
    converted_filename = "converted_image.png"

    try:
        if file:
            import requests # Moved import to ensure it's only used if needed
            img = Image.open(file.stream)
            logger.info("Image file opened successfully.")
        elif image_url:
            logger.info(f"Attempting to fetch image from URL: {image_url}")
            import requests # Moved import to ensure it's only used if needed
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            logger.info("Image fetched from URL successfully.")

        if img.mode == 'RGBA':
            img = img.convert('RGB')
        elif img.mode == 'P':
            img = img.convert('RGB')

        img.save(output_buffer, format='PNG')
        output_buffer.seek(0)

        logger.info("Image converted to desired format (PNG) in memory.")

        response = send_file(
            output_buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=converted_filename
        )
        logger.info(f"Sending converted image: {converted_filename}")
        return response

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {e}")
        return jsonify({'error': f"Failed to fetch image from URL: {e}. Please ensure it's a valid, accessible image URL."}), 500
    except Image.UnidentifiedImageError:
        logger.error("Uploaded file/URL content is not a recognized image format.")
        return jsonify({'error': 'Could not identify image file. Please ensure it is a valid image.'}), 400
    except Exception as e:
        logger.exception("An unexpected error occurred during image conversion.")
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500


@app.route('/api/convert-document', methods=['POST'])
def convert_document_api():
    logger.info("Received request for document conversion.")
    if 'file' not in request.files or request.files['file'].filename == '':
        logger.warning("No document file provided for conversion.")
        return jsonify({'error': 'No document file uploaded.'}), 400

    file = request.files['file']
    filename = file.filename
    logger.info(f"Document file uploaded: {filename}")

    if not allowed_file(filename, ALLOWED_DOCUMENT_EXTENSIONS):
        logger.warning(f"Invalid document file extension: {filename}")
        return jsonify({'error': 'Invalid document file type. Allowed: PDF, DOC, DOCX'}), 400

    # Using TemporaryDirectory for robust cleanup
    with tempfile.TemporaryDirectory() as temp_dir:
        input_filepath = os.path.join(temp_dir, secure_filename(filename))

        # Save the uploaded file temporarily
        file.save(input_filepath)
        logger.info(f"Saved uploaded file to temporary path: {input_filepath}")

        converted_output_filename = ""
        output_filepath = ""
        mimetype = ""

        try:
            if filename.lower().endswith('.pdf'):
                # Convert PDF to DOCX
                converted_output_filename = os.path.splitext(filename)[0] + '.docx'
                output_filepath = os.path.join(temp_dir, converted_output_filename)
                logger.info(f"Converting PDF to DOCX. Output: {output_filepath}")
                cv = PdfToDocxConverter(input_filepath)
                cv.convert(output_filepath, start=0, end=None)
                cv.close() # Ensure the converter closes its file handles
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                logger.info("PDF to DOCX conversion complete.")

            elif filename.lower().endswith(('.doc', '.docx')):
                # Convert DOC/DOCX to PDF
                converted_output_filename = os.path.splitext(filename)[0] + '.pdf'
                output_filepath = os.path.join(temp_dir, converted_output_filename)
                logger.info(f"Converting DOC/DOCX to PDF. Output: {output_filepath}")
                # Ensure LibreOffice/MS Office is available on the Render server for docx2pdf
                # This is a critical dependency that might not be present on Render's default environment.
                # You might need a custom Docker image or a different approach for docx2pdf.
                docx_to_pdf_convert(input_filepath, output_filepath)
                mimetype = 'application/pdf'
                logger.info("DOCX to PDF conversion complete.")
            else:
                logger.warning(f"Unsupported document file type for conversion: {filename}")
                return jsonify({'error': 'Unsupported document file type.'}), 400

            # Read the converted file into an in-memory buffer before sending
            # This releases the file handle on disk, allowing TemporaryDirectory to clean up.
            with open(output_filepath, 'rb') as f:
                output_buffer = io.BytesIO(f.read())
            output_buffer.seek(0) # Rewind the buffer to the beginning
            logger.info("Converted document read into memory buffer.")

            # Send the converted file from the in-memory buffer
            response = send_file(
                output_buffer, # <--- Sending BytesIO object instead of filepath
                mimetype=mimetype,
                as_attachment=True,
                download_name=converted_output_filename
            )
            logger.info(f"Sending converted document: {converted_output_filename}")
            return response

        except Exception as e:
            logger.exception("An error occurred during document conversion.")
            return jsonify({'error': f'An error occurred during conversion: {e}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
