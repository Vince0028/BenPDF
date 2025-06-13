from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
from PIL import Image
import os
import io
from pdf2docx import Converter as PdfToDocxConverter
from docx2pdf import convert as docx_to_pdf_convert
import logging
import zipfile
import glob
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configuration for upload and converted folders
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CONVERTED_FOLDER'] = 'converted'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB limit for uploads

# Ensure upload and converted directories exist (for local testing mostly)
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
        if not (image_url.startswith('http://') or image_url.startswith('https://')):
            logger.warning(f"Invalid URL format: {image_url}")
            return jsonify({'error': 'Invalid URL format. Must start with http:// or https://'}), 400
    else:
        logger.warning("No file or URL provided for image conversion.")
        return jsonify({'error': 'No image file uploaded or URL provided.'}), 400

    output_buffer = io.BytesIO()
    converted_filename = "converted_image.png"

    try:
        if file:
            img = Image.open(file.stream)
            logger.info("Image file opened successfully.")
        elif image_url:
            logger.info(f"Attempting to fetch image from URL: {image_url}")
            import requests
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

    import tempfile
    temp_dir = tempfile.mkdtemp()
    input_filepath = os.path.join(temp_dir, filename)
    
    file.save(input_filepath)
    logger.info(f"Saved uploaded file to temporary path: {input_filepath}")

    converted_output_filename = ""
    output_filepath = ""

    try:
        if filename.lower().endswith('.pdf'):
            converted_output_filename = os.path.splitext(filename)[0] + '.docx'
            output_filepath = os.path.join(temp_dir, converted_output_filename)
            logger.info(f"Converting PDF to DOCX. Output: {output_filepath}")
            cv = PdfToDocxConverter(input_filepath)
            cv.convert(output_filepath, start=0, end=None)
            cv.close()
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            logger.info("PDF to DOCX conversion complete.")

        elif filename.lower().endswith(('.doc', '.docx')):
            converted_output_filename = os.path.splitext(filename)[0] + '.pdf'
            output_filepath = os.path.join(temp_dir, converted_output_filename)
            logger.info(f"Converting DOC/DOCX to PDF. Output: {output_filepath}")
            docx_to_pdf_convert(input_filepath, output_filepath)
            mimetype = 'application/pdf'
            logger.info("DOCX to PDF conversion complete.")
        else:
            logger.warning(f"Unsupported document file type for conversion: {filename}")
            return jsonify({'error': 'Unsupported document file type.'}), 400

        response = send_file(
            output_filepath,
            mimetype=mimetype,
            as_attachment=True,
            download_name=converted_output_filename
        )
        logger.info(f"Sending converted document: {converted_output_filename}")
        return response

    except Exception as e:
        logger.exception("An error occurred during document conversion.")
        return jsonify({'error': f'An error occurred during conversion: {e}'}), 500
    finally:
        if os.path.exists(input_filepath):
            os.remove(input_filepath)
        if os.path.exists(output_filepath):
            os.remove(output_filepath)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")


def generate_conversion_steps(input_value, source_base, target_base_int, decimal_value):
    """Generates a detailed step-by-step solution for base conversions."""
    steps = []
    base_names = {2: "Binary", 8: "Octal", 10: "Decimal", 16: "Hexadecimal"}
    source_base_name = base_names[source_base]
    target_base_name = base_names[target_base_int]

    # Step 1: Convert source to Decimal (if not already decimal)
    if source_base != 10:
        steps.append(f"Step 1: Convert {source_base_name} {input_value} to Decimal.")
        if source_base in [2, 8, 16]:
            power_base = source_base
            expanded_form_parts = []
            decimal_calc_val = 0
            # Iterate from right to left (least significant digit to most significant)
            for i, digit_char in enumerate(reversed(input_value)):
                digit_val = int(digit_char, source_base) # Handles 'A'-'F' for hex
                term = digit_val * (power_base ** i)
                expanded_form_parts.append(f"({str(digit_val)}×{power_base}^{i})")
                decimal_calc_val += term
            
            # Reverse the expanded_form_parts for correct display order (highest power first)
            expanded_form_str = " + ".join(expanded_form_parts[::-1]) 
            steps.append(f"   Method: Multiply each digit by its base ({power_base}) raised to its position (right to left, starting from 0), then sum the results.")
            steps.append(f"   {input_value} = {expanded_form_str} = {decimal_value}")
    else:
        steps.append(f"Step 1: Source is already Decimal: {input_value}")
        
    # Step 2: Convert Decimal to Target Base (if not already target base)
    if target_base_int != 10:
        steps.append(f"\nStep 2: Convert Decimal {decimal_value} to {target_base_name}.")
        steps.append(f"   Method: Divide the decimal number by {target_base_int} repeatedly and collect the remainders in reverse order.")
        
        current_num = decimal_value
        remainders_display = []
        division_steps = []
        
        if current_num == 0:
            division_steps.append(f"   0 ÷ {target_base_int} = 0 R0")
            remainders_display.append("0")
        else:
            while current_num > 0:
                remainder = current_num % target_base_int
                display_remainder = ""
                if target_base_int == 16:
                    display_remainder = format(remainder, 'X') # Convert to hex char (A-F)
                else:
                    display_remainder = str(remainder)
                
                remainders_display.append(display_remainder)
                division_steps.append(f"   {current_num} ÷ {target_base_int} = {current_num // target_base_int} R{display_remainder}")
                current_num //= target_base_int
        
        steps.extend(division_steps)
        final_result_reversed = "".join(remainders_display[::-1]) # Reverse remainders to get final result
        steps.append(f"   Collect remainders in reverse: {final_result_reversed}")
    else:
        steps.append(f"\nStep 2: Target is already Decimal: {decimal_value}")

    return "\n".join(steps)


