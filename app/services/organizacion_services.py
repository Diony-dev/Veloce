from ..database import mongo 
from ..models.organizacion import Organizacion
from flask import current_app as app
from bson.objectid import ObjectId



def get_organizacion_by_id(organizacion_id):
    try:
        organizacion_data = mongo.db.organizaciones.find_one({"_id": ObjectId(organizacion_id)})
        if organizacion_data:
            organizacion = Organizacion(
                organizacion_id=str(organizacion_data['_id']),
                nombre=organizacion_data['nombre'],
                direccion=organizacion_data['direccion'],
                telefono=organizacion_data['telefono'],
                email=organizacion_data['email'],
                rnc=organizacion_data['rnc'],
                logo=organizacion_data.get('logo')
            )
            return organizacion
        else:
            app.logger.warning(f"Organizacion con ID {organizacion_id} no encontrada.")
            return None
    except Exception as e:
        app.logger.error(f"Error al obtener organizacion por ID: {e}")
        return None

def update_organizacion(organizacion_id, nombre, direccion, telefono, email, rnc, logo=None):
    try:
        update_data = {
            'nombre': nombre,
            'direccion': direccion,
            'telefono': telefono,
            'email': email,
            'rnc': rnc,
            
        }
        if logo:
            update_data['logo'] = logo
        mongo.db.organizaciones.update_one({"_id": ObjectId(organizacion_id)}, {"$set": update_data})
        app.logger.info(f"Organizacion con ID {organizacion_id} actualizada exitosamente.")
        return True
    except Exception as e:
        app.logger.error(f"Error al actualizar organizacion: {e}")
        return False
        