"""Test the DataProcessor's ZIP handling and pandas validations."""
import os
import yaml
from unittest import mock
from io import BytesIO
import email.message
import smtplib
from src.services.data_processor import DataProcessor, logger
from datetime import datetime
import pandas as pd
import shutil
import time

# Placeholder for the assumed function.  Replace with actual import if available.
from assumed_module import validate_zip_package, db_connection


def test_validation_error_details():
    """Test detailed error messages in validation failures."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Create test data with validation errors
    test_data = {
        'transaction_id': ['TX001', 'TX002', 'TX002'],  # Duplicate ID
        'customer_id': ['CUST001', 'CUST002', 'INVALID'],  # Invalid customer
        'amount': [500.00, -750.50, 1200.75],  # Negative amount
        'date': ['2025-03-05', '2025-03-05', 'invalid-date']  # Invalid date
    }
    df = pd.DataFrame(test_data)

    # Test validation rules
    rules = {
        'fields': [
            {
                'name': 'transaction_id',
                'type': 'text',
                'required': True,
                'unique': True,
                'validation_expression': "df['transaction_id'].duplicated() == False"
            },
            {
                'name': 'amount',
                'type': 'number',
                'required': True,
                'validation_expression': "df['amount'] > 0"
            }
        ],
        'row_validation': {
            'validation_expression': "df['amount'] <= 10000",
            'description': "Individual transaction amount must not exceed 10000"
        }
    }

    # Validate component
    is_valid, error_message = processor.validate_component(df, rules)

    # Verify validation failed with detailed error
    assert not is_valid, "Validation should fail"
    assert "transaction_id" in error_message, "Error should mention field name"
    assert "TX002" in error_message, "Error should include failing value"
    assert "Failed Rows" in error_message, "Error should indicate failing rows"

    # Test package validation with detailed errors
    processor.dataframes = {
        'sales.csv': df,
        'customers.csv': pd.DataFrame({
            'customer_id': ['CUST001', 'CUST002'],
            'name': ['John Doe', 'Jane Smith'],
            'email': ['john@example.com', 'jane@example.com']
        })
    }

    package_rules = {
        'validation_rules': [
            {
                'name': "Customer exists in customers catalog",
                'validation_expression': "df['sales.csv']['customer_id'].isin(df['customers.csv']['customer_id'])"
            }
        ]
    }

    # Validate package
    is_valid, error_message = processor.validate_package(package_rules)

    # Verify package validation failed with details
    assert not is_valid, "Package validation should fail"
    assert "Customer exists in customers catalog" in error_message, "Error should mention rule name"
    assert "Sample Data" in error_message, "Error should include sample data"


def test_package_processing():
    """Test processing a ZIP package with pandas validations."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Load test configurations
    base_path = os.path.join('tests', 'test_data')

    with open(os.path.join(base_path, 'test_package.yaml'), 'r') as f:
        package_config = yaml.safe_load(f)

    # Load test data
    zip_path = os.path.join(base_path, 'test_data_20250305.zip')
    with open(zip_path, 'rb') as f:
        zip_data = f.read()

    # Process the package
    components = processor.extract_package_contents(zip_data, 'test_data_20250305.zip')
    assert len(components) == 2, "Should extract 2 files from ZIP"

    # Process each component with its rules
    for component in components:
        component_rules = package_config['package']['components'][component['filename']]
        df = processor.process_package_component(component, component_rules)
        assert df is not None, f"{component['filename']} processing failed"

    # Validate package-level rules
    is_valid, error = processor.validate_package(package_config['package']['package_validation'])
    assert is_valid, f"Package validation failed: {error}"


