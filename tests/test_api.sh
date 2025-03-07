#!/bin/bash

# Test root endpoint
echo "Testing root endpoint..."
curl http://localhost:5000/

# Test YAML validation
echo -e "\n\nTesting YAML validation..."
curl -X POST http://localhost:5000/api/validate-yaml \
  -F "file=@data/yaml/catalog/productos.yaml" \
  -F "schema_type=catalog"

# Test package processing
echo -e "\n\nTesting package processing..."
curl -X POST http://localhost:5000/api/process-package \
  -F "zip_file=@data/files/zip/mixed_files.zip" \
  -F "package_yaml=@data/yaml/package/package.yaml" \
  -F "catalogs_dir=data/yaml/catalog"

# Test sender validation
echo -e "\n\nTesting sender validation..."
curl -X POST http://localhost:5000/api/validate-sender \
  -F "file=@data/yaml/sender/sender.yaml" \
  -F "package_name=Maestro de Productos Oficial"