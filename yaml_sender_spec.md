### **3️⃣ YAML de Remitentes (`senders.yaml`)**

📌 **Propósito:**  
El YAML de remitentes define **quién envía los datos**, **cómo los envía** y **qué paquetes está autorizado a enviar**. Este archivo gestiona las configuraciones específicas de cada remitente, como métodos de envío, credenciales y responsables.

---

### 📍 **Estructura del YAML**
```yaml
senders:
  corporate_owner: "Global Corp"
  data_receivers:
    - name: "Central Data Hub"
      email: "datahub@globalcorp.com"
      sftp_directory: "/corporate/datahub/"
      api_endpoint: "https://api.globalcorp.com/v1/upload_package"

  senders_list:
    - sender_id: "DIST001"
      name: "Distribuidor Uno"
      responsible_person:
        name: "Alice Johnson"
        email: "alice.johnson@dist1.com"
        phone: "+1-555-111-2222"

      submission_frequency:
        type: "monthly"  # Opciones: daily, weekly, monthly
        deadline:
          if_monthly:
            day: 5
            time: "23:59"
          if_weekly:
            day_of_week: "Monday"
            time: "12:00"

      allowed_methods: ["sftp", "email", "api"]

      configurations:
        sftp:
          host: "sftp.dist1.com"
          port: 22
          username: "dist1_user"
          password: "secure_password"
          directory: "/outgoing/sales_package/"
        email:
          allowed_senders: ["sales@dist1.com"]
          receiving_email: "sales-packages@globalcorp.com"
          subject_format: "Sales Package Submission - {date}"
        api:
          endpoint: "https://api.dist1.com/upload"
          api_key: "API_SECRET_KEY"
          method: "POST"

      packages:
        - name: "Paquete de Ventas"
          path: "packages/sales_package.yaml"
```

---

### 📍 **Descripción de Campos**
- **`corporate_owner`** → Nombre de la empresa que recibe los datos.
- **`data_receivers`** → Lista de destinatarios que procesarán los datos.
  - **`name`** → Nombre del receptor.
  - **`email`** → Dirección de correo electrónico de contacto.
  - **`sftp_directory`** → Directorio SFTP donde se almacenarán los datos recibidos.
  - **`api_endpoint`** → Endpoint API para recibir datos vía integración.
- **`senders_list`** → Lista de remitentes autorizados.
  - **`sender_id`** → Identificador único del remitente.
  - **`name`** → Nombre del remitente.
  - **`responsible_person`** → Datos de contacto del responsable del envío.
  - **`submission_frequency`** → Frecuencia de envío de datos.
    - **`type`** → Frecuencia (`daily`, `weekly`, `monthly`).
    - **`deadline`** → Fecha límite según la frecuencia.
      - **`if_monthly`** → Día del mes y hora límite.
      - **`if_weekly`** → Día de la semana y hora límite.
  - **`allowed_methods`** → Métodos de envío permitidos (`sftp`, `email`, `api`).
  - **`configurations`** → Configuración específica de cada método de envío.
    - **`sftp`** → Configuración de acceso al servidor SFTP.
    - **`email`** → Configuración de envío y recepción de datos por email.
    - **`api`** → Configuración de API para envío de datos automatizado.
  - **`packages`** → Lista de paquetes que el remitente está autorizado a enviar.

---

### 📍 **Ejemplo de YAML de Remitentes**
```yaml
senders:
  corporate_owner: "Global Corp"
  data_receivers:
    - name: "Data Processing Center"
      email: "datacenter@globalcorp.com"
      sftp_directory: "/data/incoming/"
      api_endpoint: "https://api.globalcorp.com/upload"

  senders_list:
    - sender_id: "DIST002"
      name: "Distribuidor Dos"
      responsible_person:
        name: "John Doe"
        email: "john.doe@dist2.com"
        phone: "+1-555-222-3333"

      submission_frequency:
        type: "weekly"
        deadline:
          if_weekly:
            day_of_week: "Friday"
            time: "18:00"

      allowed_methods: ["sftp", "api"]

      configurations:
        sftp:
          host: "sftp.dist2.com"
          port: 22
          username: "dist2_user"
          password: "secure_password"
          directory: "/uploads/inventory_data/"
        api:
          endpoint: "https://api.dist2.com/upload"
          api_key: "ANOTHER_SECRET_KEY"
          method: "POST"

      packages:
        - name: "Paquete de Inventario"
          path: "packages/inventory_package.yaml"
```

---

### 📢 **Conclusión**
✅ **El YAML de remitentes permite gestionar múltiples fuentes de datos, especificando responsables, métodos de envío y paquetes asignados.**  
✅ **Las configuraciones permiten flexibilidad en la forma en que se envían los datos (SFTP, API, email).**  
✅ **Las reglas de frecuencia garantizan que los datos se reciban en los tiempos esperados.**  

📌 **Este manual proporciona una referencia clara para definir correctamente los remitentes en YAML.** 🚀