def test_sftp_processing():
    """Test SFTP data retrieval and processing."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Clean up any previous processed files records
    with processor.db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM processed_files WHERE sender_id = 'TEST001'")
        processor.db_connection.commit()

    # Load test data
    base_path = os.path.join('tests', 'test_data')
    with open(os.path.join(base_path, 'test_data_20250305.zip'), 'rb') as f:
        test_file_content = f.read()

    # Mock SFTP connection and file operations
    mock_sftp = mock.MagicMock()
    mock_sftp.exists.return_value = True

    # Simulate file download by writing content to BytesIO
    def mock_getfo(remote_path, file_obj):
        file_obj.write(test_file_content)
        file_obj.seek(0)

    mock_sftp.getfo = mock_getfo

    # Create mock Connection context manager
    mock_connection = mock.MagicMock()
    mock_connection.__enter__.return_value = mock_sftp
    mock_connection.__exit__.return_value = None

    # Test SFTP configuration
    sftp_config = {
        'host': 'test.sftp.com',
        'username': 'test_user',
        'password': 'test_password',
        'port': 22,
        'directory': '/test/outgoing'
    }

    expected_file = {
        'filename': 'test_data_20250305.zip'
    }

    # Mock pysftp.Connection to return our mock
    with mock.patch('pysftp.Connection', return_value=mock_connection):
        # First attempt should process successfully
        file_data = processor.process_sftp_data(sftp_config, expected_file, "TEST001")
        assert file_data is not None, "Failed to retrieve file via SFTP"
        assert file_data == test_file_content, "Retrieved file content does not match expected"

        # Second attempt should return original data (already processed)
        file_data = processor.process_sftp_data(sftp_config, expected_file, "TEST001")
        assert file_data == test_file_content, "Should return original data for processed file"


def test_email_processing():
    """Test email data retrieval and processing."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Clean up any previous processed files records
    with processor.db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM processed_files WHERE sender_id = 'TEST001'")
        processor.db_connection.commit()

    # Load test data
    base_path = os.path.join('tests', 'test_data')
    with open(os.path.join(base_path, 'test_data_20250305.zip'), 'rb') as f:
        test_file_content = f.read()

    # Create a mock email message with attachment
    msg = email.message.EmailMessage()
    msg['Subject'] = 'Test Package - 2025-03-05'
    msg['From'] = 'test.user@example.com'
    msg['To'] = 'data@test.com'
    msg.add_attachment(
        test_file_content,
        maintype='application',
        subtype='zip',
        filename='test_data_20250305.zip'
    )

    # Mock IMAP4_SSL connection and message retrieval
    mock_imap = mock.MagicMock()
    mock_imap.search.return_value = ('OK', [b'1'])
    mock_imap.fetch.return_value = ('OK', [(b'1', msg.as_bytes())])

    # Test email configuration
    email_config = {
        'host': 'imap.test.com',
        'username': 'test_user',
        'password': 'test_password',
        'allowed_senders': ['test.user@example.com'],
        'receiving_email': 'data@test.com',
        'subject_format': 'Test Package - {date}'
    }

    expected_file = {
        'filename': 'test_data_20250305.zip',
        'subject_pattern': 'Test Package - 2025-03-05'
    }

    # Mock imaplib.IMAP4_SSL to return our mock
    with mock.patch('imaplib.IMAP4_SSL', return_value=mock_imap):
        # First attempt should process successfully
        file_data = processor.process_email_data(email_config, expected_file, "TEST001")
        assert file_data is not None, "Failed to retrieve file from email"
        assert file_data == test_file_content, "Retrieved file content does not match expected"

        # Second attempt should return original data (already processed)
        file_data = processor.process_email_data(email_config, expected_file, "TEST001")
        assert file_data == test_file_content, "Should return original data for processed file"


