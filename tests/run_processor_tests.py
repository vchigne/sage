import os
import sys
import logging
import yaml
from datetime import datetime
from pathlib import Path
import json

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sage.processors.yaml_processor import YAMLProcessor
from sage.processors.package_processor import PackageProcessor
from sage.processors.sender_processor import SenderProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_yaml_processor():
    """Probar el procesador de YAML genérico"""
    logger.info("\nProbando YAMLProcessor...")

    processor = YAMLProcessor()

    # Probar validación de YAML de catálogo
    logger.info("\nValidando YAML de catálogo:")
    success, errors = processor.validate_yaml(
        'tests/test_data/valid/catalogs/productos.yaml',
        'catalog'
    )

    if success:
        logger.info("✅ YAML de catálogo válido")
    else:
        for error in errors:
            logger.error(f"❌ {error}")

    return success, errors

def test_package_processor():
    """Probar el procesador de paquetes"""
    logger.info("\nProbando PackageProcessor...")

    processor = PackageProcessor()

    # Configurar rutas
    base_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(base_dir, 'test_data', 'valid')
    today = datetime.now().strftime('%Y%m%d')

    # Probar procesamiento de paquete ZIP
    logger.info("\nProcesando paquete ZIP:")
    success, errors = processor.process_package(
        f'tests/data/zip/ALC001-{today}-PAQUETE_MIXTO.zip',
        os.path.join(test_data_dir, 'test_package.yaml'),
        os.path.join(test_data_dir, 'catalogs')
    )

    if success:
        logger.info("✅ Paquete ZIP procesado correctamente")
    else:
        for error in errors:
            logger.error(f"❌ {error}")

    return success, errors

def test_sender_processor():
    """Probar el procesador de emisores"""
    logger.info("\nProbando SenderProcessor...")

    processor = SenderProcessor()

    # Probar procesamiento de emisor
    logger.info("\nValidando emisor:")
    success, errors = processor.process_sender(
        'tests/test_data/valid/sender_distribuidor.yaml',
        'Maestro de Productos Oficial'
    )

    if success:
        logger.info("✅ Emisor validado correctamente")
    else:
        for error in errors:
            logger.error(f"❌ {error}")

    return success, errors

def print_summary(processor_results):
    """Imprimir resumen detallado"""
    logger.info("\n" + "="*50)
    logger.info("RESUMEN DE PROCESAMIENTO")
    logger.info("="*50)

    for processor, (success, errors) in processor_results.items():
        logger.info(f"\n{processor}:")
        if success:
            logger.info("✅ Procesamiento exitoso")
        else:
            logger.info("❌ Errores encontrados:")
            for error in errors:
                logger.info(f"  - {error}")

    logger.info("\n" + "="*50)

def main():
    """Función principal de pruebas"""
    logger.info("Iniciando pruebas de procesadores...")

    processor_results = {}

    try:
        # Probar YAMLProcessor
        processor_results['YAMLProcessor'] = test_yaml_processor()

        # Probar PackageProcessor
        processor_results['PackageProcessor'] = test_package_processor()

        # Probar SenderProcessor
        processor_results['SenderProcessor'] = test_sender_processor()

        # Mostrar resumen
        print_summary(processor_results)

    except Exception as e:
        logger.error(f"Error ejecutando pruebas: {str(e)}")

if __name__ == "__main__":
    main()