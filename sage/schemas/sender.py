"""Sender schema definition and validation."""
from typing import Dict, Any
from ..utils.logger import get_logger
from ..utils.exceptions import SchemaValidationError

logger = get_logger(__name__)

class SenderSchema:
    """Schema definition and validation for senders.yaml files."""
    
    REQUIRED_FIELDS = ['corporate_owner', 'data_receivers', 'senders_list']
    
    ALLOWED_METHODS = ['sftp', 'email', 'api']
    
    @classmethod
    def validate_schema(cls, data: Dict[str, Any]) -> bool:
        """
        Validate that a sender YAML matches the expected schema.
        
        Args:
            data: Dictionary containing YAML data
            
        Returns:
            bool: True if validation passes
            
        Raises:
            SchemaValidationError: If schema validation fails
        """
        try:
            # Validate top level structure
            if 'senders' not in data:
                raise SchemaValidationError("Missing top-level 'senders' key")
                
            senders = data['senders']
            
            # Validate required fields
            missing_fields = [field for field in cls.REQUIRED_FIELDS 
                            if field not in senders]
            if missing_fields:
                raise SchemaValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}")
                
            # Validate data receivers
            receivers = senders['data_receivers']
            if not isinstance(receivers, list):
                raise SchemaValidationError("'data_receivers' must be an array")
                
            for receiver in receivers:
                if 'name' not in receiver:
                    raise SchemaValidationError("Receiver missing 'name'")
                if 'email' not in receiver:
                    raise SchemaValidationError(
                        f"Receiver '{receiver['name']}' missing 'email'")
                    
            # Validate senders list
            senders_list = senders['senders_list']
            if not isinstance(senders_list, list):
                raise SchemaValidationError("'senders_list' must be an array")
                
            for sender in senders_list:
                if 'sender_id' not in sender:
                    raise SchemaValidationError("Sender missing 'sender_id'")
                if 'name' not in sender:
                    raise SchemaValidationError(
                        f"Sender '{sender['sender_id']}' missing 'name'")
                    
                # Validate responsible person
                if 'responsible_person' not in sender:
                    raise SchemaValidationError(
                        f"Sender '{sender['name']}' missing 'responsible_person'")
                    
                person = sender['responsible_person']
                for field in ['name', 'email', 'phone']:
                    if field not in person:
                        raise SchemaValidationError(
                            f"Responsible person for '{sender['name']}' missing '{field}'")
                            
                # Validate allowed methods
                if 'allowed_methods' not in sender:
                    raise SchemaValidationError(
                        f"Sender '{sender['name']}' missing 'allowed_methods'")
                    
                methods = sender['allowed_methods']
                if not isinstance(methods, list):
                    raise SchemaValidationError("'allowed_methods' must be an array")
                    
                invalid_methods = [m for m in methods if m not in cls.ALLOWED_METHODS]
                if invalid_methods:
                    raise SchemaValidationError(
                        f"Invalid methods for '{sender['name']}': {', '.join(invalid_methods)}")
                        
                # Validate configurations
                if 'configurations' not in sender:
                    raise SchemaValidationError(
                        f"Sender '{sender['name']}' missing 'configurations'")
                    
                configs = sender['configurations']
                for method in methods:
                    if method not in configs:
                        raise SchemaValidationError(
                            f"Missing configuration for method '{method}' in sender '{sender['name']}'")
                            
            logger.debug("Successfully validated sender schema")
            return True
            
        except SchemaValidationError as e:
            logger.error(f"Sender schema validation failed: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error validating sender schema: {str(e)}"
            logger.error(error_msg)
            raise SchemaValidationError(error_msg)