def test_api_processing():
    """Test API data retrieval and processing."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Clean up any previous processed files records
    with processor.db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM processed_files WHERE sender_id = 'TEST001'")
        processor.db_connection.commit()

    # Load test data
    base_path = os.path.join('tests', 'test_data')
    with open(os.path.join(base_path, 'test_data_20250305.zip'), 'rb') as f:
        test_file_content = f.read()

    # Create mock response
    mock_response = mock.MagicMock()
    mock_response.ok = True
    mock_response.content = test_file_content

    # Test API configuration
    api_config = {
        'endpoint': 'https://api.test.com/upload',
        'api_key': 'test_api_key',
        'method': 'POST'
    }

    expected_file = {
        'filename': 'test_data_20250305.zip'
    }

    # Mock requests.request to return our mock response
    with mock.patch('requests.request', return_value=mock_response) as mock_request:
        # First attempt should process successfully
        file_data = processor.process_api_data(api_config, expected_file, "TEST001")
        assert file_data is not None, "Failed to retrieve file from API"
        assert file_data == test_file_content, "Retrieved file content does not match expected"

        # Second attempt should return original data (already processed)
        file_data = processor.process_api_data(api_config, expected_file, "TEST001")
        assert file_data == test_file_content, "Should return original data for processed file"

        # Verify API request was made correctly
        mock_request.assert_called_with(
            method='POST',
            url='https://api.test.com/upload',
            headers={'Authorization': f'Bearer {api_config["api_key"]}'}
        )


def test_execution_history():
    """Test execution history recording and notifications."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Mock SMTP for notifications
    mock_smtp = mock.MagicMock()
    mock_smtp.__enter__.return_value = mock_smtp

    # Load test configurations
    base_path = os.path.join('tests', 'test_data')
    with open(os.path.join(base_path, 'test_sender.yaml'), 'r') as f:
        sender_config = yaml.safe_load(f)['senders']

    yaml_id = "test-yaml-001"

    # Execute processor with mocked notifications
    with mock.patch('smtplib.SMTP', return_value=mock_smtp):
        # Start execution
        exec_id = processor.start_execution(yaml_id)
        assert exec_id is not None, "Failed to start execution"

        # Simulate processing
        processor.notify_receivers(sender_config, 'Running', 'Processing started')
        logger.info("Processing test data...")
        logger.info("Validating data...")
        logger.info("Saving results...")

        # Update execution status
        processor.update_execution_status('completed')
        processor.notify_receivers(sender_config, 'Success', 'Processing completed successfully')

        # Verify execution was recorded
        with processor.db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT status, log_content FROM execution_history WHERE id = %s",
                (exec_id,)
            )
            status, log_content = cursor.fetchone()
            assert status == 'completed', "Execution status not updated correctly"
            assert "Processing test data..." in log_content, "Logs not captured correctly"
            assert "Validating data..." in log_content, "Logs not captured correctly"
            assert "Saving results..." in log_content, "Logs not captured correctly"

            # Verify notifications were recorded
            cursor.execute(
                """
                SELECT COUNT(*) FROM notifications 
                WHERE execution_id = %s AND content LIKE %s
                """,
                (exec_id, '%Processing completed successfully%')
            )
            completion_notifications = cursor.fetchone()[0]
            assert completion_notifications > 0, "Completion notification not recorded"


def test_error_notifications():
    """Test that error notifications include detailed validation failures."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Mock SMTP for notifications
    mock_smtp = mock.MagicMock()
    mock_smtp.__enter__.return_value = mock_smtp

    # Create test data with validation errors
    test_data = {
        'transaction_id': ['TX001', 'TX002', 'TX002'],  # Duplicate ID
        'customer_id': ['CUST001', 'CUST002', 'INVALID'],  # Invalid customer
        'amount': [500.00, -750.50, 1200.75],  # Negative amount
        'date': ['2025-03-05', '2025-03-05', 'invalid-date']  # Invalid date
    }
    df = pd.DataFrame(test_data)

    # Load test sender configuration
    base_path = os.path.join('tests', 'test_data')
    with open(os.path.join(base_path, 'test_sender.yaml'), 'r') as f:
        sender_config = yaml.safe_load(f)['senders']

    # Execute processor with mocked notifications
    with mock.patch('smtplib.SMTP', return_value=mock_smtp):
        # Start execution
        exec_id = processor.start_execution("test-yaml-002")

        # Get validation error
        rules = {
            'fields': [
                {
                    'name': 'transaction_id',
                    'type': 'text',
                    'required': True,
                    'unique': True,
                    'validation_expression': "df['transaction_id'].duplicated() == False"
                }
            ]
        }
        component_name = "sales_data.csv"
        is_valid, error_message = processor.validate_component(df, rules, component_name)

        # Send error notification
        processor.notify_receivers(sender_config, 'Failed', error_message)
        processor.update_execution_status('failed', error_message)

        # Verify notification was recorded with error details
        with processor.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT content FROM notifications 
                WHERE execution_id = %s AND content LIKE %s
                """,
                (exec_id, '%Failed%')
            )
            notification_content = cursor.fetchone()[0]

            # Verify error details are included
            assert f"Validation Error in {component_name}" in notification_content, "Notification should include component name"
            assert "Field: transaction_id" in notification_content, "Notification should include field name"
            assert "TX002" in notification_content, "Notification should include invalid value"
            assert "Failed Rows" in notification_content, "Notification should indicate failing rows"


