"""Core processor for SAGE data validation and processing."""
import numpy as np  # Add explicit numpy import
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from ..utils.logger import get_logger
from ..utils.exceptions import ProcessingError
from .local_logger import LocalLogger
from .notifications import NotificationManager
from .validation_utils import ValidationResult, format_validation_message

logger = get_logger(__name__)

class SageProcessor:
    """Base processor class for SAGE data validation and processing."""

    def __init__(self):
        """Initialize the processor."""
        self.logger = logger

    def validate_field(self, df: pd.DataFrame, field: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate a single field in the DataFrame based on YAML rules.
        Each rule should return a Series of booleans where False indicates a validation failure.
        """
        results = []
        field_name = field['name']
        severity = field.get('severity', 'ERROR')
        message = field.get('message', '')
        validation_expression = field.get('validation_expression')

        logger.debug(f"Validando campo: {field_name}")
        logger.debug(f"Expresión de validación: {validation_expression}")

        # Check if field exists
        if field_name not in df.columns:
            results.append(ValidationResult(
                success=False,
                severity=severity,
                message=message or f"Campo faltante: {field_name}",
                field=field_name
            ))
            return results

        # Apply validation expression if present
        if validation_expression:
            try:
                # Create evaluation context
                eval_context = {
                    "df": df,
                    "pd": pd,
                    "to_datetime": pd.to_datetime,
                    "Timestamp": pd.Timestamp,
                    "now": pd.Timestamp.now,
                    "np": np  # Add numpy for numeric operations
                }

                # Handle date validations - only format validation
                if 'to_datetime' in validation_expression:
                    validation_expression = validation_expression.replace(
                        'pd.to_datetime(df[',
                        'pd.to_datetime(df['
                    ).replace(
                        '])',
                        '], errors="coerce")'
                    )

                # Handle duplicated checks - process them specially
                if '~df' in validation_expression and '.duplicated' in validation_expression:
                    # First get the duplicated values without negation
                    original_field = validation_expression.split("'")[1]
                    duplicates = df[original_field].duplicated(keep=False)

                    if duplicates.any():
                        # Create mask for duplicated values
                        duplicate_values = df[duplicates][original_field].unique()

                        # For each duplicate value, create a ValidationResult
                        for value in duplicate_values:
                            value_mask = df[original_field] == value
                            duplicate_indices = df[value_mask].index

                            for idx in duplicate_indices:
                                results.append(ValidationResult(
                                    success=False,
                                    severity=severity,
                                    message=message or f"Valor duplicado encontrado: {value}",
                                    field=field_name,
                                    value=value,
                                    line_number=idx + 2,  # +2 for header and 0-based index
                                    validation_rule=validation_expression,
                                    error_context={'duplicate_value': value}
                                ))
                        return results

                logger.debug(f"Expresión de validación: {validation_expression}")

                # Evaluate validation expression - should return a Series of booleans
                validation_result = eval(validation_expression, eval_context)
                logger.debug(f"Resultado validación para {field_name}:")
                logger.debug(f"- Tipo: {type(validation_result)}")
                logger.debug(f"- Valor: {validation_result}")

                # Handle Series results - each False value indicates a validation failure
                if isinstance(validation_result, pd.Series):
                    # For date validations, handle NaT values
                    if pd.api.types.is_datetime64_any_dtype(validation_result):
                        validation_result = validation_result.notna()

                    # Ensure we have a boolean Series
                    validation_result = validation_result.astype(bool)

                    # Get rows that failed validation
                    invalid_mask = ~validation_result
                    invalid_rows = df[invalid_mask]

                    if len(invalid_rows) > 0:
                        logger.debug(f"Filas inválidas encontradas ({len(invalid_rows)}):")
                        logger.debug(f"- Índices: {invalid_rows.index.tolist()}")
                        logger.debug(f"- Valores: {invalid_rows[field_name].tolist()}")

                        # For each failing row, create a validation result with context
                        for idx, row in invalid_rows.iterrows():
                            # Extract fields referenced in the validation expression
                            related_fields = self._get_related_fields(validation_expression)
                            error_context = {}

                            # Include context for referenced fields
                            if related_fields:
                                for rel_field in related_fields:
                                    if rel_field in row.index and rel_field != field_name:
                                        error_context[rel_field] = row[rel_field]

                            # Include special handling for date validations
                            if 'to_datetime' in validation_expression:
                                try:
                                    pd.to_datetime(row[field_name])
                                except Exception as e:
                                    error_context['error'] = str(e)

                            # Include special handling for complex business rules
                            if '|' in validation_expression or '&' in validation_expression:
                                # Log the specific condition that failed
                                error_context['validation'] = validation_expression

                            # Include special handling for regex patterns
                            if '.str.match' in validation_expression:
                                error_context['pattern'] = validation_expression.split("r'")[1].split("'")[0]

                            results.append(ValidationResult(
                                success=False,
                                severity=severity,
                                message=message,
                                field=field_name,
                                value=row[field_name],
                                line_number=idx + 2,  # +2 for header and 0-based index
                                validation_rule=validation_expression,
                                error_context=error_context
                            ))

                # Handle scalar results (should be rare, mainly for aggregations)
                elif isinstance(validation_result, (bool, int, float)):
                    if not bool(validation_result):
                        logger.debug("Validación escalar falló")
                        results.append(ValidationResult(
                            success=False,
                            severity=severity,
                            message=message,
                            field=field_name,
                            validation_rule=validation_expression
                        ))
                else:
                    error_msg = f"Tipo de resultado no soportado: {type(validation_result)}"
                    logger.error(error_msg)
                    results.append(ValidationResult(
                        success=False,
                        severity='ERROR',
                        message=error_msg,
                        field=field_name,
                        validation_rule=validation_expression
                    ))

            except Exception as e:
                error_msg = f"Error evaluando regla: {str(e)}"
                logger.error(error_msg)
                results.append(ValidationResult(
                    success=False,
                    severity='ERROR',
                    message=error_msg,
                    field=field_name,
                    validation_rule=validation_expression
                ))

        return results

    def _get_related_fields(self, validation_expression: str) -> List[str]:
        """Extract field names referenced in a validation expression."""
        related_fields = []
        try:
            # Look for df['field_name'] patterns
            import re
            matches = re.findall(r"df\['([^']+)'\]", validation_expression)
            related_fields.extend(matches)
        except Exception as e:
            logger.warning(f"Error extracting related fields: {str(e)}")
        return list(set(related_fields))  # Remove duplicates

    def validate_data(self, df: pd.DataFrame, config: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate DataFrame against YAML configuration rules.
        Each validation rule should return a Series of booleans for row-level validations,
        or a single boolean for catalog-level validations.
        """
        logger.debug("Iniciando validación de datos")
        results = []

        # Field validations
        for field in config.get('fields', []):
            field_name = field['name']
            logger.debug(f"Procesando campo: {field_name}")
            logger.debug(f"Regla de validación: {field.get('validation_expression')}")

            field_results = self.validate_field(df, field)

            if field_results:
                logger.debug(f"Resultados para {field_name}:")
                for result in field_results:
                    logger.debug(f"- Fila {result.line_number}: {result.message}")
                    if result.error_context:
                        logger.debug(f"  Contexto: {result.error_context}")

            results.extend(field_results)

        return results

    def process_data(self, 
                    data_file: str,
                    yaml_config: Dict[str, Any],
                    upload_type: Optional[str] = None,
                    sender_id: Optional[str] = None,
                    **kwargs) -> Tuple[bool, List[ValidationResult]]:
        """Process a data file according to YAML configuration."""
        try:
            # Read the data
            df = self.read_data_file(data_file)
            logger.debug(f"Datos cargados: \n{df}")

            # Validate the data according to YAML rules
            results = self.validate_data(df, yaml_config['catalog'])
            logger.debug(f"Resultados de validación: {[r.to_dict() for r in results]}")

            # Only consider error severity for success/failure
            error_results = [r for r in results if r.severity == 'ERROR']
            success = len(error_results) == 0

            # If this is an SFTP or local directory upload, log to file
            if upload_type in ['sftp', 'local'] and sender_id:
                local_logger = LocalLogger()
                package_info = {
                    'name': kwargs.get('package_name', 'N/A'),
                    'counts': {
                        'registros': len(df) if success else 0
                    }
                }
                local_logger.log_validation_results(
                    results, 
                    upload_type, 
                    sender_id,
                    package_info
                )

            # If sender config is provided, send notifications
            sender_config = kwargs.get('sender_config')
            if sender_config:
                notification_manager = NotificationManager(sender_config)
                notification_manager.notify_receivers(
                    results,
                    kwargs.get('package_name', 'N/A'),
                    package_info if success else None
                )

            return success, results

        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}")
            return False, [ValidationResult(
                success=False,
                severity='ERROR',
                message=f"Error procesando archivo: {str(e)}",
                field='file_processing'
            )]

    def read_data_file(self, file_path: str) -> pd.DataFrame:
        """Read data from a file into a DataFrame."""
        try:
            # Determine file type and read data
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_path}")

            self.logger.debug(f"Archivo cargado exitosamente: {file_path}")
            return df

        except Exception as e:
            error_msg = f"Error leyendo archivo {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ProcessingError(error_msg)