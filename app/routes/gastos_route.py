from flask import Blueprint, request, jsonify, redirect, render_template, url_for, flash
import cloudinary.uploader
from app.services.gasto_services import crear_gastos, eliminar_gasto, get_gastos_by_id, list_gastos_by_organizacion
from app.services.auth_services import get_organizacion_by_id   
from app.models.gasto import Gasto
from flask_login import login_required, current_user
from datetime import datetime
from bson.objectid import ObjectId
from flask import current_app as app
from ..utils.cliente_util import admin_required


gastos_bp = Blueprint('gastos', __name__, url_prefix='/gastos')

@gastos_bp.route('/', methods=['GET'])
@login_required
def listar_gastos():
    page = request.args.get('page', 1, type=int)
    categoria = request.args.get('categoria')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    search = request.args.get('search')

    gastos, pagination = list_gastos_by_organizacion(
        current_user.organizacion_id,
        page=page,
        categoria=categoria,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        search=search
    )

    if request.headers.get('HX-Request'):
        return render_template('gastos/_gastos_table.html', gastos=gastos, pagination=pagination)
    
    return render_template('gastos/listar.html', gastos=gastos, pagination=pagination)


@gastos_bp.route('/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_gastos_route():
    org = get_organizacion_by_id(current_user.organizacion_id)
    
    if request.method == 'POST':
        descripcion = request.form.get('descripcion')
        monto_str = request.form.get('monto') # Recibimos como string temporalmente
        categoria = request.form.get('categoria')
        fecha_str = request.form.get('fecha') # Recibimos como string temporalmente
        proveedor = request.form.get('proveedor')
        
        # Validamos que los campos existan
        if not all([descripcion, monto_str, categoria, fecha_str]):
            flash('Campos obligatorios faltantes.', 'danger')
            return render_template('gastos/crear.html')

        # --- AJUSTE CRÍTICO 1: Convertir Monto a Número ---
        # Vital para que Mongo pueda sumar ($sum) en tus reportes
        try:
            monto_final = float(monto_str)
        except (ValueError, TypeError):
            flash('El monto debe ser un número válido.', 'danger')
            return render_template('gastos/crear.html')

        # --- AJUSTE CRÍTICO 2: Convertir Fecha a Objeto Datetime ---
        # Vital para agrupar por mes/año en tus gráficos
        try:
            # El input type="date" HTML envía formato YYYY-MM-DD
            fecha_final = datetime.strptime(fecha_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            # Si falla, usamos la fecha y hora actual como seguridad
            fecha_final = datetime.now()

        # Lógica de subida de imagen (Cloudinary)...
        comprobante_url = None
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(file, folder=f"fotos_facturacion/comprobantes_gastos/{org.nombre}_{org.organizacion_id}")
                    comprobante_url = upload_result.get('secure_url')
                except Exception as e:
                    app.logger.error(f"Error uploading comprobante: {e}")
                    flash('Error al subir el comprobante, pero se intentará guardar el gasto.', 'warning')

        # Pasamos los datos YA CONVERTIDOS al servicio
        gasto_id = crear_gastos(
            current_user.organizacion_id,
            descripcion,
            monto_final,  # <--- Pasamos el float, no el string
            categoria,
            fecha_final,  # <--- Pasamos el datetime object, no el string
            proveedor,
            comprobante=comprobante_url,
            registrado_por=current_user.nombre
        )
        
        if gasto_id:
            flash('Gasto registrado correctamente.', 'success')
            return redirect(url_for('gastos.listar_gastos'))
        else:
            flash('Error al registrar el gasto.', 'danger')

    return render_template('gastos/crear.html')


@gastos_bp.route('/eliminar/<gasto_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_gasto_route(gasto_id):
    if eliminar_gasto(current_user.organizacion_id, gasto_id):
        flash('Gasto eliminado.', 'success')
    else:
        flash('No se pudo eliminar el gasto.', 'danger')
    return redirect(url_for('gastos.listar_gastos'))


@gastos_bp.route('/ver/<gasto_id>', methods=['GET'])
@login_required
def ver_gasto(gasto_id):
    gasto = get_gastos_by_id(gasto_id)
    if not gasto:
        flash('Gasto no encontrado.', 'danger')
        return redirect(url_for('gastos.listar_gastos'))
    
    return render_template('gastos/ver.html', gasto=gasto)