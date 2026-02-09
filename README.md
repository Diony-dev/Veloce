# Veloce - Sistema de Facturación 🚀

Sistema web integral para la gestión administrativa y facturación de pequeñas y medianas empresas. Desarrollado con **Flask** (Python) y **MongoDB**.

🔗 **Repositorio:** [https://github.com/Diony-dev/Veloce.git](https://github.com/Diony-dev/Veloce.git)

---

## ✨ Características Principales

- **🧾 Facturación Completa:**
  - Creación, edición y anulación de facturas.
  - Control de estados: _Pendiente_, _Pagado_, _Vencido_.
  - Generación automática de PDFs.
  - Envío de facturas por correo electrónico.

- **💳 Gestión de Pagos:**
  - Registro de múltiples formas de pago: Efectivo, Tarjeta, Transferencia, Cheque.
  - Historial de transacciones.

- **👥 Gestión de Clientes:**
  - Base de datos de clientes con historial de facturación.
  - Cuentas por cobrar y seguimiento de saldos.

- **📦 Inventario y Servicios:**
  - Catálogo de productos y servicios.
  - Control de stock (alerta de existencias).

- **📉 Gastos y Finanzas:**
  - Registro y categorización de gastos operativos.
  - **Cuadre Diario:** Reporte de flujo de caja (Ingresos vs Gastos).
  - **Estimación Fiscal:** Cálculo aproximado de impuestos (ITBIS).

- **🔐 Seguridad y Organización:**
  - Autenticación segura de usuarios.
  - **Sistema Multi-organizacion:** Cada empresa tiene sus propios datos aislados.
  - Roles de usuario y permisos.

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python 3, Flask.
- **Base de Datos:** MongoDB (Atlas o Local).
- **Frontend:** HTML5, CSS3, Bootstrap 5.
- **Interactividad:** JavaScript, HTMX (para actualizaciones dinámicas sin recarga).
- **Servicios Externos:**
  - **Cloudinary:** Almacenamiento de imágenes (logos, perfiles).
  - **Brevo (Sendinblue):** Envío de correos transaccionales (invitaciones, notificaciones).
  - **html2pdf.js:** Generación de documentos PDF en el cliente.

---

## ⚙️ Instalación y Configuración Local

Sigue estos pasos para levantar el proyecto en tu máquina local:

### 1. Clonar el repositorio

```bash
git clone https://github.com/Diony-dev/Veloce.git
cd Veloce
```

### 2. Crear y activar un entorno virtual

Es recomendable usar un entorno virtual para aislar las dependencias:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto. Puedes usar el siguiente template como referencia:

```ini
# --- Configuración General ---
SECRET_KEY=tu_clave_secreta_super_segura
TIMEZONE=America/Santo_Domingo

# --- Base de Datos (MongoDB) ---
# Ejemplo: mongodb+srv://usuario:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_URI=tu_mongo_uri
MONGO_DBNAME=sistema_facturacion

# --- Almacenamiento de Imágenes (Cloudinary) ---
# Necesario para subir logos de empresas y fotos de perfil
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret

# --- Email (Brevo / Sendinblue) ---
# Necesario para enviar invitaciones y notificaciones
BREVO_API_KEY=tu_api_key_de_brevo

# --- Otros (Opcional) ---
RESEND_API_KEY= (si se utiliza en el futuro)
```

**Nota:** Asegúrate de tener permisos de red si te conectas a un MongoDB en la nube (MongoDB Atlas).

---

## ▶️ Ejecución

Para iniciar el servidor de desarrollo:

```bash
python run.py
```

- El sistema estará disponible en: `http://localhost:5000`
- Si es la primera vez, deberás registrar una **Organización** y un **Usuario Administrador**.

---

## 📂 Estructura del Proyecto

```text
Veloce/
├── app/
│   ├── routes/      # Controladores (Endpoints de Flask)
│   ├── services/    # Lógica de negocio y acceso a datos
│   ├── models/      # Estructuras de datos (Schemas implícitos)
│   ├── templates/   # Vistas HTML (Jinja2)
│   ├── static/      # Archivos estáticos (CSS, JS, Imágenes)
│   └── ...
├── config.py        # Configuración de entornos (Dev/Prod)
├── run.py           # Punto de entrada de la aplicación
├── requirements.txt # Dependencias del proyecto
└── README.md        # Documentación
```

---

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Si deseas mejorar Veloce:

1. Haz un **Fork** del repositorio.
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz **Commit** (`git commit -m 'Agrega nueva funcionalidad'`).
4. Haz **Push** a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un **Pull Request**.

---

## 📄 Licencia

Este proyecto está bajo la Licencia [MIT](LICENSE) (o especificar si es privado/propietario).

---

Desarrollado por [Diony-dev](https://github.com/Diony-dev)
