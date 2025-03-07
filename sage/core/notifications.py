"""Notification handling for SAGE."""
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Union, Optional
from .validation_utils import ValidationResult

logger = logging.getLogger(__name__)

class NotificationManager:
    """Handles notifications based on sender configuration."""

    def __init__(self, sender_config: Dict[str, Any]):
        """Initialize with sender configuration."""
        self.config = sender_config
        self.receivers = sender_config.get('data_receivers', [])

    def format_validation_message(self, validations: List[Union[ValidationResult, Dict[str, Any]]]) -> str:
        """Format validation results for notification."""
        message_parts = ['Resultados de validación:']

        for result in validations:
            # Convert ValidationResult to dict if needed
            if isinstance(result, ValidationResult):
                result = result.to_dict()

            severity = result.get('severity', 'INFO')
            emoji = '❌' if severity == 'ERROR' else '⚠️' if severity == 'WARNING' else 'ℹ️'

            parts = [f"{emoji} {result['message']}"]

            if result.get('field'):
                parts.append(f"Campo: {result['field']}")
            if result.get('line'):
                parts.append(f"Línea: {result['line']}")
            if result.get('value') is not None:
                parts.append(f"Valor: {result['value']}")
            if result.get('validation_rule'):
                parts.append(f"Regla: {result['validation_rule']}")

            message_parts.append(' | '.join(parts))

        return '\n'.join(message_parts)

    def format_success_message(self, package_info: Dict[str, Any]) -> str:
        """Format success message with package details."""
        message_parts = [
            f"✅ Datos en el paquete {package_info.get('name', 'N/A')} correctos."
        ]

        # Add counts by entity type
        counts = package_info.get('counts', {})
        if counts:
            message_parts.append("Se han agregado:")
            for entity, count in counts.items():
                message_parts.append(f"- {count} registros de {entity}")

        return '\n'.join(message_parts)

    async def notify_receivers(self, validations: List[ValidationResult], package_name: str, package_info: Optional[Dict[str, Any]] = None) -> None:
        """Notify all configured receivers."""
        # Convert ValidationResults to dict format
        validation_dicts = [v.to_dict() for v in validations]

        # Determine if process was successful (no ERROR severity validations)
        is_success = not any(v.severity == 'ERROR' for v in validations)

        # Format message based on success/failure
        if is_success and package_info:
            message = self.format_success_message(package_info)
            subject = f"✅ Validación exitosa: {package_name}"
        else:
            message = self.format_validation_message(validation_dicts)
            subject = f"❌ Errores en validación: {package_name}"

        for receiver in self.receivers:
            try:
                # Email notification
                if receiver.get('email'):
                    self._send_email_notification(
                        receiver['email'],
                        subject,
                        message
                    )

                # API notification
                if receiver.get('api_endpoint'):
                    await self._send_api_notification(
                        receiver['api_endpoint'],
                        {
                            'package_name': package_name,
                            'success': is_success,
                            'validations': validation_dicts,
                            'package_info': package_info if is_success else None
                        }
                    )

                logger.info(f"✅ Notificación enviada a {receiver.get('name')}")

            except Exception as e:
                logger.error(f"❌ Error enviando notificación a {receiver.get('name')}: {str(e)}")

    def _send_email_notification(self, email: str, subject: str, message: str) -> None:
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = "sage-notifications@replit.app"
            msg['To'] = email

            # Add message body
            msg.attach(MIMEText(message, 'plain'))

            # Send email using configured SMTP server
            with smtplib.SMTP('smtp.replit.app', 587) as server:
                server.starttls()
                server.login('sage-notifications@replit.app', 'password')  # Use environment variables in production
                server.send_message(msg)

        except Exception as e:
            logger.error(f"❌ Error enviando email a {email}: {str(e)}")
            raise

    async def _send_api_notification(self, endpoint: str, data: Dict[str, Any]) -> None:
        """Send API notification."""
        try:
            response = requests.post(endpoint, json=data)
            response.raise_for_status()

        except Exception as e:
            logger.error(f"❌ Error enviando notificación API a {endpoint}: {str(e)}")
            raise