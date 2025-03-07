from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging
from io import BytesIO

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.services.data_processor import DataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.before_request
def before_request():
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler to ensure JSON responses"""
    logger.error(f"Unhandled error: {str(error)}", exc_info=True)
    response = jsonify({
        'status': 'error',
        'message': 'Error interno del servidor',
        'validation_errors': [{
            'type': 'server_error',
            'message': 'Error interno del servidor',
            'details': str(error)
        }]
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response, 500

@app.route('/process', methods=['POST'])
def process_file():
    """Handle file upload and processing"""
    try:
        logger.info("Processing file upload request")
        logger.info(f"Request form data: {request.form}")
        logger.info(f"Request files: {request.files}")

        if 'file' not in request.files:
            logger.warning("No file provided in request")
            return jsonify({
                'status': 'error',
                'message': 'Error de validación',
                'validation_errors': [{
                    'type': 'missing_file',
                    'message': 'No se proporcionó ningún archivo'
                }]
            }), 400

        file = request.files['file']
        package_id = request.form.get('package_id')

        logger.info(f"Received file: {file.filename} for package: {package_id}")

        if not file or not package_id:
            logger.warning("Missing required fields")
            return jsonify({
                'status': 'error',
                'message': 'Error de validación',
                'validation_errors': [{
                    'type': 'missing_fields',
                    'message': 'Faltan campos requeridos',
                    'details': 'Se requiere tanto el archivo como el ID del paquete'
                }]
            }), 400

        # Initialize processor and database
        processor = DataProcessor()
        try:
            processor.setup_database()
        except ValueError as e:
            error_data = e.args[0] if isinstance(e.args[0], dict) else {'message': str(e)}
            logger.error(f"Database setup error: {error_data}")
            return jsonify({
                'status': 'error',
                'message': error_data.get('message', 'Error de conexión'),
                'validation_errors': error_data.get('validation_errors', [{
                    'type': 'database_error',
                    'message': str(e)
                }])
            }), 500

        try:
            # Get file content as bytes
            file_content = file.stream.read() if hasattr(file, 'stream') else None

            if not isinstance(file_content, bytes):
                logger.error(f"Invalid file content type: {type(file_content)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Error de validación',
                    'validation_errors': [{
                        'type': 'invalid_format',
                        'message': 'Formato de archivo inválido',
                        'details': f'El tipo de contenido recibido es {type(file_content)}'
                    }]
                }), 400

            # Process the upload
            success = processor.process_direct_upload(
                config={
                    'max_file_size_mb': 100,
                    'allowed_ips': ['127.0.0.1', '::1'],
                    'require_2fa': False
                },
                file_data=file_content,
                original_filename=file.filename,
                sender_id=package_id
            )

            if success:
                logger.info("File processed successfully")
                return jsonify({
                    'status': 'success',
                    'message': 'Archivo procesado correctamente'
                })
            else:
                logger.error("File processing failed without raising an exception")
                return jsonify({
                    'status': 'error',
                    'message': 'Error al procesar el archivo',
                    'validation_errors': [{
                        'type': 'processing_error',
                        'message': 'No se pudo procesar el archivo correctamente'
                    }]
                }), 400

        except ValueError as e:
            error_data = e.args[0] if isinstance(e.args[0], dict) else {'message': str(e)}
            logger.error(f"Validation error: {error_data}")
            return jsonify({
                'status': 'error',
                'message': error_data.get('message', 'Error de validación'),
                'validation_errors': error_data.get('validation_errors', [{
                    'type': 'validation_error',
                    'message': str(e)
                }])
            }), 400

    except Exception as e:
        logger.exception("Unhandled error processing file")
        return jsonify({
            'status': 'error',
            'message': 'Error interno del servidor',
            'validation_errors': [{
                'type': 'server_error',
                'message': 'Error interno del servidor',
                'details': str(e)
            }]
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)