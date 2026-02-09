from app.database import mongo
from app.models.usuario import Usuario
from app.models.organizacion import Organizacion
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

def authenticate_user(correo, contraseña):
    user_data = mongo.db.usuarios.find_one({'correo': correo})
    if user_data and check_password_hash(user_data['contraseña'], contraseña):
        return Usuario(
            id=user_data['_id'],
            organizacion_id=user_data['organizacion_id'],
            nombre=user_data['nombre'],
            correo=user_data['correo'],
            contraseña=user_data['contraseña'],
            rol=user_data['rol'],
            departamento=user_data['departamento'],
            foto=user_data['foto']
        )
    return None

def user_register(org_id,nombre, correo, contraseña, rol, departamento, foto):
    if exists_user_email(correo):
        return None  # Usuario ya existe
    try:
        new_user = mongo.db.usuarios.insert_one(
            {
                'organizacion_id': ObjectId(org_id),
                'nombre': nombre,
                'correo': correo,
                'contraseña': generate_password_hash(contraseña),
                'rol': rol,
                'departamento': departamento,
                'foto': foto
            }
        )
        return str(new_user.inserted_id)
    except Exception as e:
        print(f"Error al registrar el usuario: {e}")
        return None   
    

def register_organizacion(nombre_org, direccion, telefono, email, rnc, logo):
    if exists_organizacion_rnc(rnc):
        return None  # Organización ya existe
    
    try:
        organizacion_data = mongo.db.organizaciones.insert_one(
            {
                
                'nombre': nombre_org,
                'direccion': direccion,
                'telefono': telefono,
                'email': email,
                'rnc': rnc,
                'logo': logo
            }
        )
        return str(organizacion_data.inserted_id)
    except Exception as e:
        print(f"Error al registrar la organización: {e}")
        return None

def get_user_by_id(user_id):
    user_data = mongo.db.usuarios.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return Usuario(
            id=user_data['_id'],
            organizacion_id=user_data['organizacion_id'],
            nombre=user_data['nombre'],
            correo=user_data['correo'],
            contraseña=user_data['contraseña'],
            rol=user_data['rol'],
            departamento=user_data['departamento'],
            foto=user_data.get('foto', 'default.jpg')
        )
    return None

def exists_user_email(correo):
    user_data = mongo.db.usuarios.find_one({'correo': correo})
    return user_data is not None

def exists_organizacion_rnc(rnc):
    org_data = mongo.db.organizaciones.find_one({'rnc': rnc})
    return org_data is not None


def get_organizacion_by_id(org_id):
    org_data = mongo.db.organizaciones.find_one({'_id': ObjectId(org_id)})
    if org_data:
        return Organizacion(
            organizacion_id=org_data['_id'],
            nombre=org_data['nombre'],
            direccion=org_data['direccion'],
            telefono=org_data['telefono'],
            email=org_data['email'],
            rnc=org_data['rnc'],
            logo=org_data['logo'],
            moneda=org_data.get('moneda', 'RD$')
        )
    return None

def update_user_profile(user_id, nombre, correo, foto=None):
    try:
        update_data = {
            'nombre': nombre,
            'correo': correo
        }
        if foto:
            update_data['foto'] = foto
            
        result = mongo.db.usuarios.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0 or result.matched_count > 0
    except Exception as e:
        print(f"Error al actualizar perfil: {e}")
        return False