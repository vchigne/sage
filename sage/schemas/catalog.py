"""Catalog schema definition and validation."""
from typing import Dict, Any
from ..utils.logger import get_logger
from ..utils.exceptions import SchemaValidationError

logger = get_logger(__name__)

class CatalogSchema:
    """Schema definition and validation for catalog.yaml files."""
    
    REQUIRED_FIELDS = ['name', 'description', 'fields']
    
    FIELD_TYPES = ['text', 'number', 'boolean', 'date']
    
    @classmethod
    def validate_schema(cls, data: Dict[str, Any]) -> bool:
        """
        Validate that a catalog YAML matches the expected schema.
        
        Args:
            data: Dictionary containing YAML data
            
        Returns:
            bool: True if validation passes
            
        Raises:
            SchemaValidationError: If schema validation fails
        """
        try:
            # Validate top level structure
            if 'catalog' not in data:
                raise SchemaValidationError("Missing top-level 'catalog' key")
                
            catalog = data['catalog']
            
            # Validate required fields
            missing_fields = [field for field in cls.REQUIRED_FIELDS 
                            if field not in catalog]
            if missing_fields:
                raise SchemaValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}")
                
            # Validate fields array
            fields = catalog['fields']
            if not isinstance(fields, list):
                raise SchemaValidationError("'fields' must be an array")
                
            # Validate each field definition
            for field in fields:
                if 'name' not in field:
                    raise SchemaValidationError("Field missing 'name'")
                    
                if 'type' not in field:
                    raise SchemaValidationError(
                        f"Field '{field['name']}' missing 'type'")
                        
                if field['type'] not in cls.FIELD_TYPES:
                    raise SchemaValidationError(
                        f"Invalid type '{field['type']}' for field '{field['name']}'")
                        
                if 'length' in field and not isinstance(field['length'], int):
                    raise SchemaValidationError(
                        f"'length' must be an integer for field '{field['name']}'")
                        
                if 'required' in field and not isinstance(field['required'], bool):
                    raise SchemaValidationError(
                        f"'required' must be a boolean for field '{field['name']}'")
                        
                if 'unique' in field and not isinstance(field['unique'], bool):
                    raise SchemaValidationError(
                        f"'unique' must be a boolean for field '{field['name']}'")
                        
            logger.debug("Successfully validated catalog schema")
            return True
            
        except SchemaValidationError as e:
            logger.error(f"Catalog schema validation failed: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error validating catalog schema: {str(e)}"
            logger.error(error_msg)
            raise SchemaValidationError(error_msg)
