"""Package processor for SAGE."""
import os
import zipfile
import pandas as pd
from typing import Dict, Any, List, Tuple
from datetime import datetime
import psycopg2
from ..core.processor import SageProcessor
from ..core.yaml_loader import YAMLLoader
from ..utils.exceptions import ProcessingError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PackageProcessor(SageProcessor):
    """Processor class for package validation and processing."""

    SUPPORTED_FORMATS = {'CSV', 'XLSX', 'ZIP'}

    def __init__(self):
        """Initialize the package processor."""
        super().__init__()
        self.db_connection = psycopg2.connect(os.environ['DATABASE_URL'])

    def load_yaml_config(self, yaml_path: str) -> Dict[str, Any]:
        """
        Load and validate a YAML configuration file.

        Args:
            yaml_path: Path to the YAML file

        Returns:
            Dict containing the YAML configuration

        Raises:
            ProcessingError: If YAML loading fails
        """
        try:
            loader = YAMLLoader()
            return loader.load_yaml(yaml_path)
        except Exception as e:
            error_msg = f"Error loading YAML config {yaml_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ProcessingError(error_msg)

    def get_zip_modification_time(self, zip_path: str) -> datetime:
        """Get the last modification time of the ZIP file."""
        zip_stat = os.stat(zip_path)
        return datetime.fromtimestamp(zip_stat.st_mtime)

    def is_duplicate_package(self, zip_path: str, package_name: str) -> bool:
        """
        Check if a package has already been processed based on:
        - Package name
        - ZIP file last modification time

        A package is considered duplicate if:
        1. A record exists with the same name
        2. The modification time is equal to or older than the last processed
        """
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT zip_modified_at 
                FROM processed_packages 
                WHERE package_name = %s
                ORDER BY processed_at DESC
                LIMIT 1
            """, (package_name,))
            result = cursor.fetchone()

            if not result:
                return False

            last_processed_mod_time = result[0]
            current_mod_time = self.get_zip_modification_time(zip_path)

            # It's a duplicate if modification time is equal or older
            return current_mod_time <= last_processed_mod_time

    def register_processed_package(self, zip_path: str, package_name: str):
        """Register a package as processed including its modification time."""
        mod_time = self.get_zip_modification_time(zip_path)

        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO processed_packages 
                (package_name, processed_at, zip_modified_at)
                VALUES (%s, NOW(), %s)
            """, (package_name, mod_time))
            self.db_connection.commit()

    def validate_file_format(self, file_path: str, expected_format: str) -> bool:
        """
        Validate if the file matches the expected format.

        Args:
            file_path: Path to the file
            expected_format: Expected format from package YAML ('CSV', 'XLSX', 'ZIP')

        Returns:
            bool: True if format matches, False otherwise
        """
        file_ext = os.path.splitext(file_path)[1].upper().lstrip('.')

        if expected_format == 'CSV' and file_ext == 'CSV':
            return True
        elif expected_format == 'XLSX' and file_ext in ['XLS', 'XLSX']:
            return True
        elif expected_format == 'ZIP' and file_ext == 'ZIP':
            return True

        return False

    def read_data_file(self, file_path: str) -> pd.DataFrame:
        """
        Read data from file based on its format.

        Args:
            file_path: Path to the data file

        Returns:
            pd.DataFrame: Data from the file

        Raises:
            ProcessingError: If file cannot be read
        """
        try:
            # Get file format from extension
            file_ext = os.path.splitext(file_path)[1].upper().lstrip('.')

            if file_ext == 'CSV':
                return pd.read_csv(file_path)
            elif file_ext in ['XLS', 'XLSX']:
                return pd.read_excel(file_path)
            else:
                raise ProcessingError(f"Formato de archivo no soportado: {file_ext}")
        except Exception as e:
            error_msg = f"Error al leer el archivo {file_path}: {str(e)}"
            logger.error(error_msg)
            raise ProcessingError(error_msg)

    def extract_zip(self, zip_path: str, extract_dir: str) -> List[str]:
        """
        Extract files from ZIP and return list of files.

        Args:
            zip_path: Path to the ZIP file
            extract_dir: Directory to extract files to

        Returns:
            List[str]: List of extracted files

        Raises:
            ProcessingError: If ZIP extraction fails
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                return zip_ref.namelist()
        except Exception as e:
            error_msg = f"Error al extraer el archivo ZIP {zip_path}: {str(e)}"
            logger.error(error_msg)
            raise ProcessingError(error_msg)

    def get_catalogs_from_config(self, package_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get catalogs configuration from package config.
        Supports both 'catalogs' and legacy 'components' structure.
        """
        pkg_config = package_config.get('package', {})

        # Try new 'catalogs' structure first
        if 'catalogs' in pkg_config:
            return pkg_config['catalogs']

        # Fall back to legacy 'components' structure
        if 'components' in pkg_config:
            components = []
            for name, config in pkg_config['components'].items():
                component = config.copy()
                # Remove extension from component name for catalog lookup
                base_name = os.path.splitext(name)[0]
                component['name'] = base_name
                component['path'] = f"{base_name}.yaml"
                components.append(component)
            return components

        return []

    def process_data(self, data_file: str, yaml_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Process data file based on catalog configuration."""
        self.logger.info(f"Processing data file: {data_file}")
        self.logger.info("Catalog configuration:")
        self.logger.info(str(yaml_config))

        try:
            # Read data file
            df = self.read_data_file(data_file)
            self.logger.info(f"Data file loaded successfully, shape: {df.shape}")

            # Process using parent class method
            return super().process_data(df, yaml_config)
        except Exception as e:
            error_msg = f"Error processing data file {data_file}: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg]

    def process_package(self,
                       data_file: str,
                       package_yaml: str,
                       catalogs_dir: str,
                       force: bool = False) -> Tuple[bool, List[str]]:
        """Process a package file according to its configuration."""
        errors = []
        extract_dir = 'temp_extract'

        try:
            # Load package configuration
            logger.info(f"Cargando configuración del paquete desde {package_yaml}")
            package_config = self.load_yaml_config(package_yaml)

            if not package_config or 'package' not in package_config:
                error_msg = "Configuración de paquete inválida: Falta la sección 'package'"
                logger.error(error_msg)
                return False, [error_msg]

            # Validate file format configuration
            if ('methods' not in package_config['package'] or 
                'file_format' not in package_config['package']['methods'] or
                'type' not in package_config['package']['methods']['file_format']):
                error_msg = "Configuración de formato de archivo no encontrada en el YAML del paquete"
                logger.error(error_msg)
                return False, [error_msg]

            expected_format = package_config['package']['methods']['file_format']['type'].upper()

            if expected_format not in self.SUPPORTED_FORMATS:
                error_msg = f"Formato de archivo no soportado: {expected_format}"
                logger.error(error_msg)
                return False, [error_msg]

            # Validate file format matches configuration
            if not self.validate_file_format(data_file, expected_format):
                error_msg = (f"Formato de archivo incorrecto. Se esperaba {expected_format} pero "
                           f"se recibió un archivo {os.path.splitext(data_file)[1].upper()}")
                logger.error(error_msg)
                return False, [error_msg]

            # Process based on file type
            if expected_format == 'ZIP':
                os.makedirs(extract_dir, exist_ok=True)
                try:
                    files = self.extract_zip(data_file, extract_dir)
                    logger.info(f"Extraídos {len(files)} archivos del ZIP")
                except Exception as e:
                    error_msg = f"Error al extraer el archivo ZIP: {str(e)}"
                    logger.error(error_msg)
                    return False, [error_msg]
            else:
                files = [data_file]
                logger.info("Procesando archivo individual")

            # Process each file with appropriate catalogs
            catalogs = self.get_catalogs_from_config(package_config)
            if not catalogs:
                error_msg = "No se encontraron catálogos definidos en la configuración del paquete"
                logger.error(error_msg)
                return False, [error_msg]

            for catalog_config in catalogs:
                catalog_path = os.path.join(catalogs_dir, catalog_config.get('path', ''))

                if not os.path.isfile(catalog_path):
                    error_msg = f"Archivo de catálogo no encontrado: {catalog_path}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

                try:
                    catalog = self.load_yaml_config(catalog_path)
                    for file_path in files:
                        full_path = os.path.join(extract_dir, file_path) if expected_format == 'ZIP' else file_path
                        success, validation_errors = self.process_data(
                            data_file=full_path,
                            yaml_config=catalog['catalog']
                        )
                        if not success:
                            errors.extend(validation_errors)

                except Exception as e:
                    error_msg = f"Error al procesar el archivo {file_path}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return len(errors) == 0, errors

        except Exception as e:
            error_msg = f"Error al procesar el paquete: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
        finally:
            if os.path.exists(extract_dir):
                import shutil
                shutil.rmtree(extract_dir)