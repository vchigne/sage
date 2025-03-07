"""REST API for SAGE."""
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
from typing import Tuple, Dict, Any
from dotenv import load_dotenv
import yaml

from ..processors.yaml_processor import YAMLProcessor
from ..processors.package_processor import PackageProcessor
from ..processors.sender_processor import SenderProcessor
from ..utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Configure upload settings
ALLOWED_EXTENSIONS = {'yaml', 'yml', 'zip', 'csv', 'xlsx', 'xls'}
UPLOAD_FOLDER = tempfile.gettempdir()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    def allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/')
    def index() -> Tuple[Dict[str, Any], int]:
        """API root endpoint."""
        logger.info("Accessing root endpoint")
        return jsonify({
            'name': 'SAGE API',
            'version': '1.0.0',
            'description': 'API for SAGE data validation and processing',
            'endpoints': [
                {'path': '/', 'method': 'GET', 'description': 'This information'},
                {'path': '/api/validate-yaml', 'method': 'POST', 'description': 'Validate YAML file'},
                {'path': '/api/process-package', 'method': 'POST', 'description': 'Process package ZIP'},
                {'path': '/api/validate-sender', 'method': 'POST', 'description': 'Validate sender'}
            ]
        }), 200

    @app.route('/api/process-package', methods=['POST'])
    def process_package() -> Tuple[Dict[str, Any], int]:
        """Process a package file (ZIP, CSV, or Excel)."""
        logger.info("Processing package request")
        logger.info(f"Request files: {request.files}")
        logger.info(f"Request form: {request.form}")
        logger.info(f"Request headers: {dict(request.headers)}")

        # Dump files content for debugging
        for key, file in request.files.items():
            logger.info(f"File {key}: filename={file.filename}, content_type={file.content_type}")

        # Check if required files were uploaded
        if 'file' not in request.files or 'catalog_yaml' not in request.files:
            logger.error("Missing required files")
            logger.error(f"Expected 'file' and 'catalog_yaml', got: {list(request.files.keys())}")
            return jsonify({
                'status': 'error',
                'message': 'Error de validación',
                'details': 'Se requieren el archivo de datos (CSV, Excel o ZIP) y el YAML del paquete'
            }), 400

        file = request.files['file']
        catalog_yaml = request.files['catalog_yaml']
        catalogs_dir = request.form.get('catalogs_dir', '')

        if file.filename == '' or catalog_yaml.filename == '':
            logger.error("No file selected")
            return jsonify({
                'status': 'error',
                'message': 'Error de validación',
                'details': 'No se seleccionó ningún archivo'
            }), 400

        try:
            # Save files temporarily
            data_filename = secure_filename(file.filename)
            data_filepath = os.path.join(UPLOAD_FOLDER, data_filename)
            file.save(data_filepath)

            package_filename = secure_filename(catalog_yaml.filename)
            package_filepath = os.path.join(UPLOAD_FOLDER, package_filename)
            catalog_yaml.save(package_filepath)

            logger.info(f"Processing data file: {data_filename}")

            # Process package
            processor = PackageProcessor()
            success, validation_results = processor.process_package(
                data_file=data_filepath,
                package_yaml=package_filepath,
                catalogs_dir=catalogs_dir if catalogs_dir else os.path.dirname(package_filepath),
                force=False
            )

            # Clean up
            os.remove(data_filepath)
            os.remove(package_filepath)

            if success:
                logger.info("Package processing successful")
                return jsonify({
                    'status': 'success',
                    'message': 'Archivo procesado correctamente'
                }), 200
            else:
                logger.error(f"Package processing failed: {validation_results}")
                return jsonify({
                    'status': 'error',
                    'message': 'Error en la validación',
                    'validation_results': validation_results
                }), 400

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Error del servidor',
                'details': str(e)
            }), 500

    @app.route('/api/validate-yaml', methods=['POST'])
    def validate_yaml() -> Tuple[Dict[str, Any], int]:
        """Validate a YAML file."""
        logger.info("Processing YAML validation request")

        # Check if file was uploaded
        if 'file' not in request.files:
            logger.error("No file provided in request")
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type'}), 400

        # Get schema type
        schema_type = request.form.get('schema_type')
        if not schema_type or schema_type not in ['catalog', 'package', 'sender']:
            logger.error(f"Invalid schema type: {schema_type}")
            return jsonify({'error': 'Invalid schema type'}), 400

        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            logger.info(f"Processing YAML file: {filename}")

            # Process file
            processor = YAMLProcessor()
            success, errors = processor.validate_yaml(filepath, schema_type)

            # Clean up
            os.remove(filepath)

            if success:
                logger.info("YAML validation successful")
                return jsonify({'status': 'success'}), 200
            else:
                logger.error(f"YAML validation failed: {errors}")
                return jsonify({'status': 'error', 'errors': errors}), 400

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/validate-sender', methods=['POST'])
    def validate_sender() -> Tuple[Dict[str, Any], int]:
        """Validate a sender configuration."""
        logger.info("Processing sender validation request")

        # Check if file was uploaded
        if 'file' not in request.files:
            logger.error("No file provided in request")
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400

        # Get package name
        package_name = request.form.get('package_name')
        if not package_name:
            logger.error("Package name required")
            return jsonify({'error': 'Package name required'}), 400

        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            logger.info(f"Processing sender file: {filename}")

            # Process file
            processor = SenderProcessor()
            success, errors = processor.process_sender(filepath, package_name)

            # Clean up
            os.remove(filepath)

            if success:
                logger.info("Sender validation successful")
                return jsonify({'status': 'success'}), 200
            else:
                logger.error(f"Sender validation failed: {errors}")
                return jsonify({'status': 'error', 'errors': errors}), 400

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    return app

if __name__ == '__main__':
    try:
        logger.info("Starting SAGE API server...")
        app = create_app()
        logger.info("Flask app created successfully")
        logger.info("Configuring server parameters...")

        # ALWAYS serve the app on port 5000 and bind to all interfaces
        port = 5000
        host = '0.0.0.0'
        logger.info(f"Starting server on {host}:{port}")

        app.run(
            host=host,
            port=port,
            debug=True,
            use_reloader=False  # Disable reloader to prevent duplicate processes
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise