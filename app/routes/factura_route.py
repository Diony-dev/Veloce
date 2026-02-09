
from math import ceil
from datetime import datetime
from flask import blueprints, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from app.database import mongo
from ..services.factura_services import eliminar_fact, create_factura, get_factura_by_id, update_factura_estado, list_facturas_by_organizacion, buscar_facturas, modificar_factura, list_facturas_filtradas
from ..models.factura import Factura
from ..services.cliente_services import get_cliente_by_id
from ..services.auth_services import get_organizacion_by_id

factura_bp = blueprints.Blueprint('factura', __name__)

def generar_numero_factura_timestamp():
    return datetime.now().strftime('%Y%m%d%H%M%S')

def procesar_items(descripcion, cantidad, precio_unitario):
    items = []
    for d, c, p in zip(descripcion, cantidad, precio_unitario):
        if d and c and p:
            items.append({
                'descripcion': d, 
                'cantidad': int(c), 
                'precio_unitario': float(p), 
                'total': int(c) * float(p)
            })
    return items

@factura_bp.route('/', methods=['GET'])
@login_required
def listar_facturas():
    page = request.args.get('page', 1, type=int)
    cliente = request.args.get('cliente')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')

    facturas, pagination = list_facturas_by_organizacion(
        current_user.organizacion_id,
        page=page,
        cliente=cliente,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    
    # Renderiza todo si NO es HTMX
    if not request.headers.get('HX-Request'):
        current_app.logger.info('listando las facturas')
        return render_template('factura/listar.html', facturas=facturas, pagination=pagination)

    # Renderiza solo el partial si es HTMX
    return render_template('factura/_factura_table.html', facturas=facturas, pagination=pagination)

@factura_bp.route('/crear', methods=['GET', 'POST'])
@login_required 
def crear_factura_route():
    
    if request.method == 'POST':
        invoice_num = generar_numero_factura_timestamp()
        cliente_id = request.form.get('cliente_id') 
        
        vendedor = current_user.nombre
        descripcion = request.form.getlist('descripcion[]')
        cantidad = request.form.getlist('cantidad[]')
        precio_unitario = request.form.getlist('precio_unitario[]')
        
        # --- MEJORA 1: Protección contra error de conversión numérica ---
        try:
            total = float(request.form.get('total'))
        except (ValueError, TypeError):
            total = 0.0

        fecha_str = request.form.get('fecha')
        estado = request.form.get('estado')
        forma_pago = request.form.get('forma_pago', 'efectivo')

        # Validaciones básicas...
        if not all([cliente_id, vendedor, descripcion, cantidad, precio_unitario, total, fecha_str, estado]):
            flash('Por favor, complete todos los campos obligatorios.', 'danger')
            return render_template('factura/crear.html')
        
        # ... validación de cliente ... (tu código actual está bien aquí)
        cliente_obj = get_cliente_by_id(cliente_id)
        if not cliente_obj or str(cliente_obj.organizacion_id) != str(current_user.organizacion_id):
            flash('Cliente inválido.', 'danger')
            return render_template('factura/crear.html')

        items = procesar_items(descripcion, cantidad, precio_unitario)
        
        # --- MEJORA 2: Conversión de Fecha para el Pipeline ---
        # Convertimos el string del HTML a objeto datetime real
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        except ValueError:
            # Si falla, usamos la fecha de hoy por seguridad
            fecha_obj = datetime.now()

        # --- VERIFICACIÓN DE STOCK (ADVERTENCIA) ---
        from app.services.producto_services import check_stock_availability
        warning_msg = []
        for d, c, p_unit, item_list in zip(descripcion, cantidad, precio_unitario, items):
             # items has processed dicts, but we need the raw product_id possibly from hidden inputs?
             # Wait, `items` list created by `procesar_items` DOES NOT HAVE `producto_id`!!!!
             # `procesar_items` only takes desc, qty, price. 
             # We need to capture the product IDs from the form!!!
             pass

        # We need to fetch product_ids from the form first.
        producto_ids = request.form.getlist('producto_id[]')
        
        # Re-build items with product_id if available
        # Modifying `procesar_items` would be cleaner but let's patch it here for now
        # Actually `items` is a list of dicts. We can zip it with producto_ids if they align.
        # Assuming frontend sends aligned lists (it should).
        
        for i, item in enumerate(items):
            if i < len(producto_ids):
                pid = producto_ids[i]
                if pid and len(pid) == 24: # Valid ObjectId
                    item['producto_id'] = pid
                    # Check Stock
                    try:
                        qty = float(item['cantidad'])
                        ok, msg = check_stock_availability(pid, qty)
                        if not ok:
                            flash(f"ADVERTENCIA: {msg}", 'warning')
                    except Exception:
                        pass
        
        try:
            factura_id = create_factura(
                current_user.organizacion_id, 
                invoice_num, 
                cliente_obj, 
                vendedor, 
                items, 
                total, 
                fecha_obj, 
                estado,
                forma_pago
            )
            
            if factura_id:
                flash('Factura creada exitosamente.', 'success')
                return redirect(url_for('factura.listar_facturas'))
            else:
                flash('Error al crear la factura (BD).', 'danger')
                
        except Exception as e:
            flash(f'Error inesperado: {e}', 'danger')
            return render_template('factura/crear.html')
    
    return render_template('factura/crear.html')

@factura_bp.route('/ver_factura/<factura_id>', methods=['GET'])
@login_required
def ver_factura(factura_id):
    factura = get_factura_by_id(factura_id)
    organizacion = get_organizacion_by_id(current_user.organizacion_id)
    if not factura:
        flash('Factura no encontrada.', 'danger')
        return redirect(url_for('factura.listar_facturas'))
    return render_template('factura/factura_pdf.html', factura=factura, organizacion=organizacion)


@factura_bp.route('/marcar_pago/<factura_id>', methods=['POST'])
@login_required
def marcar_pago(factura_id):
    if current_user.rol != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('factura.listar_facturas'))
    factura = get_factura_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada.', 'danger')
        return redirect(url_for('factura.listar_facturas'))
    if factura.estado == 'Pendiente':
        update_factura_estado(factura_id, 'Pagado')
        flash('Factura marcada como pagada.', 'success')
        return redirect(url_for('factura.ver_factura', factura_id=factura_id))
    else:
        flash('La factura ya está marcada como pagada.', 'info')
    return redirect(url_for('factura.ver_factura', factura_id=factura_id))


