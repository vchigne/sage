import schedule
import time
import logging
from datetime import datetime
from data_processor import DataProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def job():
    """Tarea programada para ejecutar el procesador de datos"""
    logger.info("Starting scheduled data processing job")
    try:
        processor = DataProcessor()
        processor.setup_database()

        # Procesar todos los YAMLs activos
        with processor.db_connection.cursor() as cursor:
            cursor.execute("SELECT id FROM yaml_configs WHERE active = true")
            active_yamls = cursor.fetchall()

            for yaml_id in active_yamls:
                try:
                    exec_id = processor.start_execution(yaml_id[0])
                    logger.info(f"Started execution {exec_id} for YAML {yaml_id[0]}")
                except Exception as e:
                    logger.error(f"Error processing YAML {yaml_id[0]}: {str(e)}")

        logger.info("Data processing job completed successfully")
    except Exception as e:
        logger.error(f"Error in data processing job: {str(e)}")

def run_scheduler():
    """Inicia el planificador de tareas"""
    # Ejecutar cada 30 minutos
    schedule.every(30).minutes.do(job)

    # También ejecutar al inicio
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    logger.info("Starting data processor scheduler")
    run_scheduler()