from flask import Blueprint, request, jsonify, render_template, url_for, redirect, current_app, flash
from ..services.organizacion_services import get_organizacion_by_id, update_organizacion

from ..models.organizacion import Organizacion
from ..utils.cliente_util import admin_required

from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.database import mongo
from app.models.organizacion import Organizacion
import cloudinary.uploader
import logging

config_bp = Blueprint('config', __name__)

@config_bp.route('/ajustes', methods=['GET', 'POST'])
@login_required
@admin_required
def ajustes():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        rnc = request.form.get('rnc')
        logo_url = None
        org_id = current_user.organizacion_id   

        if not all([nombre, direccion, telefono, email, rnc]):
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('config.ajustes'))
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo.filename != '':
                try:
                    upload_result = cloudinary.uploader.upload(logo, folder=f"fotos_facturacion/logo_organizaciones/", public_id=f'logo_{org_id}_{nombre}')
                    logo_url = upload_result.get('secure_url')
                except Exception as e:
                    app.logger.error(f"Error uploading logo: {e}")
                    flash('Error al subir el logo, pero se intentará guardar la organización.', 'warning')

        org = update_organizacion(org_id, nombre, direccion, telefono, email, rnc, logo_url)
        if org:
            flash('Organización actualizada correctamente.', 'success')
            return redirect(url_for('config.ajustes'))
        else:
            flash('Error al actualizar la organización.', 'danger')
            return redirect(url_for('config.ajustes'))
    else:
        org = get_organizacion_by_id(current_user.organizacion_id)
        return render_template('config/ajustes.html', org=org)  


            
        