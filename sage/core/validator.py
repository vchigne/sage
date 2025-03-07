"""Data validation functionality."""
import pandas as pd
from typing import Dict, Any, List, Tuple
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError

logger = get_logger(__name__)

class DataValidator:
    """Handles validation of data against YAML-defined rules."""

    @staticmethod
    def validate_field_type(value: Any, field_type: str) -> bool:
        """
        Validate that a value matches the expected type.

        Args:
            value: Value to validate
            field_type: Expected type ('text', 'number', 'boolean', 'date')

        Returns:
            bool: True if validation passes
        """
        try:
            if field_type == 'text':
                return isinstance(value, str)
            elif field_type == 'number':
                return isinstance(value, (int, float))
            elif field_type == 'boolean':
                return isinstance(value, bool)
            elif field_type == 'date':
                pd.to_datetime(value)
                return True
            return False
        except:
            return False

    @staticmethod
    def validate_field_length(value: Any, max_length: int) -> bool:
        """
        Validate that a value doesn't exceed the maximum length.

        Args:
            value: Value to validate
            max_length: Maximum allowed length

        Returns:
            bool: True if validation passes
        """
        if isinstance(value, str):
            return len(value) <= max_length
        elif isinstance(value, (int, float)):
            return len(str(value)) <= max_length
        return False

    @staticmethod
    def validate_unique_values(df: pd.DataFrame, field: str) -> bool:
        """
        Validate that a field contains only unique values.

        Args:
            df: DataFrame containing the data
            field: Field name to check for uniqueness

        Returns:
            bool: True if all values are unique
        """
        return df[field].nunique() == len(df)

    @staticmethod
    def validate_required_field(df: pd.DataFrame, field: str) -> bool:
        """
        Validate that a required field contains no null values.

        Args:
            df: DataFrame containing the data
            field: Field name to check for null values

        Returns:
            bool: True if no null values are found
        """
        return not df[field].isnull().any()

    @staticmethod
    def validate_expression(df: pd.DataFrame, expression: str) -> bool:
        """
        Validate data using a custom expression.

        Args:
            df: DataFrame containing the data
            expression: Python expression to evaluate

        Returns:
            bool: True if validation passes
        """
        try:
            # Modify expression to ensure we get a boolean result
            if "notnull()" in expression:
                expression = expression.replace("notnull()", "notnull().all()")
            elif ">=" in expression or "<=" in expression or ">" in expression or "<" in expression:
                expression = f"({expression}).all()"

            result = eval(expression, {'df': df, 'pd': pd})
            return bool(result)
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {str(e)}")
            return False

    @classmethod
    def validate_catalog_data(cls, df: pd.DataFrame, catalog_config: Dict) -> List[Tuple[str, str]]:
        """
        Validate data against catalog configuration.

        Args:
            df: DataFrame containing the data
            catalog_config: Catalog configuration from YAML

        Returns:
            List of (field, error_message) tuples for failed validations
        """
        errors = []

        for field in catalog_config['fields']:
            field_name = field['name']

            # Skip if field doesn't exist in data
            if field_name not in df.columns:
                errors.append((field_name, "Field not found in data"))
                continue

            # Required field validation
            if field.get('required', False):
                if not cls.validate_required_field(df, field_name):
                    errors.append((field_name, "Field contains null values"))

            # Type validation
            if not all(cls.validate_field_type(value, field['type']) 
                      for value in df[field_name].dropna()):
                errors.append((field_name, f"Invalid type, expected {field['type']}"))

            # Length validation
            if 'length' in field:
                if not all(cls.validate_field_length(value, field['length']) 
                          for value in df[field_name].dropna()):
                    errors.append((field_name, f"Value exceeds maximum length of {field['length']}"))

            # Unique validation
            if field.get('unique', False):
                if not cls.validate_unique_values(df, field_name):
                    errors.append((field_name, "Duplicate values found"))

            # Custom validation expression
            if 'validation_expression' in field:
                if not cls.validate_expression(df, field['validation_expression']):
                    errors.append((field_name, "Failed custom validation"))

        return errors