"""Validador de archivos ZIP que contienen Excel y CSV."""
import os
import sys
import zipfile
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
import psycopg2

# Agregar directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tests.validate_productos import (
    load_yaml,
    validate_excel_structure,
    validate_package_rules,
    validate_sender_permissions,
    validate_package_data
)

# Use environment variables for database connection
db_connection = psycopg2.connect(os.environ['DATABASE_URL'])


def get_zip_modification_time(zip_path: str) -> datetime:
    """
    Obtener la fecha de última modificación del archivo ZIP.
    """
    zip_stat = os.stat(zip_path)
    return datetime.fromtimestamp(zip_stat.st_mtime)

def is_duplicate_package(zip_path: str, package_name: str) -> bool:
    """
    Verificar si un paquete ya fue procesado basándose en:
    - Nombre del paquete
    - Fecha de última modificación del ZIP

    Un paquete se considera duplicado si:
    1. Existe un registro con el mismo nombre
    2. La fecha de modificación es igual o anterior al último procesado
    """
    with db_connection.cursor() as cursor:
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
        current_mod_time = get_zip_modification_time(zip_path)

        # Es duplicado si la fecha de modificación es igual o anterior
        return current_mod_time <= last_processed_mod_time

def register_processed_package(zip_path: str, package_name: str):
    """
    Registrar un paquete como procesado incluyendo su fecha de modificación.
    """
    mod_time = get_zip_modification_time(zip_path)

    with db_connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO processed_packages 
            (package_name, processed_at, zip_modified_at)
            VALUES (%s, NOW(), %s)
        """, (package_name, mod_time))
        db_connection.commit()

def extract_zip(zip_path: str, extract_dir: str) -> List[str]:
    """
    Extraer archivos del ZIP y retornar lista de archivos.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
        return zip_ref.namelist()

def get_file_type(file_path: str) -> str:
    """Determinar tipo de archivo basado en extensión."""
    ext = file_path.lower().split('.')[-1]
    if ext in ['xlsx', 'xls']:
        return 'XLSX'
    elif ext == 'csv':
        return 'CSV'
    return 'UNKNOWN'

def load_data_file(file_path: str) -> pd.DataFrame:
    """Cargar archivo Excel o CSV en DataFrame."""
    file_type = get_file_type(file_path)
    if file_type == 'XLSX':
        return pd.read_excel(file_path)
    elif file_type == 'CSV':
        return pd.read_csv(file_path)
    raise ValueError(f"Tipo de archivo no soportado: {file_type}")

def match_filename_pattern(filename: str, pattern: str) -> bool:
    """
    Verificar si un nombre de archivo coincide con el patrón esperado.
    Convierte el patrón con placeholders en una expresión regular.
    """
    import re
    # Reemplazar placeholders con patrones regex
    pattern_regex = pattern.replace(
        '{sender_id}', r'[A-Z0-9]+').replace(
        '{date}', r'\d{8}')
    return bool(re.match(pattern_regex, filename))

def validate_zip_package(
    zip_path: str,
    package_yaml: str,
    sender_yaml: str,
    catalogs_dir: str
) -> List[str]:
    """
    Validar un paquete ZIP que contiene múltiples archivos.

    Args:
        zip_path: Ruta al archivo ZIP
        package_yaml: Ruta al YAML del paquete
        sender_yaml: Ruta al YAML del emisor
        catalogs_dir: Directorio con YAMLs de catálogos
    """
    errors = []

    try:
        # Cargar YAMLs
        package = load_yaml(package_yaml)
        sender = load_yaml(sender_yaml)

        # Verificar si es un paquete duplicado
        if is_duplicate_package(zip_path, package['package']['name']):
            return ["Paquete duplicado: Ya existe una versión igual o más reciente procesada"]

        # Validar permisos del emisor
        sender_errors = validate_sender_permissions(
            sender, 
            package['package']['name']
        )
        if sender_errors:
            return sender_errors

        # Validar reglas del paquete
        package_errors = validate_package_rules(zip_path, package)
        if package_errors:
            return package_errors

        # Crear directorio temporal para extracción
        extract_dir = 'temp_extract'
        os.makedirs(extract_dir, exist_ok=True)

        # Extraer y validar archivos
        files = extract_zip(zip_path, extract_dir)
        print(f"\nValidando {len(files)} archivos en el ZIP:")

        # Validar cada archivo contra su catálogo
        for catalog_config in package['package']['catalogs']:
            catalog_path = os.path.join(catalogs_dir, catalog_config['path'])
            catalog = load_yaml(catalog_path)

            # Buscar archivo correspondiente usando el patrón
            filename_pattern = catalog['catalog']['file_format']['filename_pattern']
            matching_files = [
                f for f in files 
                if match_filename_pattern(f, filename_pattern)
            ]

            if not matching_files:
                errors.append(
                    f"No se encontró archivo para catálogo: {catalog['catalog']['name']}"
                )
                continue

            # Validar cada archivo que coincida
            for file_path in matching_files:
                print(f"\nValidando archivo: {file_path}")
                full_path = os.path.join(extract_dir, file_path)

                try:
                    # Cargar y validar datos
                    df = load_data_file(full_path)
                    print(f"Forma del DataFrame: {df.shape}")

                    # Imprimir primeras filas para depuración
                    print("\nPrimeras filas del archivo:")
                    print(df.head())

                    # Validar estructura
                    validation_errors = validate_excel_structure(df, catalog)
                    if validation_errors:
                        errors.extend([
                            f"Error en {file_path}: {error}" 
                            for error in validation_errors
                        ])
                        continue

                    # Validar reglas del paquete sobre los datos
                    package_errors = validate_package_data(df, package)
                    if package_errors:
                        errors.extend([
                            f"Error en {file_path}: {error}"
                            for error in package_errors
                        ])
                        continue

                    print(f"✅ Archivo {file_path} válido")

                except Exception as e:
                    errors.append(f"Error procesando {file_path}: {str(e)}")

        # Si todo es válido, registrar el paquete como procesado
        register_processed_package(zip_path, package['package']['name'])

        return errors

    except Exception as e:
        return [f"Error en validación: {str(e)}"]

    finally:
        # Limpiar archivos temporales
        if os.path.exists('temp_extract'):
            import shutil
            shutil.rmtree('temp_extract')

def main():
    """Función principal de prueba."""
    # Configurar archivos de prueba
    today = datetime.now().strftime('%Y%m%d')
    sender_id = 'ALC001'

    test_files = {
        'zip_mixed': {
            'file': f'tests/data/zip/{sender_id}-{today}-PAQUETE_MIXTO.zip',
            'package': 'tests/test_data/valid/test_package.yaml',
            'sender': 'tests/test_data/valid/test_sender.yaml'
        }
    }

    catalogs_dir = 'tests/test_data/valid/catalogs'

    print("\nValidando paquete ZIP con archivos mixtos:")
    print("=" * 50)
    errors = validate_zip_package(
        test_files['zip_mixed']['file'],
        test_files['zip_mixed']['package'],
        test_files['zip_mixed']['sender'],
        catalogs_dir
    )

    if errors:
        print("\nErrores encontrados:")
        for error in errors:
            print(f"❌ {error}")
    else:
        print("✅ Paquete ZIP válido")

    # Close the database connection
    if db_connection.is_connected():
        db_connection.close()

if __name__ == '__main__':
    main()