def test_filesystem_processing():
    """Test filesystem data processing with duplicate detection."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Clean up any previous processed files records
    with processor.db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM processed_files WHERE sender_id = 'TEST001'")
        processor.db_connection.commit()

    # Load test data
    base_path = os.path.join('tests', 'test_data')
    with open(os.path.join(base_path, 'test_data_20250305.zip'), 'rb') as f:
        test_file_content = f.read()

    # Set up test directories
    test_watch_dir = os.path.join(base_path, 'watch')
    test_processed_dir = os.path.join(base_path, 'processed')
    test_error_dir = os.path.join(base_path, 'error')

    os.makedirs(test_watch_dir, exist_ok=True)
    os.makedirs(test_processed_dir, exist_ok=True)
    os.makedirs(test_error_dir, exist_ok=True)

    # Copy test file to watch directory
    test_file_path = os.path.join(test_watch_dir, 'test_data_20250305.zip')
    with open(test_file_path, 'wb') as f:
        f.write(test_file_content)

    # Test filesystem configuration
    fs_config = {
        'watch_directory': test_watch_dir,
        'processed_directory': test_processed_dir,
        'error_directory': test_error_dir
    }

    expected_file = {
        'filename': 'test_data_20250305.zip'
    }

    # First processing should succeed
    file_data = processor.process_filesystem_data(fs_config, expected_file, "TEST001")
    assert file_data is not None, "Failed to process file from filesystem"
    assert file_data == test_file_content, "Retrieved file content does not match expected"

    # Copy file again to test duplicate detection
    with open(test_file_path, 'wb') as f:
        f.write(test_file_content)

    # Second processing should detect duplicate
    file_data = processor.process_filesystem_data(fs_config, expected_file, "TEST001")
    assert file_data is None, "Duplicate file was not detected"

    # Clean up test directories
    shutil.rmtree(test_watch_dir)
    shutil.rmtree(test_processed_dir)
    shutil.rmtree(test_error_dir)


def test_direct_upload():
    """Test direct upload processing with duplicate detection."""
    # Initialize processor
    processor = DataProcessor()
    processor.setup_database()

    # Clean up any previous processed files records
    with processor.db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM processed_files WHERE sender_id = 'TEST001'")
        processor.db_connection.commit()

    # Load test data
    base_path = os.path.join('tests', 'test_data')
    with open(os.path.join(base_path, 'test_data_20250305.zip'), 'rb') as f:
        test_file_content = f.read()

    # Test direct upload configuration
    upload_config = {
        'max_file_size_mb': 100,
        'allowed_ips': ['127.0.0.1'],
        'require_2fa': True
    }

    # First upload should succeed
    success = processor.process_direct_upload(
        upload_config,
        test_file_content,
        'test_data_20250305.zip',
        "TEST001"
    )
    assert success, "Direct upload processing failed"

    # Second upload should detect duplicate
    success = processor.process_direct_upload(
        upload_config,
        test_file_content,
        'test_data_20250305.zip',
        "TEST001"
    )
    assert not success, "Duplicate file was not detected"

    # Test file size limit
    large_content = b'x' * (upload_config['max_file_size_mb'] * 1024 * 1024 + 1)
    success = processor.process_direct_upload(
        upload_config,
        large_content,
        'large_file.zip',
        "TEST001"
    )
    assert not success, "File size limit was not enforced"


def test_duplicate_package_detection():
    """Probar la detección de paquetes duplicados considerando fechas."""
    # Cargar datos de prueba
    base_path = os.path.join('tests', 'test_data')
    package_path = os.path.join(base_path, 'test_package.yaml')
    sender_path = os.path.join(base_path, 'test_sender.yaml')
    test_zip = os.path.join(base_path, 'test_data_20250305.zip')

    # Limpiar registros previos
    with db_connection.cursor() as cursor:
        cursor.execute("DELETE FROM processed_packages")
        db_connection.commit()

    # Primera carga - debería ser exitosa
    errors = validate_zip_package(
        test_zip,
        package_path,
        sender_path,
        os.path.join(base_path, 'catalogs')
    )
    assert not errors, "Primera carga debería ser exitosa"

    # Intentar procesar el mismo archivo - debería detectar duplicado
    errors = validate_zip_package(
        test_zip,
        package_path,
        sender_path,
        os.path.join(base_path, 'catalogs')
    )
    assert len(errors) == 1, "Debería detectar duplicado"
    assert "Paquete duplicado" in errors[0], "Mensaje incorrecto para duplicado"

    # Simular archivo más reciente modificando el timestamp
    future_time = time.time() + 3600  # Una hora en el futuro
    os.utime(test_zip, (future_time, future_time))

    # Intentar procesar versión más reciente - debería ser exitosa
    errors = validate_zip_package(
        test_zip,
        package_path,
        sender_path,
        os.path.join(base_path, 'catalogs')
    )
    assert not errors, "Versión más reciente debería ser aceptada"

    # Verificar registros en base de datos
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM processed_packages")
        count = cursor.fetchone()[0]
        assert count == 2, "Deberían haber dos registros de procesamiento"



if __name__ == '__main__':
    test_package_processing()
    test_sftp_processing()
    test_email_processing()
    test_api_processing()
    test_execution_history()
    test_validation_error_details()
    test_error_notifications()
    test_filesystem_processing()
    test_direct_upload()
    test_duplicate_package_detection()
    print("✅ All tests passed!")

"""Test the SageProcessor with notifications and logs."""
import os
import shutil
import pytest
from datetime import datetime
import pandas as pd
from sage.core.processor import SageProcessor
from sage.core.yaml_loader import YAMLLoader
import yaml

def test_validate_field_error_messages():
    """Test that field validations generate detailed error messages."""
    # Setup test data with known validation failures
    test_data = {
        'codigo_producto': ['PROD001', 'PROD001', 'PROD002'],  # Duplicate
        'nombre_producto': ['Test 1', None, 'Test 3'],  # Null value
        'precio_lista': [100.0, -50.0, 200.0],  # Negative price
        'estado': ['Activo', 'Invalid', 'Proximamente']  # Invalid state
    }
    df = pd.DataFrame(test_data)

    # Create field validation rules
    field_rules = [
        {
            'name': 'codigo_producto',
            'validation_expression': '~df["codigo_producto"].duplicated(keep=False)',
            'message': 'El código de producto debe ser único',
            'severity': 'ERROR'
        },
        {
            'name': 'nombre_producto',
            'validation_expression': 'df["nombre_producto"].notna()',
            'message': 'El nombre del producto es requerido',
            'severity': 'ERROR'
        },
        {
            'name': 'precio_lista',
            'validation_expression': 'df["precio_lista"] > 0',
            'message': 'El precio debe ser mayor a 0',
            'severity': 'ERROR'
        },
        {
            'name': 'estado',
            'validation_expression': 'df["estado"].isin(["Activo", "Descontinuado", "Proximamente"])',
            'message': 'Estado inválido',
            'severity': 'WARNING'
        }
    ]

    processor = SageProcessor()

    # Validate each field and collect results
    all_results = []
    for field_rule in field_rules:
        results = processor.validate_field(df, field_rule)
        all_results.extend(results)

    # Verify duplicates are identified (both rows)
    duplicate_errors = [r for r in all_results if r.field == 'codigo_producto']
    assert len(duplicate_errors) == 2, "Both duplicate rows should be marked"
    assert all(r.value == 'PROD001' for r in duplicate_errors), "Incorrect duplicate value"
    assert {r.line_number for r in duplicate_errors} == {2, 3}, "Incorrect line numbers for duplicates"

    # Verify null name is identified
    null_name_errors = [r for r in all_results if r.field == 'nombre_producto']
    assert len(null_name_errors) == 1, "Should have one null name error"
    assert null_name_errors[0].line_number == 3, "Incorrect line number for null name"

    # Verify negative price is identified
    price_errors = [r for r in all_results if r.field == 'precio_lista']
    assert len(price_errors) == 1, "Should have one price error"
    assert price_errors[0].value == -50.0, "Incorrect price value"
    assert price_errors[0].line_number == 3, "Incorrect line number for price"

    # Verify invalid state is identified
    state_errors = [r for r in all_results if r.field == 'estado']
    assert len(state_errors) == 1, "Should have one state error"
    assert state_errors[0].value == 'Invalid', "Incorrect state value"
    assert state_errors[0].line_number == 3, "Incorrect line number for state"


@pytest.fixture(scope="function")
def setup_test_env():
    """Setup test environment with required directories."""
    # Create test directories
    os.makedirs('logs/sftp/TEST001', exist_ok=True)
    os.makedirs('logs/local/TEST002', exist_ok=True)

    # Print debug info about directories
    print("\nTest Environment Setup:")
    print(f"SFTP log dir: {os.path.abspath('logs/sftp/TEST001')}")
    print(f"Local log dir: {os.path.abspath('logs/local/TEST002')}")

    yield

    # Print directory contents before cleanup
    print("\nDirectory contents before cleanup:")
    if os.path.exists('logs/sftp/TEST001'):
        print("SFTP logs:", os.listdir('logs/sftp/TEST001'))
    if os.path.exists('logs/local/TEST002'):
        print("Local logs:", os.listdir('logs/local/TEST002'))

    # Comment out cleanup temporarily for debugging
    # shutil.rmtree('logs/sftp/TEST001', ignore_errors=True)
    # shutil.rmtree('logs/local/TEST002', ignore_errors=True)


def test_process_data_with_notifications(setup_test_env):
    """Test processing data with notifications."""
    # Setup test data
    data_file = 'data/files/csv/productos_test.csv'

    # Load test package configuration from YAML
    with open('tests/test_data/valid/test_package.yaml', 'r') as f:
        package_config = yaml.safe_load(f)
        # Get validation rules from the Productos catalog
        productos_config = next(
            catalog for catalog in package_config['package']['catalogs']
            if catalog['name'] == 'Productos'
        )
        validation_rules = productos_config['validation_rules']

    # Create catalog configuration with rules from YAML
    yaml_config = {
        'catalog': {
            'fields': [
                {
                    'name': 'codigo_producto',
                    'type': 'text',
                    'required': True,
                    'unique': True,
                    'validation_expression': validation_rules[0]['validation_expression'],
                    'message': validation_rules[0]['message'],
                    'severity': validation_rules[0]['severity']
                },
                {
                    'name': 'nombre_producto',
                    'type': 'text',
                    'validation_expression': validation_rules[1]['validation_expression'],
                    'message': validation_rules[1]['message'],
                    'severity': validation_rules[1]['severity']
                },
                {
                    'name': 'precio_lista',
                    'type': 'number',
                    'validation_expression': validation_rules[2]['validation_expression'],
                    'message': validation_rules[2]['message'],
                    'severity': validation_rules[2]['severity']
                },
                {
                    'name': 'estado',
                    'type': 'text',
                    'validation_expression': validation_rules[3]['validation_expression'],
                    'message': validation_rules[3]['message'],
                    'severity': validation_rules[3]['severity']
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

    # Print debug info
    print(f"\nChecking log path: {os.path.abspath('logs/sftp/TEST001')}")
    print(f"Directory exists: {os.path.exists('logs/sftp/TEST001')}")
    print(f"Directory contents: {os.listdir('logs/sftp/TEST001') if os.path.exists('logs/sftp/TEST001') else 'N/A'}")

    # Verify local log was created
    log_path = f'logs/sftp/TEST001/{datetime.now().strftime("%Y%m%d")}_validation.log'
    assert os.path.exists(log_path), f"Log file not found at {log_path}"

    # Read log content
    with open(log_path, 'r') as f:
        log_content = f.read()
        print(f"\nLog content:\n{log_content}")

    # Verify that only validation rules from YAML generated messages
    for validation_rule in validation_rules:
        if validation_rule['severity'] == 'ERROR':
            assert validation_rule['message'] in log_content, f"Missing validation message: {validation_rule['message']}"
        else:  # WARNING
            # Warning messages might not appear if data doesn't trigger them
            if validation_rule['message'] in log_content:
                assert '⚠️' in log_content, "Warning emoji missing for warning message"

    # Verify message formatting for each line
    for line in log_content.split('\n'):
        if line.strip() and not line.startswith('===') and not line.startswith('✅'):
            # Each validation message should have the format:
            # [emoji] Message | Campo: X | Línea: Y | Valor: Z [ | Regla: R]
            parts = line.split('|')
            assert len(parts) >= 3, f"Line missing required parts: {line}"
            assert any(emoji in parts[0] for emoji in ['❌', '⚠️', 'ℹ️']), f"Missing severity emoji: {line}"
            assert 'Campo:' in parts[1], f"Missing field name: {line}"
            if 'Línea:' in line:
                assert any(str(i) in line for i in range(1, 5)), f"Invalid line number: {line}"


def test_notification_message_format(setup_test_env):
    """Test notification message formatting."""
    # Setup test data with known errors
    data_file = 'data/files/csv/productos_test.csv'

    # Load test package configuration from YAML
    with open('tests/test_data/valid/test_package.yaml', 'r') as f:
        package_config = yaml.safe_load(f)
        # Get validation rules from the Productos catalog
        productos_config = next(
            catalog for catalog in package_config['package']['catalogs']
            if catalog['name'] == 'Productos'
        )
        validation_rules = productos_config['validation_rules']

    yaml_config = {
        'catalog': {
            'fields': [
                {
                    'name': 'codigo_producto',
                    'type': 'text',
                    'validation_expression': validation_rules[0]['validation_expression'],
                    'message': validation_rules[0]['message'],
                    'severity': validation_rules[0]['severity']
                },
                {
                    'name': 'nombre_producto',
                    'type': 'text',
                    'validation_expression': validation_rules[1]['validation_expression'],
                    'message': validation_rules[1]['message'],'severity': validation_rules[1]['severity']
                },
                {
                    'name': 'precio_lista',
                    'type': 'number',
                    'validation_expression': validation_rules[2]['validation_expression'],
                    'message': validation_rules[2]['message'],
                    'severity': validation_rules[2]['severity']
                },
                {
                    'name': 'estado',
                    'type': 'text',
                    'validation_expression': validation_rules[3]['validation_expression'],
                    'message': validation_rules[3]['message'],
                    'severity': validation_rules[3]['severity']
                }
            ]
        }
    }

    # Process data with local upload type
    processor = SageProcessor()
    success, results = processor.process_data(
        data_file=data_file,
        yaml_config=yaml_config,
        upload_type='local',
        sender_id='TEST002'
    )

    # Print debug info
    print(f"\nChecking log path: {os.path.abspath('logs/local/TEST002')}")
    print(f"Directory exists: {os.path.exists('logs/local/TEST002')}")
    print(f"Directory contents: {os.listdir('logs/local/TEST002') if os.path.exists('logs/local/TEST002') else 'N/A'}")

    # Verify local log was created
    log_path = f'logs/local/TEST002/{datetime.now().strftime("%Y%m%d")}_validation.log'
    assert os.path.exists(log_path), f"Log file not found at {log_path}"

    with open(log_path, 'r') as f:
        log_content = f.read()
        print(f"\nLog content:\n{log_content}")

    # Verify validation rules from YAML are applied
    for validation_rule in validation_rules:
        if validation_rule['severity'] == 'ERROR':
            assert validation_rule['message'] in log_content, f"Missing validation message: {validation_rule['message']}"
        else:  # WARNING
            # Warning messages might not appear if data doesn't trigger them
            if validation_rule['message'] in log_content:
                assert '⚠️' in log_content, "Warning emoji missing for warning message"

    # Verify message formatting
    for line in log_content.split('\n'):
        if line.strip():
            # Each non-empty line should have the format:
            # [emoji] Message | Campo: X | Línea: Y | Valor: Z [ | Regla: R]
            parts = line.split('|')
            assert len(parts) >= 3, f"Line missing required parts: {line}"
            assert any(emoji in parts[0] for emoji in ['❌', '⚠️', 'ℹ️']), f"Missing severity emoji: {line}"
            assert 'Campo:' in parts[1], f"Missing field name: {line}"
            if 'Línea:' in line:
                assert any(str(i) in line for i in range(1, 5)), f"Invalid line number: {line}"