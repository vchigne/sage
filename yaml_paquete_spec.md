### **2️⃣ YAML de Paquete (`package.yaml`)**

📌 **Propósito:**  
El YAML de paquetes define **qué datos** se esperan en un paquete, su **estructura**, **validaciones**, **métodos de envío** y **destino en la base de datos**. Un paquete puede contener múltiples catálogos, agrupándolos bajo una misma configuración de validación y procesamiento.

---

### 📍 **Estructura del YAML**
```yaml
package:
  name: "Paquete de Ventas"
  description: "Contiene los datos de ventas de distribuidores."
  mandatory: true

  methods:
    file_format:
      type: "ZIP"  # Opciones: CSV, XLSX, JSON, XML, ZIP
      filename_pattern: "{sender_id}-{date}-SALES_PACKAGE.zip"

  catalogs:
    - path: "catalogs/vendedores.yaml"
    - path: "catalogs/clientes.yaml"
    - path: "catalogs/productos.yaml"
    - path: "catalogs/ventas.yaml"

  package_validation:
    validation_rules:
      - name: "Vendedor debe existir en vendedores"
        validation_expression: "df['ventas']['vendedor_id'].isin(df['vendedores']['vendedor_id'])"
      - name: "Cliente debe existir en clientes"
        validation_expression: "df['ventas']['customer_id'].isin(df['clientes']['customer_id'])"

  destination:
    enabled: true  # Si es false, no se insertará en la BD
    database_connection:
      type: "postgresql"  # Opciones: mysql, sqlserver, oracle, postgresql
      host: "db.globalcorp.com"
      port: 5432
      username: "db_user"
      password: "secure_password"
      database: "corporate_data"
    target_table: "sales_transactions"
    
    pre_validation:
      endpoint: "https://api.globalcorp.com/v1/validate_temp_data"
      method: "POST"
      payload:
        table: "temp_sales_transactions"
        checks: ["validate_customers", "validate_products", "check_duplicates"]
    
    insertion_method: "upsert"  # Opciones: insert, upsert, replace
```

---

### 📍 **Descripción de Campos**
- **`name`** → Nombre del paquete de datos.
- **`description`** → Breve descripción del contenido del paquete.
- **`mandatory`** → Indica si el paquete es obligatorio (`true`/`false`).
- **`methods`** → Define cómo se recibe el paquete.
  - **`file_format.type`** → Tipo de archivo esperado (`CSV`, `XLSX`, `JSON`, `XML`, `ZIP`).
  - **`filename_pattern`** → Formato esperado para los archivos del paquete.
- **`catalogs`** → Lista de catálogos incluidos en el paquete.
  - **`path`** → Ruta del YAML de cada catálogo.
- **`package_validation`** → Validaciones a nivel de paquete.
  - **`validation_rules`** → Lista de reglas para validar la integridad de los datos entre catálogos.
  - **`validation_expression`** → Expresión en **Python/Pandas** para realizar validaciones cruzadas.
- **`destination`** → Configuración para almacenar los datos en la base de datos.
  - **`enabled`** → Si los datos deben insertarse (`true`/`false`).
  - **`database_connection`** → Configuración de conexión a la base de datos.
  - **`target_table`** → Tabla donde se almacenarán los datos.
  - **`pre_validation`** → API que ejecuta validaciones previas a la inserción.
  - **`insertion_method`** → Método de inserción (`insert`, `upsert`, `replace`).

---

### 📍 **Ejemplo de YAML de Paquete**
```yaml
package:
  name: "Paquete de Inventario"
  description: "Datos de inventario enviados por distribuidores."
  mandatory: true

  methods:
    file_format:
      type: "CSV"
      filename_pattern: "{sender_id}-{date}-INVENTORY_PACKAGE.csv"

  catalogs:
    - path: "catalogs/inventario.yaml"

  package_validation:
    validation_rules:
      - name: "Producto debe existir en la base de productos"
        validation_expression: "df['inventario']['producto_id'].isin(df['productos']['producto_id'])"
      - name: "Stock no puede ser negativo"
        validation_expression: "df['inventario']['stock'] >= 0"

  destination:
    enabled: true
    database_connection:
      type: "mysql"
      host: "db.empresa.com"
      port: 3306
      username: "inventory_user"
      password: "secure_password"
      database: "inventory_data"
    target_table: "inventory_records"
    
    pre_validation:
      endpoint: "https://api.empresa.com/v1/validate_inventory"
      method: "POST"
      payload:
        table: "temp_inventory"
        checks: ["validate_stock", "check_duplicates"]
    
    insertion_method: "insert"
```

---

### 📢 **Conclusión**
✅ **El YAML de paquetes permite definir la validación y procesamiento de múltiples catálogos bajo una misma configuración.**  
✅ **Las validaciones garantizan que los datos enviados cumplan con integridad referencial antes de ser procesados.**  
✅ **El sistema es flexible y escalable, permitiendo diferentes métodos de envío y configuraciones de base de datos.**  

📌 **Este manual proporciona una referencia clara para los analistas sobre cómo definir correctamente un paquete en YAML.** 🚀