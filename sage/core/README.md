# SAGE Core Processor

Este módulo contiene el procesador central genérico de SAGE que maneja toda la lógica de validación basada en YAML.

## Estructura

- `processor.py`: Procesador base (SageProcessor) que implementa la lógica común de:
  - Carga y validación de YAML
  - Lectura y validación de datos
  - Procesamiento de reglas definidas en YAML

## Procesadores Especializados

Los siguientes procesadores heredan del SageProcessor y agregan funcionalidad específica:

1. YAMLProcessor:
   - Validación genérica de archivos YAML
   - Verificación de esquemas según tipo (catálogo, paquete, emisor)

2. PackageProcessor:
   - Manejo de paquetes ZIP
   - Extracción y validación de múltiples archivos
   - Aplicación de reglas por tipo de archivo

3. SenderProcessor:
   - Validación dedicada para emisores
   - Verificación de permisos y frecuencias
   - Control de plazos de envío

## Validaciones Automáticas

El procesador aplica automáticamente las siguientes validaciones básicas:

1. Campos Requeridos:
   - Verifica que los campos marcados como required=true no sean nulos
   - Ejemplo: 
     ```yaml
     fields:
       - name: "codigo_producto"
         type: "text"
         required: true  # Campo obligatorio
     ```

2. Validación de Duplicados:
   - Para campos marcados como unique=true
   - Ejemplo:
     ```yaml
     fields:
       - name: "codigo_producto"
         type: "text"
         unique: true  # No permite duplicados
     ```

3. Campos Numéricos:
   - Valida decimales según configuración
   - Ejemplo:
     ```yaml
     fields:
       - name: "precio"
         type: "number"
         decimals: 2  # Máximo 2 decimales
     ```

4. Campos de Fecha:
   - Convierte automáticamente usando pandas to_datetime
   - Valida formato de fecha
   - Ejemplo:
     ```yaml
     fields:
       - name: "fecha_creacion"
         type: "date"
     ```

## Combinando Validaciones Automáticas y Personalizadas

Las validaciones automáticas trabajan en conjunto con las reglas personalizadas:

```yaml
fields:
  - name: "codigo_producto"
    type: "text"
    required: true
    unique: true
    validation_expression: "df['codigo_producto'].str.match(r'PROD[0-9]{4}$')"
    message: "El código debe tener el formato PRODXXXX"
```

En este ejemplo:
1. La validación automática verifica que el campo no sea nulo y no tenga duplicados
2. La regla personalizada valida el formato específico del código

## Uso

Todo el procesamiento en SAGE se realiza a través de este core, que puede ser accedido desde:
- CLI
- API REST
- Interfaz de usuario

El flujo siempre es:
1. Cargar configuración YAML
2. Validar estructura
3. Procesar datos según reglas
4. Reportar resultados