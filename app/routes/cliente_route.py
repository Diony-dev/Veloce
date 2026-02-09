from flask import blueprints, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from ..services.cliente_services import create_cliente, delete_cliente, list_clientes_by_organizacion, get_cliente_by_id, search_clientes_by_name, update_cliente
from ..services.factura_services import list_facturas_by_cliente as get_facturas_by_cliente_id
from ..utils.cliente_util import admin_required
cliente_bp = blueprints.Blueprint('cliente',__name__)

@cliente_bp.route('/', methods=['GET'])
@login_required
def listar_clientes():
    page = request.args.get('page', 1, type=int)
    cliente = request.args.get('cliente')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    clientes, pagination = list_clientes_by_organizacion(
        current_user.organizacion_id,
        page=page,
        cliente=cliente,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

    # Renderiza todo si NO es HTMX
    if not request.headers.get('HX-Request'):
        return render_template('clients/lista.html', clientes=clientes, pagination=pagination)

    # Renderiza solo el partial si es HTMX
    return render_template('clients/_cliente_table.html', clientes=clientes, pagination=pagination)

@cliente_bp.route('/add', methods =['GET', 'POST'])
@login_required
def create_client():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        correo = request.form.get('correo')
        telefono = request.form.get('tel')
        identificacion = request.form.get('ident')
        if not all([nombre, apellido, correo, telefono]):
            current_app.logger.error('falto algun campo importante en el registro')
            flash('Todo los campos deben ser registrados', 'danger')
            return redirect(url_for('cliente.create_client'))
        cliente = create_cliente(nombre,apellido, correo, telefono, current_user.organizacion_id,
                                 identificacion)
        if not cliente:
            current_app.logger.error('ocurrio un error al registrar al cliente, probablemente su correo ya esta registrado')
            return redirect(url_for('cliente.create_client'))
        current_app.logger.info('Cliente registrado correctamente')
        flash('Cliente registrado correctamente', 'success')
        return redirect(url_for('cliente.listar_clientes'))
    return render_template('clients/crear_cliente.html')

@cliente_bp.route('/ver/<cliente_id>', methods=['GET'])
@login_required
def ver_cliente(cliente_id):
    cliente = get_cliente_by_id(cliente_id)
    facturas, paginacion = get_facturas_by_cliente_id(cliente_id, page=request.args.get('page', 1, type=int), per_page=5)
    if not cliente or str(cliente.organizacion_id) != str(current_user.organizacion_id):
        current_app.logger.error('El cliente no existe o no pertenece a su organización')
        flash('El cliente no existe o no pertenece a su organización', 'danger')
        return redirect(url_for('cliente.listar_clientes'))
    current_app.logger.info(f'Visualizando detalles del cliente: {cliente.nombre} {cliente.apellido} {cliente.id}')
    current_app.logger.info(f'Facturas del cliente: {len(facturas)} encontradas')
    if request.headers.get('HX-Request'):
        print(facturas)
        return render_template('clients/partials/_facturas_cliente.html', facturas=facturas, pagination=paginacion, cliente=cliente)
    print(facturas)
    return render_template('clients/ver.html', cliente=cliente, facturas=facturas, pagination=paginacion)


@cliente_bp.route('/buscar')
@login_required
def buscar_clientes():
    # El término de búsqueda viene de la URL (ej. /buscar?q=Darlyn)
    q = request.args.get('q', '')
    clientes = []
    
    # No busques si el término es muy corto
    if len(q) > 1:
        clientes = search_clientes_by_name(current_user.organizacion_id, q)
        
    # Renderizamos un FRAGMENTO (parcial) de HTML, no una página completa
    return render_template('clients/partials/_search_results.html', clientes=clientes)

@cliente_bp.route('/editar/<cliente_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_cliente(cliente_id):
    cliente = get_cliente_by_id(cliente_id)
    
    if not cliente:
        flash('Cliente no encontrado.', 'danger')
        return redirect(url_for('cliente.listar_clientes'))

    # Verificar que el cliente pertenezca a la organización del usuario
    if str(cliente.organizacion_id) != str(current_user.organizacion_id):
        flash('No tienes permiso para editar este cliente.', 'danger')
        return redirect(url_for('cliente.listar_clientes'))

    if request.method == 'POST':
        # Recolectar datos del formulario
        datos = {
            'nombre': request.form.get('nombre'),
            'apellido': request.form.get('apellido'),
            'correo': request.form.get('correo'),
            'telefono': request.form.get('telefono'),
            'identificacion': request.form.get('identificacion')
        }
        
        if update_cliente(cliente_id, datos):
            flash('Cliente actualizado correctamente.', 'success')
            return redirect(url_for('cliente.ver_cliente', cliente_id=cliente_id))
        else:
            flash('Error al actualizar el cliente.', 'danger')

    return render_template('clients/editar_cliente.html', cliente=cliente)

@cliente_bp.route('/eliminar/<cliente_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_cliente(cliente_id):
    cliente = get_cliente_by_id(cliente_id)
    
    if not cliente or str(cliente.organizacion_id) != str(current_user.organizacion_id):
        flash('No tienes permiso o el cliente no existe.', 'danger')
        return redirect(url_for('cliente.listar_clientes'))

    if delete_cliente(cliente_id):
        flash('Cliente eliminado correctamente.', 'success')
    else:
        flash('Error al eliminar el cliente (puede tener datos relacionados).', 'danger')
        
    return redirect(url_for('cliente.listar_clientes'))