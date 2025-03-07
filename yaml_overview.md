# **📘 Manual de Especificación: YAMLs para Gestión de Datos de Distribuidores**

## **📌 Introducción**
Este documento describe la estructura y uso de los tres tipos de YAMLs utilizados para la gestión y validación de datos enviados por distribuidores a **Global Corp**. Se especifica la función de cada YAML, sus relaciones y los valores aceptados en cada campo.

---

## **1️⃣ Tipos de YAML y su Relación**

| YAML | Descripción | Relación con otros YAMLs |
|------|------------|-------------------------|
| **YAML de Remitentes (`senders.yaml`)** | Define los distribuidores que envían datos, el método de envío y los paquetes asignados. | Referencia los YAML de paquetes (`package.yaml`) que cada remitente debe enviar. |
| **YAML de Paquete (`package.yaml`)** | Define los datos esperados en un paquete, su estructura, validaciones y destino en la base de datos. | Contiene referencias a YAMLs de catálogos (`catalog.yaml`). |
| **YAML de Catálogo (`catalog.yaml`)** | Define la estructura de los datos dentro de un paquete (campos, validaciones de filas y catálogos). | Se usa dentro de un paquete y no tiene referencia a remitentes. |

---

## **2️⃣ YAML de Remitentes (`senders.yaml`)**
📌 **Propósito:**  
Define **quién** envía datos, **cómo** lo hace y **qué paquetes** debe entregar.

### **Estructura del YAML**
```yaml
senders:
  corporate_owner: <string>
  data_receivers: 
    - name: <string>
      email: <string>
      sftp_directory: <string>
      api_endpoint: <string>
  senders_list:
    - distributor_id: <string>
      name: <string>
      responsible_person:
        name: <string>
        email: <string>
        phone: <string>
      allowed_methods: <array>
      configurations:
        sftp:
          host: <string>
          port: <integer>
          username: <string>
          password: <string>
          directory: <string>
        email:
          allowed_senders: <array>
          receiving_email: <string>
          subject_format: <string>
        api:
          endpoint: <string>
          api_key: <string>
          method: <string>
      packages:
        - name: <string>
          path: <string>
```

### **📍 Descripción de Campos**
- **`corporate_owner`** → Nombre de la empresa que recibe los datos.  
- **`data_receivers`** → Lista de destinatarios de los datos.  
  - `name` → Nombre del centro de datos.  
  - `email` → Correo donde se recibirán notificaciones.  
  - `sftp_directory` → Directorio en SFTP donde se almacenan los paquetes recibidos.  
  - `api_endpoint` → URL del endpoint para recepción por API.  
- **`senders_list`** → Lista de distribuidores autorizados para enviar datos.  
  - `distributor_id` → Identificador único del distribuidor.  
  - `name` → Nombre del distribuidor.  
  - `responsible_person` → Datos de contacto del responsable.  
  - `allowed_methods` → Métodos de envío permitidos (`sftp`, `email`, `api`, `crud`).  
  - `configurations` → Detalles de conexión por método.  
  - `packages` → Lista de paquetes que este distribuidor debe enviar.  

### **📌 Valores Posibles**
- **`allowed_methods`** → Valores aceptados: `["sftp", "email", "api", "crud"]`.  
- **`method` en API** → Valores aceptados: `"POST"`, `"PUT"`.  

---

## **3️⃣ YAML de Paquete (`package.yaml`)**
📌 **Propósito:**  
Define **qué datos** se esperan en el paquete, su **estructura**, **validaciones** y **destino** en la base de datos.

### **Estructura del YAML**
```yaml
package:
  name: <string>
  description: <string>
  submission_frequency:
    type: <string>
    deadline:
      if_monthly: 
        day: <integer>
        time: <string>
  mandatory: <boolean>
  methods:
    file_format:
      type: <string>
      filename_pattern: <string>
  catalogs:
    - path: <string>
  package_validation:
    validation_rules:
      - name: <string>
        validation_expression: <string>
  destination:
    enabled: <boolean>
    database_connection:
      type: <string>
      host: <string>
      port: <integer>
      username: <string>
      password: <string>
      database: <string>
    target_table: <string>
    pre_validation:
      endpoint: <string>
      method: <string>
      payload: <object>
    insertion_method: <string>
```

### **📍 Descripción de Campos**
- **`submission_frequency`** → Define la periodicidad del envío (`daily`, `weekly`, `monthly`).  
- **`methods.file_format.type`** → Tipo de archivo (`CSV`, `XLSX`, `JSON`).  
- **`catalogs`** → Lista de YAMLs de catálogos incluidos en el paquete.  
- **`package_validation`** → Validaciones que afectan a todo el paquete.  
- **`destination`** → Configuración para guardar los datos en la base de datos.  
  - `enabled` → Si los datos deben insertarse (`true`/`false`).  
  - `database_connection` → Configuración de conexión a la base de datos.  
  - `pre_validation` → API para validaciones antes de insertar en la BD.  
  - `insertion_method` → Método de inserción (`insert`, `upsert`, `replace`).  

### **📌 Valores Posibles**
- **`submission_frequency.type`** → `"daily"`, `"weekly"`, `"monthly"`.  
- **`methods.file_format.type`** → `"CSV"`, `"XLSX"`, `"JSON"`.  
- **`insertion_method`** → `"insert"`, `"upsert"`, `"replace"`.  

---

## **4️⃣ YAML de Catálogo (`catalog.yaml`)**
📌 **Propósito:**  
Define la **estructura de los datos**, validaciones de **fila y catálogo**.

### **Estructura del YAML**
```yaml
catalog:
  name: <string>
  description: <string>
  fields:
    - name: <string>
      type: <string>
      length: <integer>
      required: <boolean>
      unique: <boolean>
      validation_expression: <string>
  row_validation:
    validation_expression: <string>
    description: <string>
  catalog_validation:
    validation_expression: <string>
    description: <string>
  file_format:
    filename_pattern: <string>
```

### **📍 Descripción de Campos**
- **`fields`** → Lista de campos y reglas de validación.  
  - `type` → Tipo de dato (`text`, `number`, `boolean`, `date`).  
  - `length` → Longitud máxima del campo.  
  - `unique` → Si el campo debe ser único.  
  - `validation_expression` → Expresión Python para validar el campo.  
- **`row_validation`** → Validaciones a nivel de fila.  
- **`catalog_validation`** → Validaciones globales sobre el catálogo.  

### **📌 Valores Posibles**
- **`type`** → `"text"`, `"number"`, `"boolean"`, `"date"`.  

---

## **📢 Conclusión**
✅ **Cada YAML tiene un rol claro:** remitentes, paquetes y catálogos.  
✅ **Las validaciones garantizan calidad y consistencia de datos.**  
✅ **La estructura permite flexibilidad y escalabilidad.**  

📌 **¿Este manual cubre todas las dudas de los analistas?** 🚀