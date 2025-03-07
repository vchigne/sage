import os
import yaml
import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import imaplib
import email
import pysftp
import json
import pandas as pd
import numpy as np
import zipfile
import rarfile
import requests
from io import BytesIO, StringIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import shutil
from pathlib import Path
import watchdog.observers
import watchdog.events

class StringIOHandler(logging.Handler):
    """Custom logging handler that writes to a StringIO buffer."""
    def __init__(self):
        super().__init__()
        self.log_buffer = StringIO()

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_buffer.write(msg + '\n')
            self.log_buffer.flush()  # Ensure content is written immediately
        except Exception:
            self.handleError(record)

    @property
    def log_content(self):
        return self.log_buffer.getvalue()

    def clear(self):
        """Clear the buffer content"""
        self.log_buffer.seek(0)
        self.log_buffer.truncate(0)

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Process data files according to YAML configurations."""

    def __init__(self):
        self.db_connection = None
        self.config_cache = {}
        self.dataframes = {}
        self.current_execution_id = None
        self.log_handler = None

        # Setup string handler for capturing logs
        self.log_handler = StringIOHandler()
        self.log_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        )
        logger.addHandler(self.log_handler)

        # Set logging level to DEBUG for more detailed information
        logger.setLevel(logging.DEBUG)

    def calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate SHA256 hash of file data."""
        return hashlib.sha256(file_data).hexdigest()

    def is_file_processed(self, file_hash: str, sender_id: str) -> Tuple[bool, Optional[str]]:
        """Check if a file has been processed before."""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT status, error_message 
                    FROM processed_files 
                    WHERE file_hash = %s AND sender_id = %s
                    ORDER BY processed_at DESC 
                    LIMIT 1
                    """,
                    (file_hash, sender_id)
                )
                result = cursor.fetchone()
                if result:
                    return True, f"File was previously processed with status: {result[0]}"
                return False, None
        except Exception as e:
            logger.error(f"Error checking processed files: {str(e)}")
            return False, None

    def mark_file_processed(self, file_hash: str, file_name: str, sender_id: str, 
                          method: str, status: str, error_message: Optional[str] = None):
        """Mark a file as processed in the database."""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO processed_files 
                    (file_hash, file_name, sender_id, processing_method, status, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (file_hash, sender_id) 
                    DO UPDATE SET 
                        status = EXCLUDED.status,
                        error_message = EXCLUDED.error_message,
                        processed_at = CURRENT_TIMESTAMP
                    """,
                    (file_hash, file_name, sender_id, method, status, error_message)
                )
                self.db_connection.commit()
        except Exception as e:
            logger.error(f"Error marking file as processed: {str(e)}")
            self.db_connection.rollback()

    def process_filesystem_data(self, config: Dict[str, Any], expected_file: Dict[str, Any], sender_id: str) -> Optional[bytes]:
        """Process a file from the filesystem according to sender configuration."""
        logger.info(f"Processing filesystem file: {expected_file['filename']}")
        try:
            watch_dir = Path(config['watch_directory'])
            processed_dir = Path(config['processed_directory'])
            error_dir = Path(config['error_directory'])

            # Create directories if they don't exist
            processed_dir.mkdir(parents=True, exist_ok=True)
            error_dir.mkdir(parents=True, exist_ok=True)

            file_path = watch_dir / expected_file['filename']
            if not file_path.exists():
                logger.warning(f"File not found in watch directory: {file_path}")
                return None

            # Read file content
            with open(file_path, 'rb') as f:
                file_data = f.read()

            try:
                # Move to processed directory with auto-renaming
                dest_path = processed_dir / file_path.name
                counter = 1
                while dest_path.exists():
                    base_name = file_path.stem
                    suffix = file_path.suffix
                    dest_path = processed_dir / f"{base_name}_{counter}{suffix}"
                    counter += 1

                shutil.move(str(file_path), str(dest_path))
                logger.info(f"Moved processed file to: {dest_path}")

                return file_data

            except Exception as e:
                logger.error(f"Error processing filesystem data: {str(e)}")
                # Move to error directory on failure
                error_path = error_dir / file_path.name
                if file_path.exists():
                    counter = 1
                    while error_path.exists():
                        base_name = file_path.stem
                        suffix = file_path.suffix
                        error_path = error_dir / f"{base_name}_{counter}{suffix}"
                        counter += 1
                    shutil.move(str(file_path), str(error_path))
                    logger.error(f"Moved failed file to: {error_path}")
                return None

        except Exception as e:
            logger.error(f"Error in filesystem processing: {str(e)}")
            return None

    def process_sftp_data(self, config: Dict[str, Any], expected_file: Dict[str, Any], sender_id: str) -> Optional[bytes]:
        """Process a file from SFTP according to sender configuration."""
        logger.info(f"Processing SFTP file: {expected_file['filename']}")
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None  # TODO: Implement hostkey verification

            with pysftp.Connection(
                config['host'],
                username=config['username'],
                password=config['password'],
                cnopts=cnopts
            ) as sftp:
                remote_path = f"{config['directory']}/{expected_file['filename']}"
                processed_dir = f"{config['directory']}/processed"
                error_dir = f"{config['directory']}/error"

                # Create processed and error directories if they don't exist
                if not sftp.exists(processed_dir):
                    sftp.mkdir(processed_dir)
                if not sftp.exists(error_dir):
                    sftp.mkdir(error_dir)

                if not sftp.exists(remote_path):
                    logger.warning(f"File not found in SFTP: {remote_path}")
                    return None

                try:
                    # Download file content
                    buffer = BytesIO()
                    sftp.getfo(remote_path, buffer)
                    buffer.seek(0)
                    file_data = buffer.read()

                    # Move to processed directory with auto-renaming
                    filename = os.path.basename(remote_path)
                    processed_path = f"{processed_dir}/{filename}"
                    counter = 1
                    while sftp.exists(processed_path):
                        base_name, ext = os.path.splitext(filename)
                        processed_path = f"{processed_dir}/{base_name}_{counter}{ext}"
                        counter += 1

                    sftp.rename(remote_path, processed_path)
                    logger.info(f"Moved processed file to: {processed_path}")

                    return file_data

                except Exception as e:
                    logger.error(f"Error processing SFTP file: {str(e)}")
                    # Move to error directory on failure
                    error_path = f"{error_dir}/{os.path.basename(remote_path)}"
                    counter = 1
                    while sftp.exists(error_path):
                        base_name, ext = os.path.splitext(filename)
                        error_path = f"{error_dir}/{base_name}_{counter}{ext}"
                        counter += 1

                    if sftp.exists(remote_path):
                        sftp.rename(remote_path, error_path)
                        logger.error(f"Moved failed file to: {error_path}")
                    return None

        except Exception as e:
            logger.error(f"Error in SFTP processing: {str(e)}")
            return None

    def validate_file_extension(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate if a file has an allowed extension."""
        allowed_extensions = ('.xlsx', '.xls', '.zip')
        file_extension = os.path.splitext(filename.lower())[1]

        if not file_extension:
            return False, "El archivo no tiene extensión"

        if file_extension not in allowed_extensions:
            return False, f"Tipo de archivo no permitido. Solo se permiten archivos: {', '.join(allowed_extensions)}"

        return True, None

    def process_direct_upload(self, config: Dict[str, Any], file_data: bytes, 
                            original_filename: str, sender_id: str) -> bool:
        """Process a directly uploaded file."""
        logger.info(f"Processing direct upload: {original_filename}")
        try:
            # Validate input types
            if not isinstance(file_data, bytes):
                logger.error(f"Invalid file_data type: {type(file_data)}")
                raise ValueError({
                    'validation_errors': [{
                        'type': 'input_error',
                        'message': 'Formato de archivo inválido',
                        'details': f'Se esperaba bytes, se recibió {type(file_data)}'
                    }],
                    'message': 'Error en el formato del archivo'
                })

            # Process files according to type
            components = []
            try:
                if original_filename.lower().endswith('.zip'):
                    logger.info("Processing ZIP file")
                    buffer = BytesIO(file_data)
                    with zipfile.ZipFile(buffer) as zf:
                        excel_files_found = False
                        for name in zf.namelist():
                            logger.info(f"Processing file from ZIP: {name}")
                            # Skip directories and hidden files
                            if name.endswith('/') or name.startswith('.'):
                                continue

                            # Solo procesar archivos Excel dentro del ZIP
                            if name.lower().endswith(('.xlsx', '.xls')):
                                excel_files_found = True
                                with zf.open(name) as f:
                                    components.append({
                                        'filename': name,
                                        'content': f.read()
                                    })

                        if not excel_files_found:
                            logger.error("No Excel files found in ZIP")
                            raise ValueError({
                                'validation_errors': [{
                                    'type': 'invalid_content',
                                    'message': 'El archivo ZIP no contiene archivos Excel válidos'
                                }],
                                'message': 'Error en el contenido del ZIP'
                            })
                else:
                    # Procesar archivo Excel individual
                    logger.info("Processing single Excel file")
                    components.append({
                        'filename': original_filename,
                        'content': file_data
                    })

            except zipfile.BadZipFile as e:
                logger.error(f"Invalid ZIP file: {str(e)}")
                raise ValueError({
                    'validation_errors': [{
                        'type': 'invalid_zip',
                        'message': 'El archivo ZIP está corrupto o tiene un formato inválido'
                    }],
                    'message': 'Error en el archivo ZIP'
                })

            # Mark file as processed
            file_hash = self.calculate_file_hash(file_data)
            self.mark_file_processed(
                file_hash=file_hash,
                file_name=original_filename,
                sender_id=sender_id,
                method='direct_upload',
                status='processed'
            )

            logger.info("File processed successfully")
            return True

        except Exception as e:
            logger.error(f"Error in process_direct_upload: {str(e)}", exc_info=True)
            if isinstance(e, ValueError) and isinstance(e.args[0], dict):
                raise
            raise ValueError({
                'validation_errors': [{
                    'type': 'unknown_error',
                    'message': str(e)
                }],
                'message': 'Error desconocido'
            })

    def process_email_data(self, config: Dict[str, Any], expected_file: Dict[str, Any], sender_id: str) -> Optional[bytes]:
        """
        Process a file from email according to sender configuration.
        Handles authentication and attachment extraction.
        """
        logger.info(f"Processing email for file: {expected_file['filename']}")
        try:
            logger.debug(f"Connecting to email server: {config['host']}")
            mail = imaplib.IMAP4_SSL(config['host'])
            mail.login(config['username'], config['password'])
            mail.select('inbox')

            search_criteria = f'SUBJECT "{expected_file["subject_pattern"]}"'
            logger.debug(f"Searching emails with criteria: {search_criteria}")
            _, message_numbers = mail.search(None, search_criteria)

            for num in message_numbers[0].split():
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)

                for part in message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    if filename == expected_file['filename']:
                        content = part.get_payload(decode=True)
                        file_data = content

                        # Check if already processed
                        file_hash = self.calculate_file_hash(file_data)
                        is_processed, message = self.is_file_processed(file_hash, sender_id)
                        if is_processed:
                            logger.info(f"File already processed: {message}")
                            return file_data  # Return data for consistency

                        # Mark as processed after successful extraction
                        self.mark_file_processed(
                            file_hash=file_hash,
                            file_name=expected_file['filename'],
                            sender_id=sender_id,
                            method='email',
                            status='processed'
                        )

                        logger.info(f"Found and extracted file from email: {filename}")
                        return file_data

            logger.warning(f"File not found in emails: {expected_file['filename']}")
            return None

        except Exception as e:
            logger.error(f"Error processing email data: {str(e)}")
            return None

    def process_api_data(self, config: Dict[str, Any], expected_file: Dict[str, Any], sender_id: str) -> Optional[bytes]:
        """
        Process a file from API according to sender configuration.
        Handles authentication and data retrieval.
        """
        logger.info(f"Processing API data for file: {expected_file['filename']}")
        try:
            headers = {
                'Authorization': f"Bearer {config['api_key']}"
            }

            logger.debug(f"Making API request to: {config['endpoint']}")
            response = requests.request(
                method=config['method'],
                url=config['endpoint'],
                headers=headers
            )

            if not response.ok:
                logger.error(f"API request failed: {response.text}")
                return None

            file_data = response.content

            # Check if already processed
            file_hash = self.calculate_file_hash(file_data)
            is_processed, message = self.is_file_processed(file_hash, sender_id)
            if is_processed:
                logger.info(f"File already processed: {message}")
                return file_data  # Return data for consistency

            # Mark as processed after successful download
            self.mark_file_processed(
                file_hash=file_hash,
                file_name=expected_file['filename'],
                sender_id=sender_id,
                method='api',
                status='processed'
            )

            logger.info("Successfully retrieved data from API")
            return file_data

        except Exception as e:
            logger.error(f"Error processing API data: {str(e)}")
            return None

    def extract_package_contents(self, file_data: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Extract contents from a compressed file or process a single file.
        Supports ZIP and RAR formats, with special handling for Excel files.
        """
        logger.info(f"Extracting contents from: {filename}")
        try:
            if not isinstance(file_data, bytes):
                logger.error(f"Invalid file_data type: {type(file_data)}")
                raise ValueError({
                    'validation_errors': [{
                        'type': 'input_error',
                        'message': 'Formato de archivo inválido',
                        'details': {
                            'expected': 'bytes',
                            'received': str(type(file_data))
                        }
                    }],
                    'message': 'Error en el formato del archivo'
                })

            contents = []
            if filename.endswith('.zip'):
                logger.info("Processing ZIP file")
                file_like = BytesIO(file_data)
                try:
                    with zipfile.ZipFile(file_like) as zf:
                        for name in zf.namelist():
                            with zf.open(name) as file:
                                file_content = file.read()
                                # Determine file type and process accordingly
                                if name.lower().endswith(('.xlsx', '.xls')):
                                    logger.info(f"Processing Excel file from ZIP: {name}")
                                    excel_buffer = BytesIO(file_content)
                                    df = pd.read_excel(excel_buffer)
                                    contents.append({
                                        'filename': name,
                                        'content': df.to_csv(index=False).encode('utf-8')
                                    })
                                else:
                                    contents.append({
                                        'filename': name,
                                        'content': file_content
                                    })
                except zipfile.BadZipFile as e:
                    logger.error(f"Error processing ZIP file: {str(e)}")
                    raise ValueError({
                        'validation_errors': [{
                            'type': 'zip_error',
                            'message': 'El archivo ZIP está corrupto o tiene un formato inválido'
                        }]
                    })
            elif filename.lower().endswith(('.xlsx', '.xls')):
                logger.info(f"Processing single Excel file: {filename}")
                excel_buffer = BytesIO(file_data)
                df = pd.read_excel(excel_buffer)
                contents.append({
                    'filename': filename,
                    'content': df.to_csv(index=False).encode('utf-8')
                })
            else:
                logger.info(f"Processing single file: {filename}")
                contents.append({
                    'filename': filename,
                    'content': file_data
                })

            return contents

        except Exception as e:
            logger.error(f"Error in extract_package_contents: {str(e)}", exc_info=True)
            raise ValueError({
                'validation_errors': [{
                    'type': 'processing_error',
                    'message': 'Error al procesar el archivo',
                    'details': str(e)
                }],
                'message': 'Error al procesar el archivo'
            })

    def validate_component(self, df: pd.DataFrame, rules: Dict[str, Any], component_name: str = "unknown") -> tuple[bool, Optional[str]]:
        """
        Validate data component using pandas expressions.
        Returns detailed error messages when validation fails.
        """
        logger.info("Starting component validation")
        try:
            validation_env = {
                'df': df,
                'pd': pd,
                'np': np
            }

            # Field level validations
            for field in rules.get('fields', []):
                try:
                    logger.debug(f"Evaluating field validation: {field['validation_expression']}")
                    result = eval(
                        field['validation_expression'],
                        {"__builtins__": {}},
                        validation_env
                    )
                    if hasattr(result, 'all'):
                        if not result.all():
                            # Get the failing rows
                            failing_rows = df[~result].index.tolist()
                            failing_values = df.loc[failing_rows, field['name']].tolist()
                            error_msg = f"""                            Validation Error in {component_name}:
                            - Field: {field['name']}
                            - Rule: {field['validation_expression']}
                            - Failed Rows: {failing_rows}
                            - Invalid Values: {failing_values}
                            """
                            return False, error_msg
                    elif not result:
                        error_msg = f"""
                        Validation Error in {component_name}:
                        - Field: {field['name']}
                        - Rule: {field['validation_expression']}
                        - Entire column failed validation
                        """
                        return False, error_msg
                except Exception as e:
                    logger.error(f"Error in field validation: {str(e)}")
                    return False, f"Error evaluating field validation for {field['name']} in {component_name}: {str(e)}"

            # Row level validation
            if 'row_validation' in rules:
                try:
                    result = eval(
                        rules['row_validation']['validation_expression'],
                        {"__builtins__": {}},
                        validation_env
                    )
                    if hasattr(result, 'all'):
                        if not result.all():
                            # Get failing rows
                            failingrows = df[~result].index.tolist()
                            error_msg = f"""
                            Row Validation Error in {component_name}:
                            - Rule: {rules['row_validation']['description']}
                            - Failed Rows: {failing_rows}
                            - Row Data: {df.loc[failing_rows].to_dict('records')}
                            """
                            return False, error_msg
                    elif not result:
                        error_msg = f"""
                        Row Validation Error in {component_name}:
                        - Rule: {rules['row_validation']['description']}
                        - All rows failed validation
                        """
                        return False, error_msg
                except Exception as e:
                    logger.error(f"Error in row validation: {str(e)}")
                    return False, f"Error evaluating row validation in {component_name}: {str(e)}"

            # Catalog level validation
            if 'catalog_validation' in rules:
                try:
                    result = eval(
                        rules['catalog_validation']['validation_expression'],
                        {"__builtins": {}},
                        validation_env
                    )
                    if hasattr(result, 'all'):
                        if not result.all():
                            error_msg = f"""
                            Catalog Validation Error in {component_name}:
                            - Rule: {rules['catalog_validation']['description']}
                            - Data Summary: {df.describe().to_dict()}
                            """
                            return False, error_msg
                    elif not result:
                        error_msg = f"""
                        Catalog Validation Error in {component_name}:
                        - Rule: {rules['catalog_validation']['description']}
                        - Validation failed for entire catalog
                        """
                        return False, error_msg
                except Exception as e:
                    logger.error(f"Error in catalog validation: {str(e)}")
                    return False, f"Error evaluating catalog validation in {component_name}: {str(e)}"

            logger.info("Component validation completed successfully")
            return True, None

        except Exception as e:
            logger.error(f"Error in component validation: {str(e)}")
            return False, f"Error en la validación del componente: {str(e)}"

    def validate_package_contents(self, components: List[Dict[str, Any]], yaml_config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate package contents against YAML configuration.
        Returns (success, error_message).
        """
        try:
            # Validate expected files from YAML config
            expected_files = yaml_config.get('expected_files', [])
            received_files = [comp['filename'] for comp in components]

            logger.info(f"Expected files: {expected_files}")
            logger.info(f"Received files: {received_files}")

            missing_files = [f for f in expected_files if f not in received_files]
            unexpected_files = [f for f in received_files if f not in expected_files]

            validation_errors = []

            if missing_files:
                validation_errors.append({
                    'type': 'missing_files',
                    'message': f"Faltan archivos requeridos: {', '.join(missing_files)}",
                    'details': {
                        'missing': missing_files
                    }
                })
            if unexpected_files:
                validation_errors.append({
                    'type': 'unexpected_files',
                    'message': f"Archivos no esperados en el paquete: {', '.join(unexpected_files)}",
                    'details': {
                        'unexpected': unexpected_files
                    }
                })

            if validation_errors:
                raise ValueError({
                    'validation_errors': validation_errors,
                    'message': 'Error en la estructura del archivo'
                })

            # Process each component according to YAML rules
            for component in components:
                component_rules = yaml_config.get('components', {}).get(component['filename'])
                if not component_rules:
                    validation_errors.append({
                        'type': 'missing_rules',
                        'message': f"No se encontraron reglas para el archivo: {component['filename']}"
                    })
                    continue

                try:
                    # Convert component content to DataFrame
                    df = pd.read_csv(BytesIO(component['content']))

                    # Validate component structure and content
                    is_valid, error_message = self.validate_component(
                        df, 
                        component_rules, 
                        component['filename']
                    )

                    if not is_valid:
                        validation_errors.append({
                            'type': 'validation_error',
                            'message': error_message,
                            'component': component['filename']
                        })

                except Exception as e:
                    validation_errors.append({
                        'type': 'processing_error',
                        'message': f"Error procesando {component['filename']}: {str(e)}"
                    })

            if validation_errors:
                raise ValueError({
                    'validation_errors': validation_errors,
                    'message': 'Error en la validación de los archivos'
                })

            return True, None

        except Exception as e:
            if isinstance(e, ValueError) and isinstance(e.args[0], dict):
                raise
            logger.error(f"Error in package validation: {str(e)}")
            return False, f"Error en la validación del paquete: {str(e)}"

    def validate_sender_config(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate sender configuration."""
        try:
            required_fields = ['name', 'type', 'schedule']
            missing_fields = [f for f in required_fields if f not in config]

            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"

            if config['type'] not in ['email', 'sftp', 'filesystem', 'api', 'direct_upload']:
                return False, f"Invalid sender type: {config['type']}"

            return True, None

        except Exception as e:
            logger.error(f"Error validating sender configuration: {str(e)}")
            return False, f"Sender validation error: {str(e)}"

    def process_yaml_config(self, yaml_id: str) -> Dict[str, Any]:
        """Process YAML configuration with detailed error logging."""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT config::text as config_text
                    FROM yaml_configs 
                    WHERE id = %s AND active = true
                    """,
                    (yaml_id,)
                )
                result = cursor.fetchone()
                if not result:
                    raise ValueError("No se encontró configuración activa para este paquete")

                try:
                    yaml_config = yaml.safe_load(result[0])
                    if not isinstance(yaml_config, dict):
                        raise ValueError("La configuración YAML no tiene un formato válido")
                    return yaml_config
                except yaml.YAMLError as e:
                    logger.error(f"Error parsing YAML config: {str(e)}")
                    raise ValueError(f"Error al parsear la configuración YAML: {str(e)}")

        except Exception as e:
            logger.error(f"Error processing YAML config: {str(e)}", exc_info=True)
            raise ValueError(f"Error al procesar la configuración: {str(e)}")

    def process_configuration(self, yaml_id: str) -> bool:
        """Process a complete YAML configuration"""
        logger.info(f"Processing configuration for YAML ID: {yaml_id}")
        try:
            success = False
            config = self.process_yaml_config(yaml_id)
            if not config or config.get('status') != 'success':
                error_msg = config.get('message', "Failed to load configuration")
                logger.error(error_msg)
                self.update_execution_status('failed', error_msg)
                return False

            exec_id = self.start_execution(yaml_id)
            logger.info(f"Started new execution tracking")
            self.notify_receivers(config, 'Running', 'Processing started')

            sender_id = config.get('sender_id', yaml_id)

            # Process each package
            for package_config in config.get('packages', []):
                # Check allowed methods
                if 'filesystem' in config['allowed_methods']:
                    file_data = self.process_filesystem_data(
                        config['configurations']['filesystem'],
                        package_config,
                        sender_id
                    )
                    if file_data:
                        success = self.process_package_data(file_data, package_config, config, sender_id, 'filesystem')
                        continue

                if 'sftp' in config['allowed_methods']:
                    file_data = self.process_sftp_data(
                        config['configurations']['sftp'],
                        package_config,
                        sender_id
                    )
                    if file_data:
                        success = self.process_package_data(file_data, package_config, config, sender_id, 'sftp')
                        continue

                if 'email' in config['allowed_methods']:
                    file_data = self.process_email_data(config['configurations']['email'], package_config, sender_id)
                    if file_data:
                        success = self.process_package_data(file_data, package_config, config, sender_id, 'email')
                        continue

                if 'api' in config['allowed_methods']:
                    file_data = self.process_api_data(config['configurations']['api'], package_config, sender_id)
                    if file_data:
                        success = self.process_package_data(file_data, package_config, config, sender_id, 'api')
                        continue

                if 'direct_upload' in config['allowed_methods']:
                    file_data = package_config.get('file_data') # Handle direct upload
                    if file_data:
                        success = self.process_package_data(file_data, package_config, config, sender_id, 'direct_upload')
                        continue

            if success:
                self.update_execution_status('completed')
                self.notify_receivers(config, 'Success', 'Processing completed successfully')
            else:
                self.update_execution_status('failed', 'No data processed successfully')
                self.notify_receivers(config, 'Failed', 'No data processed successfully')

            return success

        except Exception as e:
            error_msg = f"Error processing configuration {yaml_id}: {str(e)}"
            logger.error(error_msg)
            self.update_execution_status('failed', error_msg)
            if 'config' in locals():
                self.notify_receivers(config, 'Failed', error_msg)
            return False

    def process_package_data(self, file_data: bytes, package_config: Dict[str, Any], 
                             sender_config: Dict[str, Any], sender_id: str, method: str) -> bool:
        """Process package data and track its processing status"""
        try:
            # Calculate file hash and check if already processed
            file_hash = self.calculate_file_hash(file_data)
            is_processed, message = self.is_file_processed(file_hash, sender_id)
            if is_processed:
                logger.info(f"Skipping already processed file: {message}")
                return True

            # Extract and process components            
            components = self.extract_package_contents(file_data, package_config['filename'])
            is_package_valid, package_error = self.validate_package(package_config, package_config['filename'])

            if not is_package_valid:
                logger.error(f"Package validation failed: {package_error}")
                self.notify_receivers(sender_config, 'Failed', f"Package validation failed: {package_error}")
                self.mark_file_processed(
                    file_hash=file_hash,
                    file_name=package_config['filename'],
                    sender_id=sender_id,
                    method=method,
                    status='error',
                    error_message=package_error
                )
                return False

            # Validate package contents against YAML config
            is_contents_valid, contents_error = self.validate_package_contents(components, package_config)
            if not is_contents_valid:
                logger.error(f"Package contents validation failed: {contents_error}")
                self.notify_receivers(sender_config, 'Failed', f"Package contents validation failed: {contents_error}")
                self.mark_file_processed(
                    file_hash=file_hash,
                    file_name=package_config['filename'],
                    sender_id=sender_id,
                    method=method,
                    status='error',
                    error_message=contents_error
                )
                return False


            # Process components
            for component in components:
                df = self.process_package_component(component, package_config['components'][component['filename']])
                if df is None:
                    logger.error(f"Failed to process component {component['filename']}")
                    self.mark_file_processed(
                        file_hash=file_hash,
                        file_name=package_config['filename'],
                        sender_id=sender_id,
                        method=method,
                        status='error',
                        error_message=f"Failed to process component {component['filename']}"
                    )
                    return False
                if not self.save_processed_data(df, package_config['components'][component['filename']]):
                    logger.error(f"Failed to save component {component['filename']}")
                    self.mark_file_processed(
                        file_hash=file_hash,
                        file_name=package_config['filename'],
                        sender_id=sender_id,
                        method=method,
                        status='error',
                        error_message=f"Failed to save component {component['filename']}"
                    )
                    return False


            # Process successfully
            self.mark_file_processed(
                file_hash=file_hash,
                file_name=package_config['filename'],
                sender_id=sender_id,
                method=method,
                status='processed'
            )
            return True

        except Exception as e:
            logger.error(f"Error processing package data: {str(e)}")
            if 'file_hash' in locals():
                self.mark_file_processed(
                    file_hash=file_hash,
                    file_name=package_config['filename'],
                    sender_id=sender_id,
                    method=method,
                    status='error',
                    error_message=str(e)
                )
            return False

    def load_yaml_config(self, yaml_id: str) -> Dict[str, Any]:
        """Load YAML configuration from database."""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT config FROM yaml_configs WHERE id = %s",
                    (yaml_id,)
                )
                result = cursor.fetchone()
                if result:
                    return yaml.safe_load(result[0])
                return {}
        except Exception as e:
            logger.error(f"Error loading YAML config {yaml_id}: {str(e)}")
            return {}

    def download_file(self, config: Dict[str, Any], package_config: Dict[str, Any], sender_id: str) -> Optional[bytes]:
        """Download file from configured source (SFTP, Email, or API)"""
        try:
            if 'sftp' in config['configurations'] and 'sftp' in config['allowed_methods']:
                return self.process_sftp_data(config['configurations']['sftp'], package_config, sender_id)
            elif 'email' in config['configurations'] and 'email' in config['allowed_methods']:
                return self.process_email_data(config['configurations']['email'], package_config, sender_id)
            elif 'api' in config['configurations'] and 'api' in config['allowed_methods']:
                return self.process_api_data(config['configurations']['api'], package_config, sender_id)
            elif 'filesystem' in config['configurations'] and 'filesystem' in config['allowed_methods']:
                return self.process_filesystem_data(config['configurations']['filesystem'], package_config, sender_id)
            elif 'direct_upload' in config['configurations'] and 'direct_upload' in config['allowed_methods']:
                # Handle direct upload differently, assuming file_data is already available
                return package_config['file_data']  # Assuming file_data is passed in package_config
            else:
                logger.error("No valid data source configured")
                return None
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None

    @staticmethod
    def run_processor():
        """Main function to run the processor"""
        processor = DataProcessor()
        processor.setup_database()

        try:
            with processor.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id 
                    FROM yaml_files 
                    WHERE validation_status = 'valid' 
                    AND type = 'senders'
                """)

                configs = cursor.fetchall()
                for (yaml_id,) in configs:
                    processor.process_configuration(yaml_id)

        except Exception as e:
            logger.error(f"Error in main processor: {str(e)}")
        finally:
            if processor.db_connection:
                processor.db_connection.close()

    def setup_database(self, database_url=None):
        """Setup database connection with provided URL or environment variable."""
        from src.services import setup_database_connection
        self.db_connection = setup_database_connection(database_url)
        if self.db_connection is None:
            raise ValueError("No se pudo establecer la conexión con la base de datos")
        # Create necessary tables if they don't exist
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    id SERIAL PRIMARY KEY,
                    file_hash VARCHAR(64) NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    sender_id VARCHAR(50) NOT NULL,
                    processing_method VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id SERIAL PRIMARY KEY,
                    yaml_id VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    log_content TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    execution_id INTEGER REFERENCES execution_history(id),
                    type VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db_connection.commit()
        logger.info("Database connection established")

if __name__ == '__main__':
    DataProcessor.run_processor()