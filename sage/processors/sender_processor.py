"""Sender processor for SAGE.

This processor extends the base SageProcessor to handle sender validation
and processing. It uses the core functionality from SageProcessor while adding
specific validation for sender permissions, frequency rules and deadlines.

Example:
    processor = SenderProcessor()
    success, errors = processor.process_sender(
        'config/sender.yaml',
        'Maestro de Productos'
    )
"""
from datetime import datetime
from typing import Dict, Any, List, Tuple
from ..core.processor import SageProcessor
from ..utils.exceptions import ProcessingError

class SenderProcessor(SageProcessor):
    """Processor class for sender validation and processing."""

    def __init__(self):
        """Initialize the sender processor."""
        super().__init__()

    def validate_sender_permissions(self, 
                                 sender_config: Dict[str, Any],
                                 package_name: str) -> List[str]:
        """
        Validate sender permissions for a package.

        Args:
            sender_config: Sender configuration from YAML
            package_name: Name of the package to validate

        Returns:
            List[str]: List of validation errors
        """
        errors = []

        try:
            # Verify package authorization
            authorized_packages = [
                p['name'] 
                for p in sender_config['senders']['senders_list'][0]['packages']
            ]

            if package_name not in authorized_packages:
                errors.append(f"Package not authorized: {package_name}")
                return errors

            # Get frequency configuration
            freq_config = sender_config['senders']['senders_list'][0]['submission_frequency']

            # Validate submission frequency
            if freq_config['type'] == 'monthly':
                today = datetime.now()
                deadline_day = freq_config['deadline']['if_monthly']['day']
                deadline_time = freq_config['deadline']['if_monthly']['time']

                if today.day > deadline_day:
                    errors.append(f"Submission past deadline (day {deadline_day})")

                deadline_hour = int(deadline_time.split(':')[0])
                if today.hour > deadline_hour:
                    errors.append(f"Submission past time limit ({deadline_time})")

            elif freq_config['type'] == 'weekly':
                today = datetime.now()
                deadline_day = freq_config['deadline']['if_weekly']['day_of_week']
                deadline_time = freq_config['deadline']['if_weekly']['time']

                if today.strftime('%A') > deadline_day:
                    errors.append(f"Submission past deadline (day {deadline_day})")

                deadline_hour = int(deadline_time.split(':')[0])
                if today.hour > deadline_hour:
                    errors.append(f"Submission past time limit ({deadline_time})")

            elif freq_config['type'] == 'daily':
                today = datetime.now()
                deadline_time = freq_config['deadline']['if_daily']['time']

                deadline_hour = int(deadline_time.split(':')[0])
                if today.hour > deadline_hour:
                    errors.append(f"Submission past time limit ({deadline_time})")

            return errors

        except Exception as e:
            error_msg = f"Error validating sender permissions: {str(e)}"
            self.logger.error(error_msg)
            return [error_msg]

    def process_sender(self,
                      sender_yaml: str,
                      package_name: str,
                      **kwargs) -> Tuple[bool, List[str]]:
        """
        Process a sender configuration.

        Args:
            sender_yaml: Path to the sender YAML
            package_name: Name of the package being submitted
            **kwargs: Additional processing parameters

        Returns:
            Tuple[bool, List[str]]: (success, list of errors)
        """
        try:
            # Load sender configuration using core functionality
            sender_config = self.load_yaml_config(sender_yaml)

            # Validate sender permissions
            errors = self.validate_sender_permissions(sender_config, package_name)

            return len(errors) == 0, errors

        except Exception as e:
            error_msg = f"Error processing sender: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg]