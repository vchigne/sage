"""Test runner for validar YAMLs de SAGE."""
import os
import sys
import logging
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Agregar el directorio src al path de Python
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from sage.schemas.catalog import CatalogSchema
from sage.schemas.package import PackageSchema
from sage.schemas.sender import SenderSchema

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def clean_database(processor):
    """Limpiar tablas de prueba"""
    with processor.db_connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE processed_files RESTART IDENTITY CASCADE")
        processor.db_connection.commit()

def load_yaml(file_path: str) -> Dict[str, Any]:
    """Cargar archivo YAML"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error cargando {file_path}: {str(e)}")
        return {}

def validate_yaml_structure(
    data: Dict[str, Any],
    yaml_type: str,
    file_path: str
) -> List[Tuple[str, str, bool]]:
    """
    Validar estructura del YAML y retornar resultados por sección
    Returns: List of (section, message, is_valid)
    """
    results = []
    logger.info(f"\nValidando archivo: {os.path.basename(file_path)}")
    logger.info("="*80 + "\n")

    try:
        if yaml_type == 'catalog':
            results.extend(_validate_catalog_sections(data))
        elif yaml_type == 'package':
            results.extend(_validate_package_sections(data))
        elif yaml_type == 'sender':
            results.extend(_validate_sender_sections(data))
    except Exception as e:
        results.append(('general', f"Error general: {str(e)}", False))

    return results

def _validate_catalog_sections(data: Dict[str, Any]) -> List[Tuple[str, str, bool]]:
    """Validar secciones de un catálogo"""
    results = []

    # Validar estructura básica
    if 'catalog' not in data:
        return [('root', "Falta clave 'catalog'", False)]

    catalog = data['catalog']

    # Validar campos requeridos
    logger.info("Validando campos principales:")
    for field in ['name', 'description', 'fields']:
        exists = field in catalog
        results.append(
            (field, f"Campo '{field}': {'presente' if exists else 'faltante'}", exists)
        )

    # Validar fields si existe
    if 'fields' in catalog:
        logger.info("\nValidando definición de campos:")
        for i, field in enumerate(catalog['fields']):
            field_results = _validate_catalog_field(field)
            results.extend((f"field[{i}].{section}", msg, valid) 
                         for section, msg, valid in field_results)

    # Validar validaciones
    logger.info("\nValidando reglas de validación:")
    if 'row_validation' in catalog:
        results.extend(_validate_validation_section(catalog['row_validation'], 'row'))

    if 'catalog_validation' in catalog:
        results.extend(_validate_validation_section(catalog['catalog_validation'], 'catalog'))

    return results

def _validate_catalog_field(field: Dict[str, Any]) -> List[Tuple[str, str, bool]]:
    """Validar un campo individual del catálogo"""
    results = []

    # Campos requeridos
    for required in ['name', 'type']:
        exists = required in field
        results.append(
            (required, f"'{required}': {'presente' if exists else 'faltante'}", exists)
        )

    # Validar tipo
    if 'type' in field:
        valid_type = field['type'] in CatalogSchema.FIELD_TYPES
        results.append(
            ('type', f"tipo '{field['type']}': {'válido' if valid_type else 'inválido'}", 
             valid_type)
        )

    # Validar otros atributos
    if 'length' in field:
        valid_length = isinstance(field['length'], int)
        results.append(
            ('length', f"length: {'válido' if valid_length else 'debe ser entero'}", 
             valid_length)
        )

    if 'required' in field:
        valid_required = isinstance(field['required'], bool)
        results.append(
            ('required', f"required: {'válido' if valid_required else 'debe ser booleano'}", 
             valid_required)
        )

    if 'unique' in field:
        valid_unique = isinstance(field['unique'], bool)
        results.append(
            ('unique', f"unique: {'válido' if valid_unique else 'debe ser booleano'}", 
             valid_unique)
        )

    return results

def _validate_validation_section(
    section: Dict[str, Any], 
    section_type: str
) -> List[Tuple[str, str, bool]]:
    """Validar una sección de validación"""
    results = []

    # Validar expression
    if 'validation_expression' in section:
        expr = section['validation_expression']
        valid_expr = isinstance(expr, str) and len(expr.strip()) > 0
        results.append(
            (f'{section_type}_validation.expression',
             f"expresión: {'válida' if valid_expr else 'inválida'}",
             valid_expr)
        )
    else:
        results.append(
            (f'{section_type}_validation.expression',
             "falta expresión de validación",
             False)
        )

    return results

def _validate_package_sections(data: Dict[str, Any]) -> List[Tuple[str, str, bool]]:
    """Validar secciones de un paquete"""
    results = []

    # Validar estructura básica
    if 'package' not in data:
        return [('root', "Falta clave 'package'", False)]

    package = data['package']

    # Validar campos requeridos
    logger.info("Validando campos principales:")
    for field in ['name', 'description', 'methods', 'catalogs']:
        exists = field in package
        results.append(
            (field, f"Campo '{field}': {'presente' if exists else 'faltante'}", exists)
        )

    # Validar métodos
    logger.info("\nValidando configuración de métodos:")
    if 'methods' in package:
        if 'file_format' in package['methods']:
            file_format = package['methods']['file_format']

            # Validar tipo de archivo
            if 'type' in file_format:
                valid_type = file_format['type'] in PackageSchema.ALLOWED_FILE_TYPES
                results.append(
                    ('methods.file_format.type',
                     f"tipo '{file_format['type']}': {'válido' if valid_type else 'inválido'}",
                     valid_type)
                )

            # Validar patrón de nombre
            if 'filename_pattern' in file_format:
                valid_pattern = isinstance(file_format['filename_pattern'], str)
                results.append(
                    ('methods.file_format.pattern',
                     f"patrón: {'válido' if valid_pattern else 'debe ser texto'}",
                     valid_pattern)
                )

    # Validar catalogs y destination
    logger.info("\nValidando referencias y destino:")
    if 'catalogs' in package:
        valid_catalogs = isinstance(package['catalogs'], list)
        results.append(
            ('catalogs',
             f"catálogos: {'válido' if valid_catalogs else 'debe ser lista'}",
             valid_catalogs)
        )

        if valid_catalogs:
            for i, catalog in enumerate(package['catalogs']):
                if 'path' not in catalog:
                    results.append(
                        (f'catalogs[{i}]',
                         "falta atributo 'path'",
                         False)
                    )

    if 'destination' in package:
        dest = package['destination']
        if not isinstance(dest.get('enabled'), bool):
            results.append(
                ('destination.enabled',
                 "enabled debe ser booleano",
                 False)
            )

        if 'database_connection' in dest:
            db = dest['database_connection']
            valid_type = db.get('type') in ['postgresql']
            results.append(
                ('destination.database.type',
                 f"tipo de base de datos: {'válido' if valid_type else 'no soportado'}",
                 valid_type)
            )

        if 'insertion_method' in dest:
            valid_method = dest['insertion_method'] in ['insert', 'upsert', 'replace']
            results.append(
                ('destination.insertion_method',
                 f"método de inserción: {'válido' if valid_method else 'no soportado'}",
                 valid_method)
            )

    return results

def _validate_sender_sections(data: Dict[str, Any]) -> List[Tuple[str, str, bool]]:
    """Validar secciones de un emisor"""
    results = []

    # Validar estructura básica
    if 'senders' not in data:
        return [('root', "Falta clave 'senders'", False)]

    senders = data['senders']

    # Validar campos principales
    logger.info("Validando campos principales:")
    for field in ['corporate_owner', 'data_receivers', 'senders_list']:
        exists = field in senders
        results.append(
            (field, f"Campo '{field}': {'presente' if exists else 'faltante'}", exists)
        )

    # Validar data_receivers
    logger.info("\nValidando receptores de datos:")
    if 'data_receivers' in senders:
        receivers = senders['data_receivers']
        if isinstance(receivers, list):
            for i, receiver in enumerate(receivers):
                for field in ['name', 'email']:
                    exists = field in receiver
                    results.append(
                        (f'data_receivers[{i}].{field}',
                         f"'{field}': {'presente' if exists else 'faltante'}",
                         exists)
                    )

    # Validar senders_list
    logger.info("\nValidando lista de emisores:")
    if 'senders_list' in senders:
        senders_list = senders['senders_list']
        if isinstance(senders_list, list):
            for i, sender in enumerate(senders_list):
                results.extend(_validate_sender_entry(sender, i))

    return results

def _validate_sender_entry(
    sender: Dict[str, Any], 
    index: int
) -> List[Tuple[str, str, bool]]:
    """Validar una entrada individual de sender"""
    results = []

    # Validar campos requeridos
    for field in ['sender_id', 'name', 'responsible_person', 'allowed_methods']:
        exists = field in sender
        results.append(
            (f'senders_list[{index}].{field}',
             f"'{field}': {'presente' if exists else 'faltante'}",
             exists)
        )

    # Validar allowed_methods
    if 'allowed_methods' in sender:
        valid_methods = all(method in ['sftp', 'email', 'api'] 
                          for method in sender['allowed_methods'])
        results.append(
            (f'senders_list[{index}].allowed_methods',
             f"métodos: {'válidos' if valid_methods else 'algunos métodos inválidos'}",
             valid_methods)
        )

    # Validar responsible_person
    if 'responsible_person' in sender:
        person = sender['responsible_person']
        for field in ['name', 'email', 'phone']:
            exists = field in person
            results.append(
                (f'senders_list[{index}].responsible_person.{field}',
                 f"'{field}': {'presente' if exists else 'faltante'}",
                 exists)
            )

    # Validar configuraciones de método
    if 'configurations' in sender:
        config = sender['configurations']

        # Validar SFTP
        if 'sftp' in config:
            sftp = config['sftp']
            for field in ['host', 'port', 'username', 'password', 'directory']:
                if field not in sftp:
                    results.append(
                        (f'senders_list[{index}].configurations.sftp.{field}',
                         f"falta configuración '{field}'",
                         False)
                    )
                elif field == 'port' and not isinstance(sftp[field], int):
                    results.append(
                        (f'senders_list[{index}].configurations.sftp.{field}',
                         "puerto debe ser número",
                         False)
                    )

        # Validar Email
        if 'email' in config:
            email = config['email']
            for field in ['allowed_senders', 'receiving_email', 'subject_format']:
                if field not in email:
                    results.append(
                        (f'senders_list[{index}].configurations.email.{field}',
                         f"falta configuración '{field}'",
                         False)
                    )

        # Validar API
        if 'api' in config:
            api = config['api']
            for field in ['endpoint', 'api_key', 'method']:
                if field not in api:
                    results.append(
                        (f'senders_list[{index}].configurations.api.{field}',
                         f"falta configuración '{field}'",
                         False)
                    )
                elif field == 'method' and api[field] not in ['POST', 'PUT']:
                    results.append(
                        (f'senders_list[{index}].configurations.api.{field}',
                         "método debe ser POST o PUT",
                         False)
                    )

    return results

def print_validation_results(results: List[Tuple[str, str, bool]]):
    """Imprimir resultados de validación de forma organizada"""
    valid_count = sum(1 for _, _, valid in results if valid)
    total = len(results)

    logger.info(f"\nResultados de validación ({valid_count}/{total} válidos):")
    logger.info("-" * 80)

    # Agrupar resultados por sección principal
    sections = {}
    for section, message, is_valid in results:
        main_section = section.split('.')[0]
        if main_section not in sections:
            sections[main_section] = []
        sections[main_section].append((section, message, is_valid))

    # Imprimir resultados por sección
    for section_name, section_results in sections.items():
        logger.info(f"\nSección: {section_name}")
        logger.info("-" * 40)
        for section, message, is_valid in section_results:
            status = "✅" if is_valid else "❌"
            logger.info(f"{status} {section}: {message}")

    logger.info("\n" + "="*80)

def main():
    """Función principal de pruebas"""
    logger.info("\nVALIDACIÓN DE ARCHIVOS YAML")
    logger.info("="*80)

    test_files = {
        'valid': {
            'catalog': 'tests/test_data/valid/catalog.yaml',
            'package': 'tests/test_data/valid/package.yaml',
            'sender': 'tests/test_data/valid/sender.yaml'
        },
        'invalid': {
            'catalog': [
                'tests/test_data/invalid/catalog_missing_fields.yaml',
                'tests/test_data/invalid/catalog_invalid_types.yaml',
                'tests/test_data/invalid/catalog_invalid_validation.yaml'
            ],
            'package': [
                'tests/test_data/invalid/package_invalid.yaml',
                'tests/test_data/invalid/package_invalid_destination.yaml'
            ],
            'sender': [
                'tests/test_data/invalid/sender_invalid.yaml',
                'tests/test_data/invalid/sender_invalid_methods.yaml'
            ]
        }
    }

    logger.info("\nValidando archivos correctos:")
    for yaml_type, file_path in test_files['valid'].items():
        data = load_yaml(file_path)
        if data:
            results = validate_yaml_structure(data, yaml_type, file_path)
            print_validation_results(results)

    logger.info("\nValidando archivos con errores:")
    for yaml_type, file_paths in test_files['invalid'].items():
        for file_path in file_paths:
            data = load_yaml(file_path)
            if data:
                results = validate_yaml_structure(data, yaml_type, file_path)
                print_validation_results(results)

if __name__ == '__main__':
    main()
from src.services.data_processor import DataProcessor