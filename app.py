# app.py
from flask import Flask, request, send_file, render_template, jsonify
from werkzeug.utils import secure_filename
import os
import uuid # For unique filenames to prevent conflicts

# Conversion Libraries
from PIL import Image # For image manipulation
from pdf2docx import Converter as PdfToDocxConverter # Renamed to avoid conflict
from docx2pdf import convert as docx_to_pdf_convert # Renamed to avoid conflict

app = Flask(__name__)

# Define upload and converted file directories
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# --- Frontend Route ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API Endpoints for Conversion ---

@app.route('/api/convert-image', methods=['POST'])
def convert_image_api():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # Create a unique filename for the uploaded file
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        _, file_extension = os.path.splitext(original_filename)
        temp_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}{file_extension}")
        file.save(temp_upload_path)

        try:
            # Define output filename with a camera-like prefix and JPG format
            converted_filename = f"camera_photo_{unique_id}.jpg"
            converted_file_path = os.path.join(app.config['CONVERTED_FOLDER'], converted_filename)

            # Open image with Pillow, resize (optional), and save as JPG
            img = Image.open(temp_upload_path)
            # You can add more image processing here, e.g., resizing, quality adjustment
            # img.thumbnail((1200, 1200), Image.Resampling.LANCZOS) # Example: Resize to max 1200px
            img.save(converted_file_path, "JPEG", quality=90) # Save as JPG with 90% quality

            # Clean up the temporarily uploaded file
            os.remove(temp_upload_path)

            # Send the converted file back to the client
            return send_file(converted_file_path, as_attachment=True, download_name=converted_filename)

        except Exception as e:
            # Clean up any files created before the error
            if os.path.exists(temp_upload_path):
                os.remove(temp_upload_path)
            if os.path.exists(converted_file_path):
                os.remove(converted_file_path)
            app.logger.error(f"Image conversion error: {e}")
            return jsonify({'error': f'Image conversion failed: {str(e)}'}), 500
    return jsonify({'error': 'An unexpected error occurred during image processing'}), 500

@app.route('/api/convert-document', methods=['POST'])
def convert_document_api():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        base_name, file_extension = os.path.splitext(original_filename)
        file_extension = file_extension.lower()

        temp_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}{file_extension}")
        file.save(temp_upload_path)

        converted_filename = ""
        converted_file_path = ""

        try:
            if file_extension == '.pdf':
                converted_filename = f"{base_name}.docx"
                converted_file_path = os.path.join(app.config['CONVERTED_FOLDER'], f"{unique_id}.docx")
                
                cv = PdfToDocxConverter(temp_upload_path)
                cv.convert(converted_file_path)
                cv.close()
            elif file_extension in ['.doc', '.docx']:
                # For .doc files, consider converting to .docx first if docx2pdf doesn't handle them directly.
                # docx2pdf works best with .docx. If you need .doc, you might need a more complex solution
                # or tell users to save as .docx first.
                if file_extension == '.doc':
                    # This path might need more robust handling for .doc to .docx before PDF conversion
                    # For simplicity, we'll proceed assuming docx2pdf can handle it or expect .docx
                    app.logger.warning("Converting .doc file. docx2pdf typically works best with .docx.")

                converted_filename = f"{base_name}.pdf"
                converted_file_path = os.path.join(app.config['CONVERTED_FOLDER'], f"{unique_id}.pdf")
                docx_to_pdf_convert(temp_upload_path, converted_file_path)
            else:
                os.remove(temp_upload_path)
                return jsonify({'error': 'Unsupported file type. Only PDF, DOC, DOCX are supported.'}), 400

            # Clean up the temporarily uploaded file
            os.remove(temp_upload_path)

            # Send the converted file back to the client
            # Use original base_name for cleaner download name
            return send_file(converted_file_path, as_attachment=True, download_name=converted_filename)

        except Exception as e:
            # Clean up any files created before the error
            if os.path.exists(temp_upload_path):
                os.remove(temp_upload_path)
            if os.path.exists(converted_file_path):
                os.remove(converted_file_path)
            app.logger.error(f"Document conversion error: {e}")
            # Specific error message for docx2pdf dependency
            if "soffice" in str(e).lower() or "libreoffice" in str(e).lower() or "word" in str(e).lower():
                return jsonify({'error': 'Conversion failed. Please ensure LibreOffice (or MS Word on Windows) is installed on the server.'}), 500
            return jsonify({'error': f'Document conversion failed: {str(e)}'}), 500
    return jsonify({'error': 'An unexpected error occurred during document processing'}), 500

# Cleanup for converted files after they are sent (optional, can be done by a cron job)
@app.after_request
def cleanup_file(response):
    if "X-Sendfile" in response.headers: # Or check if response is a file download
        file_path = response.headers.get("X-Sendfile") or response.headers.get("Content-Disposition").split("filename=")[1].strip('"')
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                app.logger.info(f"Cleaned up {file_path}")
            except Exception as e:
                app.logger.error(f"Error cleaning up file {file_path}: {e}")
    return response


if __name__ == '__main__':
    # When running locally, ensure 'debug=True' is only for development.
    # For production, disable debug and use a production-ready WSGI server like Gunicorn or uWSGI.
    app.run(debug=True)