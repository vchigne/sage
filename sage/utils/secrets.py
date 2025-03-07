"""Secret management functionality."""
import os
import re
from typing import Dict, Any, Optional
from .logger import get_logger
from .exceptions import SecretError

logger = get_logger(__name__)

class SecretManager:
    """Handles loading and processing of secrets from YAML files."""
    
    @staticmethod
    def load_secrets(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load secrets from YAML data, replacing template variables with environment values.
        
        Args:
            yaml_data: Dictionary containing YAML data with template variables
            
        Returns:
            Dictionary with template variables replaced with actual values
            
        Raises:
            SecretError: If required environment variables are missing
        """
        try:
            # Convert YAML to string to do replacements
            str_data = str(yaml_data)
            
            # Find all template variables
            template_vars = re.findall(r'{{\s*([A-Z_]+)\s*}}', str_data)
            
            # Replace each template variable with its environment value
            for var in template_vars:
                env_value = os.environ.get(var)
                if env_value is None:
                    raise SecretError(f"Missing environment variable: {var}")
                    
                str_data = str_data.replace(f"{{{{ {var} }}}}", env_value)
                
            # Convert back to dictionary
            processed_data = eval(str_data)
            return processed_data
            
        except Exception as e:
            error_msg = f"Error processing secrets: {str(e)}"
            logger.error(error_msg)
            raise SecretError(error_msg)
    
    @classmethod
    def get_database_config(cls, db_type: str, environment: str) -> Dict[str, Any]:
        """
        Get database configuration for specific type and environment.
        
        Args:
            db_type: Type of database ('mysql', 'postgresql')
            environment: Environment name ('dev', 'test', 'prod')
            
        Returns:
            Dictionary containing database configuration
        """
        from ..core.yaml_loader import YAMLLoader
        
        try:
            yaml_loader = YAMLLoader()
            db_config = yaml_loader.load_yaml('config/secrets/database.yaml')
            
            if not db_config or 'databases' not in db_config:
                raise SecretError("Invalid database configuration")
                
            if db_type not in db_config['databases']:
                raise SecretError(f"Unknown database type: {db_type}")
                
            if environment not in db_config['databases'][db_type]:
                raise SecretError(f"Unknown environment: {environment}")
                
            config = db_config['databases'][db_type][environment]
            return cls.load_secrets({'config': config})['config']
            
        except Exception as e:
            error_msg = f"Error loading database configuration: {str(e)}"
            logger.error(error_msg)
            raise SecretError(error_msg)
    
    @classmethod
    def get_email_config(cls, environment: str) -> Dict[str, Any]:
        """Get email configuration for specific environment."""
        from ..core.yaml_loader import YAMLLoader
        
        try:
            yaml_loader = YAMLLoader()
            email_config = yaml_loader.load_yaml('config/secrets/email.yaml')
            
            if not email_config or 'email_servers' not in email_config:
                raise SecretError("Invalid email configuration")
                
            if environment not in email_config['email_servers']['smtp']:
                raise SecretError(f"Unknown environment: {environment}")
                
            config = email_config['email_servers']['smtp'][environment]
            return cls.load_secrets({'config': config})['config']
            
        except Exception as e:
            error_msg = f"Error loading email configuration: {str(e)}"
            logger.error(error_msg)
            raise SecretError(error_msg)
    
    @classmethod
    def get_sftp_config(cls, environment: str) -> Dict[str, Any]:
        """Get SFTP configuration for specific environment."""
        from ..core.yaml_loader import YAMLLoader
        
        try:
            yaml_loader = YAMLLoader()
            sftp_config = yaml_loader.load_yaml('config/secrets/sftp.yaml')
            
            if not sftp_config or 'sftp_servers' not in sftp_config:
                raise SecretError("Invalid SFTP configuration")
                
            if environment not in sftp_config['sftp_servers']:
                raise SecretError(f"Unknown environment: {environment}")
                
            config = sftp_config['sftp_servers'][environment]
            return cls.load_secrets({'config': config})['config']
            
        except Exception as e:
            error_msg = f"Error loading SFTP configuration: {str(e)}"
            logger.error(error_msg)
            raise SecretError(error_msg)
