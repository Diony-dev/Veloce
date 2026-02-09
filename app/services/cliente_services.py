from ..database import mongo
from ..models.cliente import Cliente
from bson.objectid import ObjectId
from datetime import datetime
from math import ceil
from ..utils.cliente_util import verify_exits
from flask import flash, current_app

def create_cliente(nombre, apellido, correo, telefono, organizacion_id, identificacion=None):
    try:
        correo = correo.lower()
        cliente_exists = verify_exits(correo, organizacion_id)
        if cliente_exists:
            flash('Ese correo ya esta registrado para clientes', 'danger')
            return None
        cliente_data = mongo.db.clientes.insert_one(
            {
                'organizacion_id': ObjectId(organizacion_id),
                'nombre': nombre,
                'apellido':apellido,
                'correo': correo,
                'telefono': telefono,
                'identificacion': identificacion,
                'created_at': datetime.utcnow()
            }
        )
        return str(cliente_data.inserted_id)
    except Exception as e:
        print(f"Error al crear el cliente: {e}")
        return None
    
def list_clientes_by_organizacion(organizacion_id, page=1, per_page=10, cliente=None, fecha_desde=None, fecha_hasta=None):
    skip = (page - 1) * per_page
    query = {'organizacion_id': ObjectId(organizacion_id)}

    import re
    # Filtro por cliente (búsqueda parcial)
    if cliente:
        query['$or'] = [
            {'nombre': {'$regex': re.escape(cliente), '$options': 'i'}},
            {'apellido': {'$regex': re.escape(cliente), '$options': 'i'}}
        ]

    # Filtro por fechas
    if fecha_desde and fecha_hasta:
        try:
            desde = datetime.strptime(fecha_desde, "%Y-%m-%d")
            hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d").replace(hour=23, minute=59, second=59) 
            query['created_at'] = {'$gte': desde, '$lte': hasta}
        except ValueError:
            pass

    total = mongo.db.clientes.count_documents(query)
    cursor = (
        mongo.db.clientes.find(query)
        .skip(skip)
        .limit(per_page)
        .sort('created_at', -1)
    )

    clientes = [
        Cliente(
            id=f['_id'],
            organizacion_id=f['organizacion_id'],
            nombre=f['nombre'],
            apellido = f['apellido'],
            correo=f['correo'],
            telefono=f['telefono'],
            created_at=f['created_at'],
            identificacion=f['identificacion'],
        ) for f in cursor
    ]

    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': ceil(total / per_page),
        'has_prev': page > 1,
        'has_next': page < ceil(total / per_page),
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page < ceil(total / per_page) else None
    }

    return clientes, pagination

def get_cliente_by_id(cliente_id):
    cliente_data = mongo.db.clientes.find_one({'_id': ObjectId(cliente_id)})
    if cliente_data:
        return Cliente(
            id=cliente_data['_id'],
            organizacion_id=cliente_data['organizacion_id'],
            nombre=cliente_data['nombre'],
            apellido=cliente_data['apellido'],
            correo=cliente_data['correo'],
            telefono=cliente_data['telefono'],
            created_at=cliente_data['created_at'],
            identificacion=cliente_data['identificacion'],
        )
    return None
def update_cliente(cliente_id, data_cliente):
    try:
        correo = data_cliente.get('correo', '').lower()
        cliente_exists = verify_exits(correo,  cliente_id)
        if cliente_exists:
            flash('Ese correo ya esta registrado para otro cliente', 'danger')
            return False
        datos_a_actualizar = {k:v for k, v in data_cliente.items() if v is not None}
        result = mongo.db.clientes.update_one(
            {'_id': ObjectId(cliente_id)},
            {
                '$set': datos_a_actualizar
            }
        )
        current_app.logger.info(f"Cliente {cliente_id} actualizado correctamente.")
        return result.modified_count > 0
    except Exception as e:
        current_app.logger.error(f"Error al actualizar el cliente: {e}")
        return False
    

def delete_cliente(cliente_id):
    """
    Elimina un cliente por su ID.
    """
    try:
        # Opcional: Verificar si tiene facturas antes de borrar
        # facturas_count = mongo.db.facturas.count_documents({'cliente_id': ObjectId(cliente_id)})
        # if facturas_count > 0:
        #     return False  # No borrar si tiene historial
        
        result = mongo.db.clientes.delete_one({'_id': ObjectId(cliente_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error eliminando cliente: {e}")
        return False

def get_cliente_by_org(organizacion_id):
    try:
        clientes_cursor = mongo.db.clientes.find({'organizacion_id': ObjectId(organizacion_id)})
        clientes = []
        for cliente_data in clientes_cursor:
            cliente = Cliente(
                id=cliente_data['_id'],
                organizacion_id=cliente_data['organizacion_id'],
                nombre=cliente_data['nombre'],
                apellido=cliente_data['apellido'],
                correo=cliente_data['correo'],
                telefono=cliente_data['telefono'],
                created_at=cliente_data['created_at'],
                identificacion=cliente_data['identificacion'],
            )
            clientes.append(cliente)
        return clientes
    except Exception as e:
        current_app.logger.error(f"Error al obtener clientes por organización: {e}")
        return []
    
def search_clientes_by_name(organizacion_id, search_term, limit=5):
    """
    Busca clientes por nombre dentro de una organización.
    """
    query = {
        'organizacion_id': ObjectId(organizacion_id),
        # Buscamos en el nombre O el apellido
        '$or': [
            {'nombre': {'$regex': search_term, '$options': 'i'}},
            {'apellido': {'$regex': search_term, '$options': 'i'}}
        ]
    }
    
    cursor = mongo.db.clientes.find(query).limit(limit)
    
    # Reconstruye los objetos Cliente
    clientes = [
        Cliente(
            id=c['_id'],
            # ... todos los otros campos ...
            nombre=c.get('nombre'),
            apellido=c.get('apellido'),
            identificacion=c.get('identificacion'),
            organizacion_id=c.get('organizacion_id'),
            correo=c.get('correo'),
            telefono=c.get('telefono'),
            created_at=c.get('created_at'),
            
            # ... etc
        ) for c in cursor
    ]
    return clientes