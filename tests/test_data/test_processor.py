"""Test the SageProcessor with notifications and logs."""
import os
import pytest
from sage.core.processor import SageProcessor
from sage.core.yaml_loader import YAMLLoader

def test_process_data_with_notifications():
    """Test processing data with notifications."""
    # Setup test data
    data_file = 'data/files/csv/productos_ejemplo.csv'
    yaml_config = {
        'catalog': {
            'fields': [
                {
                    'name': 'codigo_producto',
                    'type': 'text',
                    'required': True,
                    'unique': True,
                    'message': 'El código de producto es obligatorio y debe ser único'
                },
                {
                    'name': 'nombre_producto',
                    'type': 'text',
                    'required': True,
                    'message': 'El nombre del producto es obligatorio'
                }
            ]
        }
    }
    
    # Setup sender config for notifications
    sender_config = {
        'data_receivers': [
            {
                'name': 'Test Data Hub',
                'email': 'test@example.com'
            }
        ]
    }

    # Process data with SFTP upload type
    processor = SageProcessor()
    success, results = processor.process_data(
        data_file=data_file,
        yaml_config=yaml_config,
        upload_type='sftp',
        sender_id='TEST001',
        sender_config=sender_config,
        package_name='Test Package'
    )

    # Verify local log was created
    log_path = f'logs/sftp/TEST001/{datetime.now().strftime("%Y%m%d")}_validation.log'
    assert os.path.exists(log_path)

    # Read log content
    with open(log_path, 'r') as f:
        log_content = f.read()

    # Verify log format
    assert '❌' in log_content  # Error messages
    assert '⚠️' in log_content  # Warning messages
    assert 'Campo:' in log_content  # Field name
    assert 'Línea:' in log_content  # Line number
    assert 'Valor:' in log_content  # Invalid value
    assert 'Regla:' in log_content  # Validation rule