@app.route('/api/convert-base', methods=['POST'])
def convert_base_api():
    logger.info("Received request for base conversion.")
    data = request.json
    input_value = data.get('inputValue')
    source_base_str = data.get('sourceBase')
    target_base_str = data.get('targetBase')

    if not all([input_value, source_base_str, target_base_str]):
        logger.warning("Missing input for base conversion.")
        return jsonify({'error': 'Missing input value, source base, or target base.'}), 400

    # Map string bases to integer bases and their display names
    base_map = {
        'binary': {'int': 2, 'name': 'Binary'},
        'decimal': {'int': 10, 'name': 'Decimal'},
        'octal': {'int': 8, 'name': 'Octal'},
        'hexadecimal': {'int': 16, 'name': 'Hexadecimal'}
    }
    
    source_info = base_map.get(source_base_str)
    target_info = base_map.get(target_base_str)

    if source_info is None or target_info is None:
        logger.warning(f"Invalid source or target base specified: {source_base_str} -> {target_base_str}")
        return jsonify({'error': 'Invalid source or target base. Choose from binary, decimal, octal, hexadecimal.'}), 400

    source_base = source_info['int']
    target_base = target_info['int']
    
    # Input validation based on source base
    input_value = input_value.upper() # Convert hex input to uppercase for consistency
    if source_base == 2:
        if not re.fullmatch(r'[01]+', input_value):
            return jsonify({'error': 'Invalid binary input. Must contain only 0s and 1s.'}), 400
    elif source_base == 8:
        if not re.fullmatch(r'[0-7]+', input_value):
            return jsonify({'error': 'Invalid octal input. Must contain digits 0-7.'}), 400
    elif source_base == 10:
        if not re.fullmatch(r'[0-9]+', input_value):
            return jsonify({'error': 'Invalid decimal input. Must contain only 0-9.'}), 400
    elif source_base == 16:
        if not re.fullmatch(r'[0-9A-F]+', input_value):
            return jsonify({'error': 'Invalid hexadecimal input. Must contain 0-9 and A-F.'}), 400

    try:
        # Convert input_value to an integer (decimal representation)
        decimal_value = int(input_value, source_base)
        logger.info(f"Converted '{input_value}' from base {source_base} to decimal: {decimal_value}")

        # Convert decimal_value to the target base
        converted_value = ""
        if target_base == 2:
            converted_value = bin(decimal_value)[2:] # Remove "0b" prefix
        elif target_base == 8:
            converted_value = oct(decimal_value)[2:] # Remove "0o" prefix
        elif target_base == 10:
            converted_value = str(decimal_value)
        elif target_base == 16:
            converted_value = hex(decimal_value)[2:].upper() # Remove "0x" prefix and make uppercase
        
        logger.info(f"Converted decimal '{decimal_value}' to base {target_base}: {converted_value}")

        # Generate solution steps
        solution_steps = generate_conversion_steps(input_value, source_base, target_base, decimal_value)
        
        return jsonify({'result': converted_value, 'solution': solution_steps}), 200

    except ValueError as e:
        logger.error(f"ValueError during base conversion: {e}")
        return jsonify({'error': 'Invalid number format for the specified source base.'}), 400
    except Exception as e:
        logger.exception("An unexpected error occurred during base conversion.")
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500
