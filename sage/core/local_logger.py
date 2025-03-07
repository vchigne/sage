"""Local file logging for SFTP and directory uploads."""
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from .validation_utils import ValidationResult, format_validation_message

logger = logging.getLogger(__name__)

class LocalLogger:
    """Handles local file logging for SFTP and directory uploads."""

    def __init__(self, base_dir: str = "logs"):
        """Initialize local logger."""
        self.base_dir = base_dir
        self._ensure_log_dirs()

    def _ensure_log_dirs(self):
        """Ensure log directories exist."""
        logger.info(f"Ensuring log directories exist in {self.base_dir}")
        for upload_type in ['sftp', 'local']:
            dir_path = os.path.join(self.base_dir, upload_type)
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created/verified directory: {dir_path}")

    def _get_log_path(self, upload_type: str, sender_id: str) -> str:
        """Get the path for the log file."""
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"{date_str}_validation.log"
        sender_dir = os.path.join(self.base_dir, upload_type, sender_id)
        os.makedirs(sender_dir, exist_ok=True)
        log_path = os.path.join(sender_dir, filename)
        logger.info(f"Log will be written to: {log_path}")
        return log_path

    def log_validation_results(self, 
                           results: List[ValidationResult], 
                           upload_type: str,
                           sender_id: str,
                           package_info: Dict[str, Any]) -> None:
        """
        Log validation results to a local file.

        Args:
            results: List of validation results
            upload_type: Type of upload ('sftp' or 'local')
            sender_id: ID of the sender
            package_info: Dictionary with package information (name, counts, etc)
        """
        logger.info(f"Processing validation results for {upload_type} upload from {sender_id}")
        log_path = self._get_log_path(upload_type, sender_id)

        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                # Write timestamp
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"\n=== Validación {timestamp} ===\n")
                logger.debug(f"Writing validation results at {timestamp}")

                # Write package info if successful
                if not any(r.severity == 'ERROR' for r in results):
                    logger.info("Process successful, writing package info")
                    f.write("\n✅ Proceso exitoso\n")
                    f.write(f"📦 Paquete: {package_info.get('name', 'N/A')}\n")
                    for entity, count in package_info.get('counts', {}).items():
                        f.write(f"📊 {count} registros de {entity}\n")
                    f.write("\n")

                # Write validation messages
                for result in results:
                    # Format the message with icons and proper structure
                    message = format_validation_message(result)
                    logger.debug(f"Writing validation message: {message}")

                    # Write the validation rule in a user-friendly format
                    message += "\nRegla: "
                    if result.validation_rule:
                        rule = result.validation_rule
                        # Make the rule more readable
                        rule = rule.replace("df['", "").replace("']", "")
                        rule = rule.replace(".isin", " debe estar en ")
                        rule = rule.replace(".notna()", "no puede estar vacío")
                        rule = rule.replace(".duplicated", "está duplicado")
                        rule = rule.replace(" > ", " mayor que ")
                        rule = rule.replace(" < ", " menor que ")
                        rule = rule.replace(" >= ", " mayor o igual a ")
                        rule = rule.replace(" <= ", " menor o igual a ")
                        rule = rule.replace(" == ", " igual a ")
                        rule = rule.replace(" != ", " diferente de ")
                        rule = rule.replace(" | ", " o ")
                        rule = rule.replace(" & ", " y ")
                        message += rule
                    else:
                        message += "No especificada"

                    f.write(f"{message}\n\n")

                f.write("\n")  # Extra line for readability

            logger.info(f"✓ Resultados guardados en log local: {log_path}")

        except Exception as e:
            logger.error(f"❌ Error escribiendo log local {log_path}: {str(e)}")
            raise