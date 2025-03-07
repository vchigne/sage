"""Main entry point for SAGE."""
import os
from sage.core.yaml_loader import YAMLLoader
from sage.core.processor import SageProcessor
from sage.utils.logger import get_logger
from sage.utils.exceptions import SAGEError

logger = get_logger(__name__)

def process_data_file(data_file: str, 
                   catalog_file: str) -> bool:
    """
    Process a data file using the specified catalog configuration.

    Args:
        data_file: Path to the data file
        catalog_file: Path to the catalog YAML file

    Returns:
        bool: True if processing succeeds
    """
    try:
        # Load catalog configuration
        yaml_loader = YAMLLoader()
        catalog_data = yaml_loader.load_yaml(catalog_file)
        if not catalog_data:
            logger.error("❌ No se pudo cargar el archivo YAML del catálogo")
            return False

        logger.info(f"Procesando archivo: {data_file}")
        logger.info(f"Usando catálogo: {catalog_file}")

        # Verify file exists
        if not os.path.exists(data_file):
            logger.error(f"❌ Archivo no encontrado: {data_file}")
            return False

        # Process data according to catalog configuration
        processor = SageProcessor()
        success, validation_results = processor.process_data(
            data_file=data_file, 
            yaml_config=catalog_data['catalog']
        )

        if success:
            logger.info(f"✅ Archivo procesado exitosamente: {data_file}")

        return success

    except SAGEError as e:
        logger.error(f"❌ Error procesando datos: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return False

def main():
    """Main entry point for the application."""
    logger.info("🚀 Starting SAGE - Structured Automated Governance of Entities")

    # Process sample data file
    data_file = os.path.join('data', 'files', 'csv', 'productos_ejemplo.csv')
    catalog_file = os.path.join('data', 'yaml', 'catalog', 'productos.yaml')

    if not process_data_file(data_file, catalog_file):
        logger.error("❌ Procesamiento de datos fallido")
        return

    logger.info("✅ Procesamiento de datos completado exitosamente")

if __name__ == '__main__':
    main()