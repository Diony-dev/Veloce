from flask import blueprints, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..services.auth_services import authenticate_user, user_register, register_organizacion, update_user_profile
from ..services.organizacion_services import get_organizacion_by_id
from werkzeug.utils import secure_filename
#cloudinary
from flask import current_app
from bson.objectid import ObjectId
from app.database import mongo
from app.models.usuario import Usuario
from app.models.organizacion import Organizacion
import cloudinary.uploader
import logging
from datetime import datetime, timedelta
from app.services.email_services import send_invitation_email
from app.services.auth_services import generate_password_hash


auth_bp = blueprints.Blueprint('auth', __name__)
logger = logging.getLogger(__name__)
@auth_bp.route('register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
       nombre_org = request.form.get('nombre_org')
       direccion = request.form.get('direccion')
       telefono = request.form.get('telefono')
       email = request.form.get('email')
       rnc = request.form.get('rnc')
       logo = request.form.get('logo')
       org_id = register_organizacion(nombre_org, direccion, telefono, email, rnc, None)
       if org_id:
              logger.info(f'Organizacion registrada con ID: {org_id}')
              if logo:
                  upload = secure_filename(logo.filename)
                  upload_result = cloudinary.uploader.upload(upload, folder=f"fotos_facturacion/logo_organizaciones/{org_id}", public_id=str(org_id))
                  mongo.db.organizaciones.update_one(
                      {'_id': ObjectId(org_id)},
                      {'$set': {'logo': upload_result.get('secure_url')}}
                  )
              flash('Organización registrada exitosamente. Ahora registre al usuario.', 'success')
              return redirect(url_for('auth.register_user', org_id=org_id))
       if org_id is None:
            flash('Error al registrar la organización. El RNC ya existe.', 'danger')
            return redirect(url_for('auth.register'))
    return render_template('auth/register_organizacion.html')

@auth_bp.route("/register_user/<org_id>", methods=['GET', 'POST'])
def register_user(org_id):
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')
        rol = request.form.get('rol', default='admin')
        departamento = request.form.get('departamento', default='general')
        foto = request.form.get('foto', default='default.jpg')
        user_id = user_register(org_id,nombre, correo, contraseña, rol, departamento, foto)
        if user_id:
            logger.info(f'Usuario registrado con ID: {user_id}')
            if foto and foto != 'default.jpg':
                upload = secure_filename(foto.filename)
                upload_result = cloudinary.uploader.upload(upload, folder=f"fotos_facturacion/fotos_usuarios/{org_id}", public_id=str(user_id))
                mongo.db.usuarios.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': {'foto': upload_result.get('secure_url')}}
                )
            flash('Usuario registrado exitosamente. Ahora puede iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Error al registrar el usuario. El correo ya existe.', 'danger')
    return render_template('auth/register_user.html', org_id=org_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')
        user = authenticate_user(correo, contraseña)
        if user:
            login_user(user)
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Credenciales inválidas. Inténtalo de nuevo.', 'danger')
    return render_template('/auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))





@auth_bp.route('/register-invite/<token>', methods=['GET', 'POST'])
def register_via_invite(token):
    # 1. Buscar la invitación por token y que no haya sido usada
    invitacion = mongo.db.invitaciones.find_one({'token': token, 'usada': False})
    
    if not invitacion:
        flash('El enlace de invitación es inválido o ya fue usado.', 'danger')
        return redirect(url_for('auth.login'))
    
    # 2. Verificar si la invitación ha expirado (48 horas)
    if datetime.now() > invitacion['expira_en']:
        flash('Esta invitación ha expirado. Pide al administrador que te envíe una nueva.', 'warning')
        return redirect(url_for('auth.login'))

    # 3. Obtener nombre de la organización para mostrarlo en la bienvenida
    org = get_organizacion_by_id(invitacion['organizacion_id'])
    org_nombre = org.nombre if org else "la organización"

    # Preparar datos para pasar a la vista
    context = {
        'email': invitacion['email'],
        'role': invitacion['role'],
        'org_nombre': org_nombre,
        'token': token
    }

    # --- PROCESAR EL FORMULARIO (POST) ---
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validaciones básicas
        if not nombre or not password:
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('auth/register_invite.html', invitacion=context)
            
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('auth/register_invite.html', invitacion=context)

        # 4. Crear el Nuevo Usuario
        nuevo_usuario = {
            'email': invitacion['email'], # El email viene fijo de la invitación
            'nombre': nombre,
            'password': generate_password_hash(password), # IMPORTANTE: Encriptar password
            'organizacion_id': invitacion['organizacion_id'], # ¡Aquí está la magia! Lo vinculamos a la empresa.
            'role': invitacion['role'],
            'foto': 'default.jpg', # Foto por defecto
            'is_active': True,
            'created_at': datetime.now()
        }
        
        try:
            # Guardar usuario
            id_user = user_register(invitacion['organizacion_id'], nombre, invitacion['email'], password, invitacion['role'], 'general', 'default.jpg')
            if id_user is None:
                flash('Error al registrar el usuario. El correo ya existe.', 'danger')
                return render_template('auth/register_invite.html', invitacion=context)
            # 5. Marcar invitación como usada para que no se pueda volver a usar
            mongo.db.invitaciones.update_one(
                {'_id': invitacion['_id']},
                {'$set': {'usada': True}}
            )
            
            flash('¡Registro completado con éxito! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Error al registrar usuario: {str(e)}', 'danger')

    # --- MOSTRAR EL FORMULARIO (GET) ---
    return render_template('auth/register_invite.html', invitacion=context)

@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        foto = request.files['foto']
        org = get_organizacion_by_id(current_user.organizacion_id)
        org_name = org.nombre
        org_id = org.organizacion_id

        foto_url = None
        if foto and foto.filename != '':
            try:
                upload = secure_filename(foto.filename)
                upload_result = cloudinary.uploader.upload(foto, folder=f"fotos_facturacion/fotos_usuarios/{org_name}{org_id}", public_id=str(current_user.id))
                foto_url = upload_result.get('secure_url')
            except Exception as e:
                flash(f'Error al subir la imagen: {e}', 'danger')
                current_app.logger.error(f'Error al subir la imagen: {e}')
                return redirect(url_for('auth.perfil'))

        if update_user_profile(current_user.id, nombre, correo, foto_url):
            flash('Perfil actualizado correctamente', 'success')
            # Actualizar datos de sesión si es necesario, pero flask-login lo hará en el próximo request
        else:
            flash('No se pudieron guardar los cambios o no hubo cambios.', 'info')
            
        return redirect(url_for('auth.perfil'))
        
    return render_template('auth/perfil.html', user=current_user)