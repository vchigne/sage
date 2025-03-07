"""Script para generar datos de prueba para SAGE."""
import os
import pandas as pd
from zipfile import ZipFile
import logging
from datetime import datetime, timedelta
import numpy as np

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_directory():
    """Create directory structure for test files"""
    dirs = [
        'tests/data/excel', 
        'tests/data/csv', 
        'tests/data/zip', 
        'data/files/csv', 
        'data/files/zip'
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    logger.info("Created test directories")

def generate_sample_data(rows=100, data_type='products', include_errors=False):
    """Generate sample data for testing."""
    if data_type == 'products':
        # Generar datos base que cumplan las reglas
        base_data = {
            'codigo_producto': [f'PROD{i:04d}' for i in range(rows)],
            'nombre_producto': [f'Producto de prueba {i:04d}' for i in range(rows)],
            'categoria': np.random.choice(['Alimentos', 'Bebidas', 'Limpieza', 'Cuidado Personal'], rows),
            'precio_lista': np.random.uniform(100, 1000, rows).round(2),
            'estado': np.random.choice(['Activo', 'Descontinuado', 'Proximamente'], rows)
        }

        if include_errors:
            # Introducir errores específicos para pruebas
            # 1. Valor nulo en nombre_producto (ERROR)
            base_data['nombre_producto'][2] = None  # Línea 3 en el CSV

            # 2. Precio negativo (ERROR)
            base_data['precio_lista'][4] = -50.00  # Línea 5 en el CSV

            # 3. Estado inválido (WARNING)
            base_data['estado'][6] = 'Inactivo'  # Línea 7 en el CSV

            # 4. Código de producto duplicado (ERROR)
            base_data['codigo_producto'][8] = base_data['codigo_producto'][0]  # Línea 9 en el CSV

        df = pd.DataFrame(base_data)

        if include_errors:
            logger.info("✓ Datos generados con errores intencionales para pruebas:")
            logger.info("  - Valor nulo en nombre_producto (línea 3)")
            logger.info("  - Precio negativo en precio_lista (línea 5)")
            logger.info("  - Estado inválido 'Inactivo' (línea 7)")
            logger.info("  - Código de producto duplicado (línea 9)")
        else:
            logger.info("✓ Datos válidos generados correctamente")

        return df

    else:
        raise ValueError(f"Tipo de datos no soportado: {data_type}")

def generate_productos_ejemplo():
    """Generate sample productos.csv file with intentional errors."""
    logger.info("Generando archivo productos_ejemplo.csv...")

    # Generar datos con errores específicos para probar validación
    df = generate_sample_data(rows=20, data_type='products', include_errors=True)

    # Guardar en la ruta esperada
    output_path = 'data/files/csv/productos_ejemplo.csv'
    df.to_csv(output_path, index=False)
    logger.info(f"✅ Archivo generado en: {output_path}")

    # Mostrar primeras filas
    logger.info("\nPrimeras filas del archivo generado:")
    logger.info(df.head().to_string())

    return output_path

def create_test_files():
    """Create test files in different formats."""
    today = datetime.now().strftime('%Y%m%d')
    sender_id = 'ALC001'

    logger.info("Generando archivos de datos...")

    # Generar datos válidos
    df_products = generate_sample_data(rows=50, data_type='products', include_errors=False)

    # Crear archivos Excel y CSV con nombres según patrón
    logger.info("Generando archivos...")

    # Productos en Excel
    productos_file = f'{sender_id}-{today}-PRODUCTOS.xlsx'
    df_products.to_excel(f'tests/data/excel/{productos_file}', index=False)

    # Crear ZIP con múltiples formatos
    logger.info("Creando archivo ZIP...")
    zip_file = f'{sender_id}-{today}-PAQUETE_SIMPLE.zip'

    with ZipFile(f'data/files/zip/{zip_file}', 'w') as zipf:
        # Guardar productos.csv temporalmente
        temp_csv = 'tests/data/csv/productos.csv'
        df_products.to_csv(temp_csv, index=False)
        zipf.write(temp_csv, f'{sender_id}-{today}-PRODUCTOS.csv')
        os.remove(temp_csv)  # Limpiar archivo temporal

    logger.info("Test files created successfully")

    # Listar todos los archivos generados
    logger.info("\nArchivos generados:")
    for root, dirs, files in os.walk('data'):
        level = root.replace('data', '').count(os.sep)
        indent = ' ' * 4 * level
        logger.info(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            logger.info(f"{subindent}{f}")

if __name__ == "__main__":
    create_test_directory()
    # Generar archivo de ejemplo con errores intencionales para probar validación
    generate_productos_ejemplo()
    # Generar archivos de prueba válidos
    create_test_files()
    logger.info("Test data generation completed")