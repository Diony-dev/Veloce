import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..database import mongo
from bson import ObjectId
from ..services.email_services import send_invitation_email
from ..utils.cliente_util import admin_required
from ..utils.date_util import get_now

team_bp = Blueprint('team', __name__, url_prefix='/equipo')

@team_bp.route('/')
@admin_required
@login_required
def listar_equipo():
    # Seguridad: Solo usuarios vinculados a una organización
    if not current_user.organizacion_id:
        flash('No tienes una organización asignada.', 'danger')
        return redirect(url_for('main.dashboard'))

    # 1. Obtener colaboradores activos
    colaboradores = list(mongo.db.usuarios.find({
        'organizacion_id': ObjectId(current_user.organizacion_id)
    }))

    # 2. Obtener invitaciones pendientes
    invitaciones = list(mongo.db.invitaciones.find({
        'organizacion_id': ObjectId(current_user.organizacion_id),
        'usada': False
    }))

    return render_template('config/equipo.html', colaboradores=colaboradores, invitaciones=invitaciones)

@team_bp.route('/invitar', methods=['POST'])
@admin_required
@login_required
def invitar_colaborador():
    email = request.form.get('email')
    role = request.form.get('role')

    if not email or not role:
        flash('Todos los campos son obligatorios.', 'warning')
        return redirect(url_for('team.listar_equipo'))

    # Verificar si el usuario ya existe en el sistema globalmente (opcional) o en la org
    existing_user = mongo.db.usuarios.find_one({'email': email})
    if existing_user:
        flash('Este usuario ya está registrado en Veloce.', 'warning')
        return redirect(url_for('team.listar_equipo'))

    # Verificar si ya tiene invitación pendiente
    existing_invite = mongo.db.invitaciones.find_one({
        'email': email, 
        'organizacion_id': ObjectId(current_user.organizacion_id),
        'usada': False
    })
    if existing_invite:
        flash('Ya existe una invitación pendiente para este correo.', 'info')
        return redirect(url_for('team.listar_equipo'))

    # Crear Token y guardar invitación
    token = secrets.token_urlsafe(32)
    now = get_now()
    invitacion = {
        'email': email,
        'role': role,
        'organizacion_id': ObjectId(current_user.organizacion_id),
        'token': token,
        'creado_por': current_user.id,
        'fecha_creacion': now,
        'expira_en': now + timedelta(hours=48),
        'usada': False
    }
    
    mongo.db.invitaciones.insert_one(invitacion)

    # Obtener nombre de la organización para el correo
    org = mongo.db.organizaciones.find_one({'_id': ObjectId(current_user.organizacion_id)})
    org_name = org.get('nombre_legal', 'Nuestra Empresa') if org else 'Nuestra Empresa'

    # Enviar Email
    exito, msg = send_invitation_email(email, org_name, role, token)
    
    if exito:
        flash(f'Invitación enviada correctamente a {email}', 'success')
    else:
        flash(f'Invitación guardada, pero falló el envío del correo: {msg}', 'warning')

    return redirect(url_for('team.listar_equipo'))

@team_bp.route('/eliminar/<user_id>', methods=['POST'])
@admin_required
@login_required
def eliminar_colaborador(user_id):
    if user_id == current_user.id:
        flash('No puedes eliminarte a ti mismo.', 'danger')
        return redirect(url_for('team.listar_equipo'))

    # Eliminar usuario (Hard Delete)
    result = mongo.db.usuarios.delete_one({
        '_id': ObjectId(user_id),
        'organizacion_id': ObjectId(current_user.organizacion_id)
    })
    
    if result.deleted_count > 0:
        flash('Colaborador eliminado del equipo.', 'success')
    else:
        flash('No se pudo eliminar el usuario.', 'danger')
        
    return redirect(url_for('team.listar_equipo'))

@team_bp.route('/cancelar-invitacion/<invitacion_id>', methods=['POST'])
@admin_required
@login_required
def cancelar_invitacion(invitacion_id):
    mongo.db.invitaciones.delete_one({
        '_id': ObjectId(invitacion_id),
        'organizacion_id': ObjectId(current_user.organizacion_id)
    })
    flash('Invitación cancelada.', 'success')
    return redirect(url_for('team.listar_equipo'))

@team_bp.route('/cambiar-rol/<user_id>', methods=['POST'])
@admin_required
@login_required
def cambiar_rol(user_id):
    if user_id == current_user.id:
        flash('No puedes cambiar tu propio rol aquí.', 'warning')
        return redirect(url_for('team.listar_equipo'))

    nuevo_rol = request.form.get('role')
    mongo.db.usuarios.update_one(
        {'_id': ObjectId(user_id), 'organizacion_id': ObjectId(current_user.organizacion_id)},
        {'$set': {'rol': nuevo_rol}}
    )
    flash('Rol actualizado.', 'success')
    return redirect(url_for('team.listar_equipo'))