@factura_bp.route('/editar_factura/<factura_id>', methods=['GET', 'POST'])
@login_required
def editar_factura(factura_id):
    factura = get_factura_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada.', 'danger')
        return redirect(url_for('factura.listar_facturas'))
    if request.method == 'POST':
        cliente_nombre = request.form.get('cliente')
        descripcion = request.form.getlist('descripcion[]')
        cantidad = request.form.getlist('cantidad[]')
        precio_unitario = request.form.getlist('precio_unitario[]')
        
        # Protección contra error de conversión numérica
        try:
            total = float(request.form.get('total'))
        except (ValueError, TypeError):
            total = 0.0
            
        fecha = request.form.get('fecha')
        estado = request.form.get('estado')
        forma_pago = request.form.get('forma_pago', 'efectivo')
        
        if not all([cliente_nombre, descripcion, cantidad, precio_unitario, total, fecha, estado]):
            flash('Por favor, complete todos los campos obligatorios.', 'danger')
            return redirect(url_for('factura.editar_factura', factura_id=factura_id))
        
        items = procesar_items(descripcion, cantidad, precio_unitario)
        # Convertir fecha string a objeto datetime
        try:
            if fecha:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
            else:
                fecha_obj = datetime.now()
        except ValueError:
            fecha_obj = datetime.now()

        # Preservar estructura del cliente
        cliente_data = factura.cliente
        if isinstance(cliente_data, dict):
            cliente_data['nombre'] = cliente_nombre
            cliente_data['apellido'] = '' # Evitamos duplicidad ya que el input contenía ambos
        else:
            # Fallback por si acaso
            cliente_data = {'nombre': cliente_nombre, 'apellido': '', 'id': None}

        data_factura = {
            'cliente': cliente_data,
            'items': items,
            'total': total,
            'fecha_emision': fecha_obj,
            'estado': estado,
            'forma_pago': forma_pago or 'efectivo' 
        }
        exito = modificar_factura(factura_id, data_factura)
        if exito:
            flash('Factura actualizada exitosamente.', 'success')
            return redirect(url_for('factura.ver_factura', factura_id=factura_id))
        else:
            flash('Error al actualizar la factura.', 'danger')
    return render_template('factura/editar_factura.html', factura=factura)


@factura_bp.route('/eliminar_factura/<factura_id>', methods=['DELETE', 'GET'])
@login_required
def eliminar_factura(factura_id):
    if current_user.rol != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('factura.listar_facturas'))
    factura = get_factura_by_id(factura_id)
    if not factura:
        flash('Factura no encontrada.', 'danger')
        return redirect(url_for('factura.listar_facturas'))
    if eliminar_fact(factura_id):
        flash('Factura eliminada exitosamente.', 'success')
    else:
        flash('Error al eliminar la factura.', 'danger')
    return redirect(url_for('factura.listar_facturas'))


@factura_bp.route('/buscar', methods=['GET'])
@login_required
def buscar_facturas_route():
    organizacion_id = current_user.organizacion_id
    if not organizacion_id:
        return redirect(url_for('auth.login'))
    
    # Obtener filtros individuales
    filters = {
        'cliente': request.args.get('cliente', '').strip(),
        'vendedor': request.args.get('vendedor', '').strip(),
        'estado': request.args.get('estado', '').strip(),
        'fecha_desde': request.args.get('fecha_desde', ''),
        'fecha_hasta': request.args.get('fecha_hasta', '')
    }
    
    # Convertir fechas si existen
    try:
        if filters['fecha_desde']:
            filters['fecha_desde'] = datetime.strptime(filters['fecha_desde'], '%Y-%m-%d')
        if filters['fecha_hasta']:
            filters['fecha_hasta'] = datetime.strptime(filters['fecha_hasta'], '%Y-%m-%d')
    except ValueError:
        flash('Formato de fecha inválido', 'error')
        return redirect(url_for('factura.listar_facturas'))
    
    page = int(request.args.get('page', 1))
    per_page = 10
    skip = (page - 1) * per_page
    
    # Contar total (eficiente)
    try:
        query = {'organizacion_id': ObjectId(organizacion_id)}
        # Aquí reconstruyes el query para count...
        total_count = mongo.db.facturas.count_documents(query)
        total_pages = ceil(total_count / per_page) if total_count > 0 else 1
        
        # Obtener facturas
        facturas = list_facturas_filtradas(organizacion_id, filters, skip, per_page)
        
    except Exception as e:
        flash('Error en la búsqueda', 'error')
        return redirect(url_for('factura.listar_facturas'))
    
    pagination = {
        'page': page,
        'pages': total_pages,
        'total': total_count,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }
    
    if request.headers.get('HX-Request'):
        return render_template('factura/_factura_table.html', 
                             facturas=facturas, 
                             pagination=pagination,
                             filters=filters)

    return render_template('factura/_factura_table.html',  # Nueva template con filtros
                         facturas=facturas, 
                         pagination=pagination,
                         filters=filters)
