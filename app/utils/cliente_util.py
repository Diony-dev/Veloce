from functools import wraps
from flask import blueprints, render_template, redirect, url_for, request, flash
from flask_login import current_user
from app.database import mongo
from bson.objectid import ObjectId


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('No tienes permiso para acceder a esta página.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function        


def verify_exits( correo, organization_id):
    cliente = mongo.db.clientes.find_one({'organizacion_id':ObjectId(organization_id),
                                          'correo':correo})
    if cliente:
        return cliente
    return None
    
