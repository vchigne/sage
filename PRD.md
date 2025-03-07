# 📌 **Product Requirements Document (PRD) - SAGE**

## **1. Introducción**
### **1.1 Propósito del Documento**
Este documento define los requisitos del producto para el sistema **SAGE (Structured Automated Governance of Entities)**, diseñado para la gestión, validación y procesamiento de datos enviados por múltiples remitentes a una organización centralizada.

### **1.2 Alcance**
SAGE permite:
- La validación estructurada de archivos de datos.
- La integración con bases de datos empresariales.
- La gestión de remitentes y métodos de envío.
- La automatización del procesamiento de datos con reglas predefinidas.

### **1.3 Audiencia del Documento**
Este documento está dirigido a:
- Desarrolladores
- Arquitectos de Software
- Administradores de Base de Datos
- Analistas de Datos

---

## **2. Descripción General del Sistema**
### **2.1 Visión General**
SAGE procesa datos estructurados enviados por múltiples fuentes y valida su integridad antes de ser almacenados. Utiliza **archivos YAML** para definir reglas de validación, estructura de datos y políticas de integración.

### **2.2 Componentes Clave**
1. **Catálogos (`catalog.yaml`)**: Definen la estructura y reglas de validación de datos individuales.
2. **Paquetes (`package.yaml`)**: Agrupan varios catálogos y gestionan validaciones cruzadas.
3. **Remitentes (`senders.yaml`)**: Definen quién envía datos, con qué frecuencia y por qué método.
4. **Procesador de Datos**: Extrae, transforma y almacena la información recibida.
5. **Validación Automática**: Verifica la calidad de los datos según los YAMLs definidos.

---

## **3. Requerimientos Funcionales**

### **3.1 Procesamiento de Datos**
✅ Cargar y leer archivos **YAML** de catálogos, paquetes y remitentes.
✅ Validar datos de acuerdo con las reglas de negocio definidas en YAML.
✅ Ejecutar validaciones cruzadas entre catálogos dentro de un paquete.
✅ Insertar datos en la base de datos siguiendo estrategias definidas (`insert`, `upsert`, `replace`).

### **3.2 Validaciones y Reglas de Negocio**
✅ Validaciones a nivel de **campo** (longitud, tipo de dato, valores permitidos).
✅ Validaciones a nivel de **fila** (expresiones Python en Pandas).
✅ Validaciones a nivel de **catálogo** (duplicados, integridad referencial).
✅ Validaciones a nivel de **paquete** (relaciones entre catálogos).

### **3.3 Métodos de Envío de Datos**
✅ Soporte para **SFTP, Email y API** como métodos de envío.
✅ Validación de credenciales y permisos de remitentes.
✅ Soporte para múltiples formatos de archivo: **CSV, XLSX, JSON, XML, ZIP**.

### **3.4 Notificaciones y Errores**
✅ Generación de logs de errores detallados.
✅ Notificación a remitentes en caso de fallos.
✅ Panel de control para monitoreo del estado de los envíos.

---

## **4. Requerimientos No Funcionales**
✅ **Escalabilidad**: Soporta múltiples fuentes de datos concurrentes.
✅ **Seguridad**: Implementación de autenticación para API y SFTP.
✅ **Flexibilidad**: Uso de YAML para definir reglas sin modificar código.
✅ **Mantenimiento**: Arquitectura modular para facilitar mejoras futuras.

---

## **5. Arquitectura del Sistema**
- **Interfaz de Entrada:** Archivos YAML y datos enviados por SFTP, Email o API.
- **Capa de Validación:** Validaciones de estructura, calidad e integridad referencial.
- **Capa de Procesamiento:** Transformación de datos según reglas definidas.
- **Base de Datos:** Almacenamiento de datos validados en tablas configurables.
- **Capa de Reportes:** Generación de logs y reportes de errores.

### **Diagrama de Flujo de Datos**
1. Un remitente envía datos en el formato definido.
2. SAGE verifica la estructura del archivo basado en `catalog.yaml`.
3. Se ejecutan validaciones cruzadas definidas en `package.yaml`.
4. Si los datos cumplen las reglas, se almacenan en la base de datos.
5. Si hay errores, se generan notificaciones al remitente.

---

## **6. Casos de Uso**
🔹 **Envío de datos de ventas**
- Un distribuidor carga un **paquete de ventas** con transacciones.
- SAGE valida si los clientes y productos existen en la base de datos.
- Si todo está correcto, los datos son almacenados.

🔹 **Validación de inventario en tiempo real**
- Los distribuidores envían información sobre **stock disponible**.
- Se verifica que los productos existan y el stock no sea negativo.
- Una vez validado, se actualiza la base de datos.

🔹 **Integración con APIs externas**
- Un remitente envía datos a través de **API**.
- SAGE valida la estructura y almacena los datos.

🔹 **Monitoreo y Reporte de Envíos**
- Un tablero muestra el estado de los envíos.
- Se emiten alertas si un remitente **no envió** su información.

---

## **7. Requerimientos Técnicos**
✅ **Lenguaje:** Python
✅ **Librerías Clave:** Pandas, SQLAlchemy, YAML, Requests
✅ **Base de Datos:** PostgreSQL, MySQL, SQL Server
✅ **Integraciones:** APIs REST, SFTP, Correos Electrónicos
✅ **Formato de Configuración:** YAML

---

## **8. Métricas de Éxito**
📌 **Tasa de éxito en validaciones**: Porcentaje de datos correctamente validados.
📌 **Tiempo de procesamiento**: Tiempo desde la recepción hasta la inserción en la base de datos.
📌 **Número de errores detectados**: Indicador de calidad del proceso.
📌 **Disponibilidad del sistema**: Porcentaje de uptime de los servicios.

---

## **9. Plan de Implementación**
### **9.1 Fases del Proyecto**
1️⃣ **Definición de YAMLs y validaciones** (1 mes)  
2️⃣ **Desarrollo del motor de validación** (2 meses)  
3️⃣ **Implementación de la base de datos** (1 mes)  
4️⃣ **Integración con métodos de envío (SFTP, Email, API)** (1 mes)  
5️⃣ **Pruebas y optimización** (1 mes)  
6️⃣ **Lanzamiento y monitoreo** (1 mes)  

### **9.2 Riesgos y Mitigaciones**
⚠️ **Riesgo:** Errores en validaciones YAML ➝ ✅ **Solución:** Pruebas unitarias en YAML.  
⚠️ **Riesgo:** Falta de compatibilidad con archivos ➝ ✅ **Solución:** Implementación de múltiples formatos.  
⚠️ **Riesgo:** Sobrecarga en el procesamiento ➝ ✅ **Solución:** Optimización de validaciones y procesos asíncronos.  

---

## **10. Conclusión**
SAGE proporciona una solución integral para la **gestión estructurada de datos**, asegurando calidad y eficiencia en la validación e integración de información. Este documento define la estructura, funcionalidad y plan de implementación del sistema.

📌 **Con SAGE, la validación y procesamiento de datos se vuelven más eficientes, confiables y escalables.** 🚀

