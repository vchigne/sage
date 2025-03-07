"""Test comprehensive validation cases using pandas Series."""
import os
import pandas as pd
import pytest
from sage.core.processor import SageProcessor
from sage.core.validation_utils import ValidationResult, format_validation_message
import yaml

@pytest.fixture
def validation_data():
    """Load test data and validation rules."""
    base_path = os.path.join('tests', 'test_data', 'validation')
    data_files = {
        'productos': {
            'csv': os.path.join(base_path, 'productos_avanzado.csv'),
            'yaml': os.path.join(base_path, 'productos_avanzado.yaml')
        },
        'ventas': {
            'csv': os.path.join(base_path, 'ventas_avanzado.csv'),
            'yaml': os.path.join(base_path, 'ventas_avanzado.yaml')
        }
    }

    configs = {}
    for key, paths in data_files.items():
        with open(paths['yaml'], 'r') as f:
            configs[key] = yaml.safe_load(f)

    return data_files, configs

def test_productos_validations(validation_data):
    """Test product validation rules with various scenarios."""
    data_files, configs = validation_data
    processor = SageProcessor()

    # Process productos data file
    success, results = processor.process_data(
        data_file=data_files['productos']['csv'],
        yaml_config=configs['productos'],
        upload_type='local',
        sender_id='TEST_PRODUCTOS'
    )

    # Verify validation results
    assert not success, "Validation should fail due to multiple errors"

    # Convert results to list for easier testing
    errors = [r for r in results if r.severity == 'ERROR']
    warnings = [r for r in results if r.severity == 'WARNING']

    # Básicas: Duplicados, formato y campos requeridos
    duplicate_errors = [r for r in errors if 'duplicado' in r.message.lower() or 'único' in r.message.lower()]
    assert len(duplicate_errors) > 0, "Should detect duplicate product codes"

    format_errors = [r for r in errors if 'formato' in r.message.lower()]
    assert len(format_errors) > 0, "Should detect invalid code format"

    required_errors = [r for r in errors if 'obligatorio' in r.message.lower() or 'requerido' in r.message.lower()]
    assert len(required_errors) > 0, "Should detect missing required fields"

    # Negocio: Precios y estados
    price_errors = [r for r in errors if 'precio' in r.field.lower()]
    assert len(price_errors) > 0, "Should detect invalid prices"

    state_errors = [r for r in errors if 'estado' in r.field.lower()]
    assert len(state_errors) > 0, "Should detect invalid states"

    # Categorías y fechas
    category_errors = [r for r in errors if 'categoria' in r.field.lower()]
    assert len(category_errors) > 0, "Should detect invalid categories"

    # Verify simple presence of warnings
    assert len(warnings) > 0, "Should detect validation warnings"

def test_ventas_validations(validation_data):
    """Test sales validation rules with various scenarios."""
    data_files, configs = validation_data
    processor = SageProcessor()

    # Process ventas data file
    success, results = processor.process_data(
        data_file=data_files['ventas']['csv'],
        yaml_config=configs['ventas'],
        upload_type='local',
        sender_id='TEST_VENTAS'
    )

    # Verify validation results
    assert not success, "Validation should fail due to multiple errors"

    # Convert results to list for easier testing
    errors = [r for r in results if r.severity == 'ERROR']
    validation_warnings = [r for r in results if r.severity == 'WARNING']

    # Básicas: Duplicados y formato
    duplicate_errors = [r for r in errors if 'duplicado' in r.message.lower() or 'único' in r.message.lower()]
    assert len(duplicate_errors) > 0, "Should detect duplicate sale codes"

    format_errors = [r for r in errors if 'formato' in r.message.lower()]
    assert len(format_errors) > 0, "Should detect invalid code format"

    # Negocio: Cantidades y totales
    cantidad_errors = [r for r in errors if 'cantidad' in r.field.lower()]
    assert len(cantidad_errors) > 0, "Should detect invalid quantities"

    total_errors = [r for r in errors if 'total' in r.field.lower()]
    assert len(total_errors) > 0, "Should detect total calculation errors"

    # Verify simple presence of warnings
    assert len(validation_warnings) > 0, "Should detect validation warnings"

def test_log_file_generation(validation_data):
    """Test that validation results are properly logged to file."""
    data_files, configs = validation_data
    processor = SageProcessor()

    # Process both data files
    for data_type in ['productos', 'ventas']:
        processor.process_data(
            data_file=data_files[data_type]['csv'],
            yaml_config=configs[data_type],
            upload_type='local',
            sender_id=f'TEST_{data_type.upper()}'
        )

        # Verify log file was created
        log_path = f'logs/local/TEST_{data_type.upper()}/{pd.Timestamp.now().strftime("%Y%m%d")}_validation.log'
        assert os.path.exists(log_path), f"Log file not found at {log_path}"

        # Read log content
        with open(log_path, 'r') as f:
            log_content = f.read()

            # Verify log format and content
            assert '❌' in log_content, "Error messages should be marked with ❌"
            assert '⚠️' in log_content, "Warning messages should be marked with ⚠️"
            assert 'Campo:' in log_content, "Log should include field names"
            assert 'Línea:' in log_content, "Log should include line numbers"
            assert 'Valor:' in log_content, "Log should include invalid values"
            assert 'Regla:' in log_content, "Log should include validation rules"

def test_validation_message_formatting():
    """Test that validation messages are properly formatted with icons and context."""
    # Test basic error message
    result = ValidationResult(
        success=False,
        severity='ERROR',
        message='El código de producto debe ser único',
        field='codigo_producto',
        value='PROD001',
        line_number=2,
        validation_rule='~df["codigo_producto"].duplicated(keep=False)'
    )
    formatted = format_validation_message(result)
    assert '❌' in formatted, "Error icon missing"
    assert '📋 Campo: codigo_producto' in formatted, "Field name missing or wrong format"
    assert '📍 Línea: 2' in formatted, "Line number missing or wrong format"
    assert '📝 Valor: PROD001' in formatted, "Value missing or wrong format"
    assert '🔍 Regla' in formatted, "Rule section missing"
    assert 'debe ser único' in formatted, "Rule explanation missing"

    # Test warning message with context
    result = ValidationResult(
        success=False,
        severity='WARNING',
        message='Descuentos mayores al 50% solo permitidos en pedidos de 100+ unidades',
        field='descuento',
        value=600.00,
        line_number=4,
        validation_rule='~((df["descuento"] / df["total"] > 0.50) & (df["cantidad"] < 100))',
        error_context={
            'descuento': 600.00,
            'total': 1000.00,
            'cantidad': 10
        }
    )
    formatted = format_validation_message(result)
    assert '⚠️' in formatted, "Warning icon missing"
    assert '💰' in formatted, "Money icon missing"
    assert '💡' in formatted, "Hint icon missing"
    assert 'Descuento:' in formatted, "Context missing"
    assert 'Total:' in formatted, "Context missing"
    assert 'Cantidad:' in formatted, "Context missing"

if __name__ == '__main__':
    pytest.main(['-v', __file__])