# Directorio de Datos para SAGE

Este directorio contiene los archivos y configuraciones para probar SAGE.

## Estructura

```
data/
├── yaml/                   # Archivos de configuración YAML
│   ├── catalog/           # YAMLs de catálogos
│   ├── package/           # YAMLs de paquetes
│   ├── sender/            # YAMLs de emisores
│   └── examples/          # Ejemplos de YAMLs
│
└── files/                 # Archivos de datos
    ├── excel/            # Archivos Excel (.xlsx, .xls)
    ├── csv/              # Archivos CSV
    └── zip/              # Archivos ZIP con múltiples formatos
```

## Uso

1. Archivos YAML:
   - Coloca los YAMLs de catálogo en `yaml/catalog/`
   - Coloca los YAMLs de paquete en `yaml/package/`
   - Coloca los YAMLs de emisor en `yaml/sender/`

2. Archivos de Datos:
   - Coloca archivos Excel en `files/excel/`
   - Coloca archivos CSV en `files/csv/`
   - Coloca archivos ZIP en `files/zip/`

3. Ejemplos:
   - Revisa `yaml/examples/` para ver ejemplos de cada tipo de YAML
   - Los ejemplos incluyen comentarios explicativos

## Convenciones de Nombres

1. YAMLs:
   - Catálogos: `nombre_catalogo.yaml`
   - Paquetes: `nombre_paquete.yaml`
   - Emisores: `nombre_emisor.yaml`

2. Archivos de Datos:
   - Excel/CSV: `{sender_id}-{date}-{type}.xlsx`
   - ZIP: `{sender_id}-{date}-PAQUETE_MIXTO.zip`

Donde:
- {sender_id}: Identificador del emisor (ej: ALC001)
- {date}: Fecha en formato YYYYMMDD (ej: 20250306)
- {type}: Tipo de datos (ej: PRODUCTOS, VENTAS)

## Validación

Para validar archivos usando SAGE:

1. CLI:
   ```bash
   sage validate --yaml yaml/catalog/mi_catalogo.yaml --file files/excel/datos.xlsx
   ```

2. API:
   ```bash
   curl -X POST http://localhost:5000/api/validate-yaml \
        -F "yaml=@yaml/catalog/mi_catalogo.yaml" \
        -F "file=@files/excel/datos.xlsx"
   ```

## Errores Comunes

1. Error de formato de archivo:
   - Mensaje: "Invalid filename format"
   - Solución: Verifica que el nombre del archivo siga el patrón {sender_id}-{date}-{type}

2. Error de validación de catálogo:
   - Mensaje: "Field validation failed"
   - Solución: Revisa que los datos cumplan con las reglas definidas en el YAML

3. Error de procesamiento de paquete:
   - Mensaje: "No matching file found for catalog"
   - Solución: Asegúrate que el ZIP contenga los archivos esperados según la configuración