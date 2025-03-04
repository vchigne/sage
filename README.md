# 📘 **SAGE - Structured Automated Governance of Entities**

## 📌 **Descripción del Proyecto**
SAGE es un sistema diseñado para la **validación, estructuración y procesamiento de datos** enviados por múltiples remitentes. Permite **definir, validar y almacenar información** utilizando archivos YAML, asegurando que los datos cumplan con los estándares y reglas de negocio antes de su procesamiento.

El sistema proporciona una infraestructura flexible basada en YAML para definir **catálogos de datos, paquetes de procesamiento y remitentes autorizados**, permitiendo una integración eficiente y controlada con bases de datos empresariales.

---

## 🚀 **Características Principales**
✅ **Definición de datos mediante YAML** (`catalog.yaml`, `package.yaml`, `senders.yaml`).  
✅ **Validación estructurada** de archivos antes de su procesamiento.  
✅ **Procesamiento de datos y almacenamiento automático en bases de datos.**  
✅ **Compatibilidad con múltiples métodos de envío**: SFTP, Email y API.  
✅ **Notificación y reporte de errores** en envíos fallidos.  
✅ **Soporte para formatos de archivo**: CSV, XLSX, JSON, XML y ZIP.  
✅ **Configuración flexible y escalable** para múltiples remitentes y paquetes de datos.  

---

## 🏗 **Estructura del Proyecto**
📂 **`catalogs/`** → Definiciones de estructuras de datos en YAML.  
📂 **`packages/`** → Configuración de paquetes de datos.  
📂 **`senders.yaml`** → Lista de remitentes y métodos de envío.  
📂 **`data/`** → Archivos de datos enviados.  
📂 **`logs/`** → Registros de errores y validaciones.  
📜 **`prd.md`** → Documentación de requerimientos del producto.  
📜 **`readme.md`** → Este documento de introducción.  
📜 **`procesar_sage.py`** → Script principal para validar y procesar datos.  
📜 **`validar_yaml.py`** → Validador de estructura y reglas en YAML.  

---

## 🛠 **Instalación y Configuración**
### **1️⃣ Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/sage.git
cd sage
```

### **2️⃣ Instalar dependencias**
```bash
pip install -r requirements.txt
```

### **3️⃣ Configurar YAMLs**
- Definir los catálogos en `catalogs/`
- Configurar paquetes en `packages/`
- Configurar remitentes en `senders.yaml`

### **4️⃣ Ejecutar la validación de YAMLs**
```bash
python validar_yaml.py
```

### **5️⃣ Procesar los datos**
```bash
python procesar_sage.py
```

---

## 📊 **Flujo de Trabajo**
1️⃣ **Un remitente envía datos** en el formato predefinido.  
2️⃣ **SAGE valida la estructura y el contenido** de los datos mediante reglas YAML.  
3️⃣ **Se ejecutan validaciones cruzadas** entre catálogos dentro del paquete.  
4️⃣ **Los datos son insertados en la base de datos** si cumplen con las reglas.  
5️⃣ **Si hay errores, se notifica al remitente** con detalles del problema.  

---

## 🌎 **Casos de Uso**
🔹 **Recepción y validación de datos de ventas de distribuidores.**  
🔹 **Actualización y validación de inventarios en tiempo real.**  
🔹 **Control y seguimiento de envíos de información de múltiples fuentes.**  
🔹 **Procesamiento y almacenamiento de información proveniente de APIs externas.**  

---

## 📌 **Requisitos Técnicos**
✅ **Lenguaje:** Python 3.8+
✅ **Librerías Clave:** Pandas, SQLAlchemy, YAML, Requests
✅ **Base de Datos:** PostgreSQL, MySQL, SQL Server
✅ **Integraciones:** APIs REST, SFTP, Correos Electrónicos

---

## 📢 **Contribuciones**
👥 ¡Toda contribución es bienvenida! Puedes colaborar de las siguientes maneras:
- Reportando problemas (issues).
- Proponiendo mejoras en la documentación.
- Desarrollando nuevas funcionalidades.
- Optimizando el código y corrigiendo errores.

Para contribuir, **haz un fork del repositorio**, crea una rama con tus cambios y envía un Pull Request.  

---

## 📜 **Licencia**
Este proyecto está bajo la licencia **MIT**. Puedes usarlo, modificarlo y distribuirlo libremente.

📌 **Hecho con ❤️ para garantizar la calidad y seguridad en el procesamiento de datos.** 🚀

