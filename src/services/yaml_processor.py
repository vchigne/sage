import os
import yaml
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import imaplib
import email
import pysftp
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SourceType(Enum):
    EMAIL = "email"
    SFTP = "sftp"
    LOCAL = "local"

class YAMLProcessor:
    def __init__(self):
        self.db_connection = None  # Se inicializará en setup_database

    def setup_database(self):
        """Configura la conexión a la base de datos"""
        import psycopg2
        self.db_connection = psycopg2.connect(os.environ['DATABASE_URL'])

    def process_email(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Procesa archivos YAML recibidos por email"""
        try:
            mail = imaplib.IMAP4_SSL(config['host'])
            mail.login(config['username'], config['password'])
            mail.select('inbox')

            # Buscar emails según el formato de asunto configurado
            search_criteria = f'SUBJECT "{config["subject_format"]}"'
            _, message_numbers = mail.search(None, search_criteria)

            yaml_files = []
            for num in message_numbers[0].split():
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)

                # Procesar adjuntos
                for part in message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    if filename and (filename.endswith('.yaml') or filename.endswith('.yml')):
                        content = part.get_payload(decode=True)
                        if isinstance(content, bytes):
                            content = content.decode('utf-8')
                        yaml_files.append({
                            'name': filename,
                            'content': content,
                            'source': SourceType.EMAIL.value,
                            'metadata': {
                                'from': message['from'],
                                'subject': message['subject'],
                                'date': message['date']
                            }
                        })

            return yaml_files
        except Exception as e:
            logger.error(f"Error processing email: {str(e)}")
            return []

    def process_sftp(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Procesa archivos YAML desde un servidor SFTP"""
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None  # TODO: Implementar verificación de hostkeys

            with pysftp.Connection(
                config['host'],
                username=config['username'],
                password=config['password'],
                cnopts=cnopts
            ) as sftp:
                yaml_files = []

                # Listar archivos en el directorio configurado
                for entry in sftp.listdir_attr(config['directory']):
                    filename = entry.filename
                    if filename.endswith('.yaml') or filename.endswith('.yml'):
                        remote_path = f"{config['directory']}/{filename}"
                        with sftp.open(remote_path) as f:
                            content = f.read().decode()
                            yaml_files.append({
                                'name': filename,
                                'content': content,
                                'source': SourceType.SFTP.value,
                                'metadata': {
                                    'modified_time': datetime.fromtimestamp(entry.st_mtime).isoformat(),
                                    'size': entry.st_size
                                }
                            })

                return yaml_files
        except Exception as e:
            logger.error(f"Error processing SFTP: {str(e)}")
            return []

    def validate_yaml(self, content: str, yaml_type: str) -> tuple[bool, Optional[str]]:
        """Valida el contenido del archivo YAML según su tipo"""
        try:
            # Parsear el YAML
            data = yaml.safe_load(content)

            # Validaciones específicas según el tipo
            if yaml_type == 'senders':
                required_fields = ['senders', 'corporate_owner', 'data_receivers']
                for field in required_fields:
                    if field not in data:
                        return False, f"Campo requerido faltante: {field}"

            elif yaml_type == 'catalogs':
                if not isinstance(data, dict):
                    return False, "El archivo debe contener un diccionario válido"

            elif yaml_type == 'packages':
                if not isinstance(data, dict) or 'package' not in data:
                    return False, "El archivo debe contener una definición de paquete"

            return True, None
        except yaml.YAMLError as e:
            return False, f"Error de sintaxis YAML: {str(e)}"
        except Exception as e:
            return False, f"Error de validación: {str(e)}"

    def save_to_database(self, yaml_file: Dict[str, Any], installation_id: str) -> bool:
        """Guarda el archivo YAML en la base de datos"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO yaml_files (
                        name, content, type, installation_id, 
                        validation_status, uploaded_by, upload_method,
                        metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    yaml_file['name'],
                    yaml_file['content'],
                    self._determine_yaml_type(yaml_file['name']),
                    installation_id,
                    'valid',
                    'system',
                    yaml_file['source'],
                    json.dumps(yaml_file['metadata'])
                ))
                self.db_connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            self.db_connection.rollback()
            return False

    def _determine_yaml_type(self, filename: str) -> str:
        """Determina el tipo de archivo YAML basado en su nombre"""
        filename = filename.lower()
        if 'sender' in filename:
            return 'senders'
        elif 'catalog' in filename:
            return 'catalogs'
        elif 'package' in filename:
            return 'packages'
        return 'unknown'

    def process_all_sources(self, config: Dict[str, Any]):
        """Procesa todas las fuentes configuradas"""
        try:
            self.setup_database()

            # Procesar email si está configurado
            if 'email' in config:
                yaml_files = self.process_email(config['email'])
                for yaml_file in yaml_files:
                    is_valid, error = self.validate_yaml(
                        yaml_file['content'],
                        self._determine_yaml_type(yaml_file['name'])
                    )
                    if is_valid:
                        self.save_to_database(yaml_file, config['installation_id'])
                    else:
                        logger.error(f"Validation error in {yaml_file['name']}: {error}")

            # Procesar SFTP si está configurado
            if 'sftp' in config:
                yaml_files = self.process_sftp(config['sftp'])
                for yaml_file in yaml_files:
                    is_valid, error = self.validate_yaml(
                        yaml_file['content'],
                        self._determine_yaml_type(yaml_file['name'])
                    )
                    if is_valid:
                        self.save_to_database(yaml_file, config['installation_id'])
                    else:
                        logger.error(f"Validation error in {yaml_file['name']}: {error}")

        except Exception as e:
            logger.error(f"Error in process_all_sources: {str(e)}")
        finally:
            if self.db_connection:
                self.db_connection.close()

def run_processor():
    """Función principal para ejecutar el procesador"""
    processor = YAMLProcessor()

    # TODO: Obtener la configuración de la base de datos
    config = {
        'installation_id': 'example_installation',
        'email': {
            'host': 'imap.example.com',
            'username': 'user@example.com',
            'password': 'password',
            'subject_format': 'YAML Submission'
        },
        'sftp': {
            'host': 'sftp.example.com',
            'username': 'user',
            'password': 'password',
            'directory': '/uploads'
        }
    }

    processor.process_all_sources(config)

if __name__ == '__main__':
    run_processor()