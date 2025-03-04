# 📘 Manual de Gestión del Sistema de Catálogos SAGE - Sección Definición con YAML

## 📌 Introducción

Este documento describe la estructura del YAML de **catálogos** utilizado en el sistema SAGE para definir la validación y configuración de los datos enviados por los distribuidores. Se especifica su propósito, la estructura del archivo y los valores aceptados en cada campo.

---

## 1️⃣ YAML de Catálogo (`catalog.yaml`)

📌 **Propósito:**  
Define la **estructura de los datos**, validaciones de **fila y catálogo**, y reglas de formato del archivo.

### 📍 Estructura del YAML
```yaml
catalog:
  name: "Ventas"
  description: "Registro de transacciones de ventas."
  fields:
    - name: "transaction_id"
      type: "text"
      length: 36
      required: true
      unique: true
      validation_expression: "df['transaction_id'].notnull()"
    - name: "customer_id"
      type: "text"
      length: 20
      required: true
      validation_expression: "df['customer_id'].notnull()"
    - name: "total_amount"
      type: "number"
      length: 10
      decimals: 2
      required: true
      validation_expression: "df['total_amount'] > 0"
    - name: "purchase_date"
      type: "date"
      required: true
      validation_expression: "df['purchase_date'] <= pd.Timestamp.today()"
    - name: "payment_method"
      type: "enum"
      allowed_values: ["Credit Card", "Cash", "Bank Transfer"]
      required: true
  row_validation:
    validation_expression: "df['total_amount'] > 0 & df['customer_id'].notnull()"
    description: "Cada fila debe tener un monto mayor a 0 y un cliente válido."
  catalog_validation:
    validation_expression: "df.shape[0] >= 100 & df.duplicated(subset=['transaction_id']).sum() == 0"
    description: "El catálogo debe tener al menos 100 registros y los ID de transacción deben ser únicos."
  file_format:
    filename_pattern: "{sender_id}-{date}-SALES_DATA.csv"
```

### 📍 Descripción de Campos
- **`name`** → Nombre del catálogo.
- **`description`** → Descripción del propósito del catálogo.
- **`fields`** → Lista de campos del catálogo con sus atributos:
  - **`name`** → Nombre del campo.
  - **`type`** → Tipo de dato (`text`, `number`, `date`, `enum`).
  - **`length`** → Longitud máxima permitida para campos de texto y números.
  - **`decimals`** → Número de decimales permitidos en valores numéricos.
  - **`required`** → Si el campo es obligatorio (`true`/`false`).
  - **`unique`** → Si el campo debe tener valores únicos (`true`/`false`).
  - **`validation_expression`** → Expresión en **Python** para validar el campo.
  - **`allowed_values`** → Lista de valores permitidos (solo para `enum`).
- **`row_validation`** → Validación a nivel de fila para garantizar consistencia en los datos.
- **`catalog_validation`** → Reglas de validación a nivel de todo el catálogo.
- **`file_format`** → Define el patrón de nombre de archivo esperado.

### 📍 Ejemplo de YAML de Catálogo
```yaml
catalog:
  name: "Inventario"
  description: "Registro de inventario de productos."
  fields:
    - name: "product_id"
      type: "text"
      length: 15
      required: true
      unique: true
      validation_expression: "df['product_id'].notnull()"
    - name: "product_name"
      type: "text"
      length: 100
      required: true
    - name: "stock_quantity"
      type: "number"
      length: 10
      decimals: 0
      required: true
      validation_expression: "df['stock_quantity'] >= 0"
    - name: "category"
      type: "enum"
      allowed_values: ["Electronics", "Clothing", "Furniture"]
      required: true
  row_validation:
    validation_expression: "df['stock_quantity'] >= 0"
    description: "Cada producto debe tener una cantidad de stock mayor o igual a 0."
  catalog_validation:
    validation_expression: "df['product_id'].nunique() == df.shape[0]"
    description: "No debe haber productos duplicados en el inventario."
  file_format:
    filename_pattern: "{sender_id}-{date}-INVENTORY_DATA.csv"
```

---

## 📢 Conclusión
✅ **El YAML de catálogos permite definir estructura, validaciones y formato de archivos.**  
✅ **Las validaciones garantizan calidad y consistencia en los datos enviados.**  
✅ **La estructura permite flexibilidad para diferentes tipos de catálogos.**  

📌 **Este manual proporciona una referencia clara para los analistas sobre cómo definir correctamente un catálogo en YAML.** 🚀

