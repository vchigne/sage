"""YAML loading and parsing functionality."""
import os
import yaml
from typing import Dict, Any, Optional
from ..utils.logger import get_logger
from ..utils.exceptions import YAMLLoadError

logger = get_logger(__name__)

class YAMLLoader:
    """Handles loading and basic validation of YAML files."""
    
    @staticmethod
    def load_yaml(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a YAML file and return its contents as a dictionary.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing the YAML contents or None if file doesn't exist
            
        Raises:
            YAMLLoadError: If there's an error loading the YAML file
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"YAML file not found: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as yaml_file:
                data = yaml.safe_load(yaml_file)
                logger.debug(f"Successfully loaded YAML file: {file_path}")
                return data
                
        except yaml.YAMLError as e:
            error_msg = f"Error parsing YAML file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise YAMLLoadError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error loading YAML file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise YAMLLoadError(error_msg)

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> bool:
        """
        Validate that all required fields are present in the YAML data.
        
        Args:
            data: Dictionary containing YAML data
            required_fields: List of required field names
            
        Returns:
            bool: True if all required fields are present
        """
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.error(f"Missing required fields: {', '.join(missing_fields)}")
            return False
            
        return True
