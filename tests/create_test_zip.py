"""Script to create test ZIP file for package validation."""
import os
import zipfile
from datetime import datetime

def create_test_zip():
    """Create a test ZIP file with sample data."""
    # Create test data directory
    test_data_dir = os.path.join('tests', 'test_data', 'temp_files')
    os.makedirs(test_data_dir, exist_ok=True)

    # Create sample CSV file
    csv_content = """codigo_producto,nombre,precio,estado
PROD001,Producto Test 1,99.99,Activo
PROD002,Producto Test 2,149.99,Activo"""

    csv_file = os.path.join(test_data_dir, 'productos.csv')
    with open(csv_file, 'w') as f:
        f.write(csv_content)

    # Create ZIP file
    today = datetime.now().strftime('%Y%m%d')
    zip_path = os.path.join('tests', 'test_data', f'test_data_{today}.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_file, os.path.basename(csv_file))

    print(f"✅ Created test ZIP file: {zip_path}")
    return zip_path

if __name__ == '__main__':
    create_test_zip()
