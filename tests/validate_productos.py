"""Validador de archivo de productos contra YAMLs."""
import os
import sys
import yaml
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def load_yaml(file_path: str) -> dict:
    """Cargar un archivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_field_value(df: pd.DataFrame, field: Dict[str, Any]) -> List[str]:
    """
    Validar un campo específico del DataFrame.

    Args:
        df: DataFrame con los datos
        field: Diccionario con la configuración del campo

    Returns:
        List[str]: Lista de errores encontrados
    """
    errors = []
    field_name = field['name']

    # Verificar si el campo existe
    if field_name not in df.columns:
        if field.get('required', False):
            errors.append(f"Campo requerido faltante: {field_name}")
        return errors

    column = df[field_name]

    # Validar nulos
    if field.get('required', False) and column.isnull().any():
        null_count = column.isnull().sum()
        errors.append(f"Campo {field_name}: {null_count} valores nulos encontrados")

    # Validar tipo de dato
    if field['type'] == 'text':
        if not column.dtype == 'object':
            errors.append(f"Campo {field_name}: tipo inválido, debe ser texto")
        if 'length' in field:
            mask = column.astype(str).str.len() > field['length']
            if mask.any():
                invalid_count = mask.sum()
                errors.append(f"Campo {field_name}: {invalid_count} valores exceden longitud máxima {field['length']}")

    elif field['type'] == 'number':
        if not pd.api.types.is_numeric_dtype(column):
            errors.append(f"Campo {field_name}: tipo inválido, debe ser número")
        if 'decimals' in field:
            decimal_places = (column.astype(str)
                            .str.extract(r'\.(\d+)')[0]
                            .str.len()
                            .fillna(0))
            mask = decimal_places > field['decimals']
            if mask.any():
                invalid_count = mask.sum()
                errors.append(f"Campo {field_name}: {invalid_count} valores exceden decimales permitidos {field['decimals']}")

    elif field['type'] == 'date':
        try:
            pd.to_datetime(column)
        except:
            errors.append(f"Campo {field_name}: tipo inválido, debe ser fecha")

    # Validar unicidad si es requerida
    if field.get('unique', False):
        duplicates = column.duplicated()
        if duplicates.any():
            duplicate_count = duplicates.sum()
            errors.append(f"Campo {field_name}: {duplicate_count} valores duplicados encontrados")

    # Validar regla específica del campo
    if 'validation_expression' in field:
        try:
            # Crear un diccionario con el contexto para eval
            eval_context = {"df": df, "pd": pd}
            # Evaluar la expresión usando el contexto
            expr = field['validation_expression']
            valid = eval(expr, eval_context)

            if not isinstance(valid, (bool, pd.Series)):
                errors.append(f"Campo {field_name}: regla de validación debe retornar bool o Series")
            elif isinstance(valid, pd.Series) and not valid.all():
                invalid_count = (~valid).sum()
                errors.append(f"Campo {field_name}: {invalid_count} registros no cumplen regla de validación")
            elif isinstance(valid, bool) and not valid:
                errors.append(f"Campo {field_name}: no cumple regla de validación")
        except Exception as e:
            errors.append(f"Error evaluando regla de {field_name}: {str(e)}")

    return errors

def validate_excel_structure(df: pd.DataFrame, catalog: dict) -> List[str]:
    """Validar estructura del Excel contra el catálogo."""
    errors = []
    catalog_fields = catalog['catalog']['fields']

    print("\nValidando estructura del DataFrame:")
    print(f"Dimensiones: {df.shape}")
    print(f"Columnas: {df.columns.tolist()}")

    # Validar cada campo
    for field in catalog_fields:
        field_errors = validate_field_value(df, field)
        errors.extend(field_errors)

    # Validar reglas a nivel de fila
    if 'row_validation' in catalog['catalog']:
        try:
            expr = catalog['catalog']['row_validation']['validation_expression']
            # Crear un diccionario con el contexto para eval
            eval_context = {"df": df, "pd": pd}
            # Evaluar la expresión usando el contexto
            valid = eval(expr, eval_context)
            if not isinstance(valid, pd.Series):
                errors.append("Validación de fila debe retornar una Series")
            else:
                invalid_rows = (~valid).sum()
                if invalid_rows > 0:
                    errors.append(f"Validación de fila fallida en {invalid_rows} filas")
        except Exception as e:
            errors.append(f"Error en validación de fila: {str(e)}")

    # Validar reglas a nivel de catálogo
    if 'catalog_validation' in catalog['catalog']:
        try:
            # Evaluar expresión de validación
            expr = catalog['catalog']['catalog_validation']['validation_expression']
            print(f"\nEvaluando expresión de catálogo: {expr}")

            # Crear un diccionario con el contexto para eval
            eval_context = {"df": df, "pd": pd}
            # Evaluar la expresión usando el contexto
            valid = eval(expr, eval_context)

            print(f"Resultado de validación: {valid}")

            if not isinstance(valid, bool):
                errors.append("Validación de catálogo debe retornar un booleano")
            elif not valid:
                errors.append("Validación de catálogo fallida")
        except Exception as e:
            errors.append(f"Error en validación de catálogo: {str(e)}")

    return errors

def validate_package_data(df: pd.DataFrame, package: dict) -> List[str]:
    """Validar reglas de datos del paquete."""
    errors = []

    if 'package_validation' in package['package']:
        for rule in package['package']['package_validation']['validation_rules']:
            try:
                # Crear un diccionario con el contexto para eval
                eval_context = {"df": df, "pd": pd}
                # Evaluar la expresión usando el contexto
                valid = eval(rule['validation_expression'], eval_context)
                if not valid:
                    errors.append(f"Regla de validación fallida: {rule['name']}")
            except Exception as e:
                errors.append(f"Error evaluando regla {rule['name']}: {str(e)}")

    return errors

def validate_package_rules(file_path: str, package: dict) -> List[str]:
    """Validar reglas del paquete."""
    errors = []

    # Validar tipo de archivo
    file_type = package['package']['methods']['file_format']['type']
    if not file_path.upper().endswith(file_type):
        errors.append(f"Tipo de archivo incorrecto. Esperado: {file_type}")

    # Validar patrón de nombre
    filename_pattern = package['package']['methods']['file_format']['filename_pattern']
    filename = os.path.basename(file_path)

    # Extraer variables del patrón
    pattern_vars = {
        'sender_id': r'[A-Z0-9]+',
        'date': r'\d{8}|\d{4}-\d{2}-\d{2}'
    }

    # Construir regex del patrón
    import re
    pattern_regex = filename_pattern
    for var, regex in pattern_vars.items():
        pattern_regex = pattern_regex.replace('{' + var + '}', f'({regex})')

    if not re.match(pattern_regex, filename):
        errors.append(f"Nombre de archivo no cumple patrón: {filename_pattern}")

    return errors

def validate_sender_permissions(sender: dict, package_name: str) -> List[str]:
    """Validar permisos del emisor."""
    errors = []

    # Verificar si el paquete está autorizado
    authorized_packages = [p['name'] for p in sender['senders']['senders_list'][0]['packages']]
    if package_name not in authorized_packages:
        errors.append(f"Paquete no autorizado: {package_name}")
        return errors

    # Obtener configuración de frecuencia
    freq_config = sender['senders']['senders_list'][0]['submission_frequency']

    # Validar frecuencia de envío
    if freq_config['type'] == 'monthly':
        today = datetime.now()
        deadline_day = freq_config['deadline']['if_monthly']['day']
        deadline_time = freq_config['deadline']['if_monthly']['time']

        if today.day > deadline_day:
            errors.append(f"Envío fuera de fecha límite (día {deadline_day})")

        deadline_hour = int(deadline_time.split(':')[0])
        if today.hour > deadline_hour:
            errors.append(f"Envío fuera de horario límite ({deadline_time})")

    return errors

def validate_file(
    file_path: str,
    catalog_path: str,
    package_path: str,
    sender_path: str
) -> Tuple[bool, List[str]]:
    """
    Validar un archivo según sus YAMLs de configuración.

    Args:
        file_path: Ruta al archivo a validar
        catalog_path: Ruta al YAML del catálogo
        package_path: Ruta al YAML del paquete
        sender_path: Ruta al YAML del emisor

    Returns:
        Tuple[bool, List[str]]: (éxito, lista de errores)
    """
    try:
        # Cargar YAMLs
        catalog = load_yaml(catalog_path)
        package = load_yaml(package_path)
        sender = load_yaml(sender_path)

        # Validar permisos del emisor
        errors = validate_sender_permissions(sender, package['package']['name'])
        if errors:
            return False, errors

        # Validar reglas del paquete
        errors = validate_package_rules(file_path, package)
        if errors:
            return False, errors

        # Cargar y validar datos
        df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)

        # Validar estructura y datos
        errors = validate_excel_structure(df, catalog)
        if errors:
            return False, errors

        # Validar reglas del paquete sobre los datos
        errors = validate_package_data(df, package)
        if errors:
            return False, errors

        return True, []

    except Exception as e:
        return False, [f"Error procesando archivo: {str(e)}"]

def main():
    """Función principal de validación."""
    # Configurar rutas
    base_dir = os.path.dirname(os.path.dirname(__file__))
    test_data_dir = os.path.join(base_dir, 'tests', 'test_data', 'valid')

    catalog = load_yaml(os.path.join(test_data_dir, 'catalogs', 'productos.yaml'))
    package = load_yaml(os.path.join(test_data_dir, 'package_productos.yaml'))
    sender = load_yaml(os.path.join(test_data_dir, 'sender_distribuidor.yaml'))

    # Validar archivo normal
    print("\nValidando archivo normal:")
    excel_file = f'tests/data/excel/ALC001-{datetime.now().strftime("%Y%m%d")}-PRODUCTOS.xlsx'
    success, errors = validate_file(excel_file, 
                                  os.path.join(test_data_dir, 'catalogs', 'productos.yaml'),
                                  os.path.join(test_data_dir, 'package_productos.yaml'),
                                  os.path.join(test_data_dir, 'sender_distribuidor.yaml'))

    if not success:
        print("\nErrores encontrados:")
        for error in errors:
            print(f"❌ {error}")
    else:
        print("✅ Archivo válido")

    # Validar archivo con errores
    print("\nValidando archivo con errores:")
    error_file = f'tests/data/excel/ALC001-{datetime.now().strftime("%Y%m%d")}-PRODUCTOS_ERROR.xlsx'
    success, errors = validate_file(error_file,
                                  os.path.join(test_data_dir, 'catalogs', 'productos.yaml'),
                                  os.path.join(test_data_dir, 'package_productos.yaml'),
                                  os.path.join(test_data_dir, 'sender_distribuidor.yaml'))

    if not success:
        print("\nErrores encontrados (esperados):")
        for error in errors:
            print(f"❌ {error}")
    else:
        print("⚠️ Archivo con errores validó correctamente")

if __name__ == '__main__':
    main()