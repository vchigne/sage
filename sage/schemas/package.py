"""Package schema definition and validation."""
from typing import Dict, Any
from ..utils.logger import get_logger
from ..utils.exceptions import SchemaValidationError

logger = get_logger(__name__)

class PackageSchema:
    """Schema definition and validation for package.yaml files."""
    
    REQUIRED_FIELDS = ['name', 'description', 'methods', 'catalogs']
    
    ALLOWED_FILE_TYPES = ['CSV', 'XLSX', 'JSON', 'XML', 'ZIP']
    
    @classmethod
    def validate_schema(cls, data: Dict[str, Any]) -> bool:
        """
        Validate that a package YAML matches the expected schema.
        
        Args:
            data: Dictionary containing YAML data
            
        Returns:
            bool: True if validation passes
            
        Raises:
            SchemaValidationError: If schema validation fails
        """
        try:
            # Validate top level structure
            if 'package' not in data:
                raise SchemaValidationError("Missing top-level 'package' key")
                
            package = data['package']
            
            # Validate required fields
            missing_fields = [field for field in cls.REQUIRED_FIELDS 
                            if field not in package]
            if missing_fields:
                raise SchemaValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}")
                
            # Validate methods
            methods = package['methods']
            if 'file_format' not in methods:
                raise SchemaValidationError("Missing 'file_format' in methods")
                
            file_format = methods['file_format']
            if 'type' not in file_format:
                raise SchemaValidationError("Missing 'type' in file_format")
                
            if file_format['type'] not in cls.ALLOWED_FILE_TYPES:
                raise SchemaValidationError(
                    f"Invalid file type '{file_format['type']}'")
                
            # Validate catalogs
            catalogs = package['catalogs']
            if not isinstance(catalogs, list):
                raise SchemaValidationError("'catalogs' must be an array")
                
            for catalog in catalogs:
                if 'path' not in catalog:
                    raise SchemaValidationError("Catalog missing 'path'")
                    
            # Validate package validation rules if present
            if 'package_validation' in package:
                validation = package['package_validation']
                if 'validation_rules' not in validation:
                    raise SchemaValidationError(
                        "Missing 'validation_rules' in package_validation")
                    
                rules = validation['validation_rules']
                if not isinstance(rules, list):
                    raise SchemaValidationError("'validation_rules' must be an array")
                    
                for rule in rules:
                    if 'name' not in rule:
                        raise SchemaValidationError("Validation rule missing 'name'")
                    if 'validation_expression' not in rule:
                        raise SchemaValidationError(
                            f"Validation rule '{rule['name']}' missing 'validation_expression'")
                            
            logger.debug("Successfully validated package schema")
            return True
            
        except SchemaValidationError as e:
            logger.error(f"Package schema validation failed: {str(e)}")
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error validating package schema: {str(e)}"
            logger.error(error_msg)
            raise SchemaValidationError(error_msg)
