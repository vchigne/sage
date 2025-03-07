import os
import zipfile
import pandas as pd
from io import BytesIO

def test_read_zip_excel():
    """Test reading an Excel file from within a ZIP file"""
    # Path to the test ZIP file
    zip_path = 'attached_assets/Maestro productos Alicorp.zip'
    
    print(f"\nTesting ZIP file: {zip_path}")
    print("--------------------")
    
    # Verify the file exists
    assert os.path.exists(zip_path), f"ZIP file not found at {zip_path}"
    print("✓ ZIP file exists")
    
    # Open and read the ZIP file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # List contents
        contents = zip_ref.namelist()
        print(f"\nZIP contents: {contents}")
        
        # Find Excel files
        excel_files = [f for f in contents if f.endswith(('.xlsx', '.xls'))]
        assert len(excel_files) > 0, "No Excel files found in ZIP"
        print(f"✓ Found Excel files: {excel_files}")
        
        # Read the first Excel file
        excel_file = excel_files[0]
        with zip_ref.open(excel_file) as excel:
            # Read Excel content into pandas
            df = pd.read_excel(BytesIO(excel.read()))
            
            # Display basic information
            print(f"\nExcel file: {excel_file}")
            print(f"Number of rows: {len(df)}")
            print(f"Number of columns: {len(df.columns)}")
            print("\nColumns:")
            for col in df.columns:
                print(f"- {col}")
            
            # Display first few rows
            print("\nFirst 5 rows:")
            print(df.head().to_string())
            
            return df

if __name__ == "__main__":
    test_read_zip_excel()
