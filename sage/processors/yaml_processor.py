"""YAML processor for SAGE.

This processor extends the base SageProcessor to handle generic YAML validation
and processing. It uses the core functionality from SageProcessor while adding
specific validation for different YAML types (catalog, package, sender).

Example:
    processor = YAMLProcessor()
    success, errors = processor.validate_yaml(
        'catalogs/productos.yaml',
        'catalog'
    )
"""
from typing import Dict, Any, List, Tuple
import yaml
from ..core.processor import SageProcessor
from ..utils.exceptions import ProcessingError
from ..utils.logger import get_logger

logger = get_logger(__name__)

class YAMLProcessor(SageProcessor):
    """Processor class for generic YAML file validation and processing."""

    def __init__(self):
        """Initialize the YAML processor."""
        super().__init__()

    def load_yaml_config(self, yaml_path: str) -> Dict[str, Any]:
        """
        Load and parse a YAML configuration file.

        Args:
            yaml_path: Path to the YAML file

        Returns:
            Dict[str, Any]: Parsed YAML content

        Raises:
            ProcessingError: If YAML loading fails
        """
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            error_msg = f"Error loading YAML {yaml_path}: {str(e)}"
            logger.error(error_msg)
            raise ProcessingError(error_msg)

    def validate_yaml(self, yaml_path: str, schema_type: str) -> Tuple[bool, List[str]]:
        """
        Validate a YAML file against its schema.

        Uses the core SageProcessor functionality to load and process the YAML,
        while adding specific validation based on the schema type.

        Args:
            yaml_path: Path to the YAML file
            schema_type: Type of schema to validate against ('catalog', 'package', 'sender')

        Returns:
            Tuple[bool, List[str]]: (success, list of errors)
        """
        try:
            # Load the YAML config using core functionality
            yaml_config = self.load_yaml_config(yaml_path)

            # Import the appropriate schema validator
            if schema_type == 'catalog':
                from ..schemas.catalog import CatalogSchema as SchemaValidator
            elif schema_type == 'package':
                from ..schemas.package import PackageSchema as SchemaValidator
            elif schema_type == 'sender':
                from ..schemas.sender import SenderSchema as SchemaValidator
            else:
                raise ValueError(f"Unsupported schema type: {schema_type}")

            # Validate schema
            try:
                SchemaValidator.validate_schema(yaml_config)
                return True, []
            except Exception as e:
                return False, [str(e)]

        except Exception as e:
            error_msg = f"Error validating YAML {yaml_path}: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]

    def process_yaml(self, 
                    yaml_path: str,
                    schema_type: str,
                    **kwargs) -> Tuple[bool, List[str]]:
        """
        Process a YAML file according to its type.

        Uses the core SageProcessor functionality to process the data while
        handling specific requirements for each schema type.

        Args:
            yaml_path: Path to the YAML file
            schema_type: Type of schema ('catalog', 'package', 'sender')
            **kwargs: Additional processing parameters

        Returns:
            Tuple[bool, List[str]]: (success, list of errors)
        """
        # First validate the YAML schema
        success, errors = self.validate_yaml(yaml_path, schema_type)
        if not success:
            return False, errors

        try:
            # Load the YAML config using core functionality
            yaml_config = self.load_yaml_config(yaml_path)

            # Process according to schema type
            if schema_type == 'catalog':
                if 'data_file' not in kwargs:
                    return False, ["Data file required for catalog processing"]
                return self.process_data(kwargs['data_file'], yaml_config)

            elif schema_type == 'package':
                # Package processing is handled by PackageProcessor
                return True, []

            elif schema_type == 'sender':
                # Sender processing is handled by SenderProcessor
                return True, []

            else:
                return False, [f"Unsupported schema type: {schema_type}"]

        except Exception as e:
            error_msg = f"Error processing YAML {yaml_path}: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]