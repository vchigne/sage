"""Custom exceptions for SAGE."""

class SAGEError(Exception):
    """Base exception for all SAGE errors."""
    pass

class YAMLLoadError(SAGEError):
    """Raised when there's an error loading a YAML file."""
    pass

class SchemaValidationError(SAGEError):
    """Raised when YAML schema validation fails."""
    pass

class ValidationError(SAGEError):
    """Raised when data validation fails."""
    pass

class ProcessingError(SAGEError):
    """Raised when there's an error processing data."""
    pass

class SecretError(SAGEError):
    """Raised when there's an error processing secrets."""
    pass