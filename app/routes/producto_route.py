from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services.producto_services import (
    create_producto, 
    list_productos_by_organizacion, 
    get_producto_by_id, 
    update_producto, 
    delete_producto,
    search_productos_by_nombre_codigo
)
# from app.utils.cliente_util import admin_required # Si se requiere permiso admin, descomentar e importar

producto_bp = Blueprint('producto', __name__)

@producto_bp.route('/', methods=['GET'])
@login_required
def listar_productos():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    
    productos, pagination = list_productos_by_organizacion(
        current_user.organizacion_id,
        page=page,
        search=search
    )
    
    if request.headers.get('HX-Request'):
        return render_template('productos/_producto_table.html', productos=productos, pagination=pagination)
        
    return render_template('productos/listar.html', productos=productos, pagination=pagination)

@producto_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear_producto_route():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        precio = request.form.get('precio')
        codigo = request.form.get('codigo')
        descripcion = request.form.get('descripcion')
        tipo = request.form.get('tipo', 'Servicio')
        stock = request.form.get('stock', 0)
        
        if not nombre or not precio:
            flash('Nombre y Precio son obligatorios', 'danger')
            return render_template('productos/crear.html')
            
        producto_id = create_producto(
            current_user.organizacion_id,
            nombre,
            precio,
            codigo,
            descripcion,
            tipo,
            stock
        )
        
        if producto_id:
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('producto.listar_productos'))
        else:
            flash('Error al crear el producto', 'danger')
            
    return render_template('productos/crear.html')

@producto_bp.route('/editar/<producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    producto = get_producto_by_id(producto_id)
    if not producto or str(producto.organizacion_id) != str(current_user.organizacion_id):
        flash('Producto no encontrado', 'danger')
        return redirect(url_for('producto.listar_productos'))
        
    if request.method == 'POST':
        data = {
            'nombre': request.form.get('nombre'),
            'precio': request.form.get('precio'),
            'codigo': request.form.get('codigo'),
            'descripcion': request.form.get('descripcion'),
            'tipo': request.form.get('tipo'),
            'stock': request.form.get('stock')
        }
        
        if update_producto(producto_id, data):
            flash('Producto actualizado correctamente', 'success')
            return redirect(url_for('producto.listar_productos'))
        else:
            flash('Error al actualizar el producto', 'danger')
            
    return render_template('productos/crear.html', producto=producto) # Reusamos el form de crear

@producto_bp.route('/eliminar/<producto_id>', methods=['POST'])
@login_required
def eliminar_producto_route(producto_id):
    # Validar propiedad
    producto = get_producto_by_id(producto_id)
    if not producto or str(producto.organizacion_id) != str(current_user.organizacion_id):
        flash('No tienes permiso', 'danger')
        return redirect(url_for('producto.listar_productos'))

    if delete_producto(producto_id):
        flash('Producto eliminado', 'success')
    else:
        flash('Error al eliminar', 'danger')
        
    return redirect(url_for('producto.listar_productos'))

@producto_bp.route('/buscar', methods=['GET'])
@login_required
def buscar_productos():
    q = request.args.get('q') or request.args.get('descripcion[]') or ''
    productos = []
    if len(q) > 1:
        productos = search_productos_by_nombre_codigo(current_user.organizacion_id, q)
    
    # Renderizamos un partial para usar en el dropdown de factura
    return render_template('productos/partials/_search_results.html', productos=productos)
