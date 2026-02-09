# Plan de Pruebas (Test Plan) - Veloce MVP v1.0

Este documento detalla los casos de prueba esenciales para validar la estabilidad y funcionalidad del Sistema de Facturación "Veloce" antes de su paso a producción.

---

## 1. Módulo de Autenticación y Usuarios

- [✅] **Inicio de Sesión (Login):**
  - [✅] Entrar con credenciales válidas.
  - [✅] Intentar entrar con contraseña incorrecta (verificar mensaje de error).
  - [✅] Intentar entrar con correo no registrado.
- [✅] **Protección de Rutas:**
  - [✅] Intentar acceder a `/facturas` o `/reportes` sin estar logueado (debe redirigir al login).
- [✅] **Cierre de Sesión:**
  - [✅] Verificar que al hacer logout ya no se pueda volver atrás con el navegador a páginas protegidas.

## 2. Módulo de Clientes

- [✅] **Creación:**
  - [✅] Registrar un cliente con todos los datos.
  - [✅] Intentar registrar un cliente con un correo ya existente (debe fallar).
  - [✅] Verificar que los campos obligatorios (Nombre, Teléfono) validen si están vacíos.
- [✅] **Listado y Búsqueda:**
  - [✅] Buscar cliente por **Nombre** (parcial y completo).
  - [✅] Buscar cliente por **Apellido**.
  - [✅] Probar el filtro de fechas (Desde/Hasta) con un cliente creado hoy y otro ayer.
- [✅] **Edición:**
  - [✅] Modificar el nombre o correo de un cliente existente y guardar.
- [✅] **Eliminación:**
  - [✅] (Admin) Eliminar un cliente y verificar que desaparece de la lista.

## 3. Módulo de Facturación (Core)

- [✅] **Creación de Factura:**
  - [✅] Seleccionar un cliente desde el buscador (autocompletado).
  - [✅] Agregar un ítem manual (descripción, cantidad, precio).
  - [✅] Seleccionar un producto existente del inventario.
  - [✅] Agregar múltiples líneas de ítems.
  - [✅] Eliminar una línea de ítem antes de guardar.
  - [✅] **Cálculos:** Verificar manualmente que `(Cantidad * Precio) + Impuesto` sea igual al Total mostrado.
  - [✅] **Forma de Pago:** Guardar una factura como "Efectivo" y otra como "Transferencia".
- [✅] **Gestión de Estados:**
  - [✅] Crear factura en estado "Pendiente".
  - [✅] Ir al detalle y marcarla como "Pagada". Verificar que el estado cambie visualmente.
- [✅] **Edición:**
  - [✅] Editar una factura guardada, cambiar cantidades y verificar que el total se recalcule.
- [✅] **Visualización y PDF:**
  - [✅] Abrir el detalle de una factura.
  - [✅] Generar el PDF y verificar:
    - [✅] Logo y datos de la empresa correctos.
    - [✅] Datos del cliente correctos.
    - [✅] Desglose de ítems y totales.
    - [✅] Que aparezca la "Forma de Pago" (ej. Efectivo/Transferencia).
- [✅] **Filtros de Facturas:**
  - [✅] Filtrar por rango de fechas.
  - [✅] Buscar facturas por nombre de cliente.

## 4. Módulo de Inventario / Productos

- [ ] **CRUD Básico:**
  - [✅] Crear un producto nuevo.
  - [✅] Editar precio de un producto.
  - [✅] Verificar que el nuevo precio salga al crear una factura nueva.

## 5. Módulo de Gastos

- [✅ ] **Registro:**
  - [ ✅] Registrar un gasto nuevo (ej. "Pago de Luz").
  - [ ✅] Verificar que aparezca en el listado de gastos.

## 6. Módulo de Reportes (Validación de Datos)

- [✅ ] **Cuadre Diario (Cash Flow):**
  - [ ✅] Crear una factura de $1000 en **Efectivo** (Pagada) con fecha de hoy.
  - [ ✅] Crear una factura de $2000 en **Transferencia** (Pagada) con fecha de hoy.
  - [ ✅] Crear un gasto de $500 con fecha de hoy.
  - [ ✅] **Verificación:** El reporte de hoy debe mostrar:
    - [ ✅] Total Ingresos: $3000
    - [ ✅] Ingreso Efectivo: $1000
    - [ ✅] Ingreso Otros: $2000
    - [ ✅] Total Gastos: $500
    - [ ✅] Balance: $2500
- [✅ ] **Cuentas por Cobrar:**
  - [✅ ] Verificar que aparezcan solo las facturas con estado "Pendiente" o "Vencido".
  - [✅ ] Pagar una factura pendiente y verificar que desaparece de este reporte.
- [✅ ] **Reporte Fiscal:**
  - [✅ ] Verificar que el cálculo del 18% del ITBIS sea matemáticamente correcto sobre la base imponible.

## 7. Pruebas de Estrés / Seguridad Básica (Opcional MVP)

- [ ✅] **Datos cruzados:**
  - [ ✅] Si tienes acceso a crear otra organización/usuario, verificar que el Usuario A no vea las facturas del Usuario B.
- [ ✅] **Datos "Viejos":**
  - [ ✅] Revisar que las facturas antiguas (que no tenían campo `forma_pago`) se abran correctamente y muestren "Efectivo" por defecto sin dar error.
