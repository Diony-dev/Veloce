from ..database import mongo 
from ..models.gasto import Gasto
from datetime import datetime
from bson.objectid import ObjectId
from flask import current_app as app
from math import ceil

def crear_gastos(organizacion_id, descripcion, monto, categoria, fecha, proveedor=None, comprobante=None, registrado_por=None):
    try:
        nuevo_gasto =  mongo.db.gastos.insert_one( {
            "organizacion_id": ObjectId(organizacion_id),
            "descripcion": descripcion,
            "monto": float(monto),
            "categoria": categoria,
            "fecha": fecha,
            "proveedor": proveedor,
            "comprobante": comprobante,
            "registrado_por": registrado_por
        })
        app.logger.info(f"Gasto creado con ID: {nuevo_gasto.inserted_id}")
  
        return str(nuevo_gasto.inserted_id)
    except Exception as e:
        app.logger.error(f"Error al crear gasto: {e}")
        return None

def get_gastos_by_id(gasto_id):
    try:
        gasto_data = mongo.db.gastos.find_one({"_id": ObjectId(gasto_id)})
        if gasto_data:
            gasto = Gasto(
                id=str(gasto_data['_id']),
                organizacion_id=str(gasto_data['organizacion_id']),
                descripcion=gasto_data['descripcion'],
                monto=gasto_data['monto'],
                categoria=gasto_data['categoria'],
                fecha=gasto_data['fecha'],
                proveedor=gasto_data.get('proveedor'),
                comprobante=gasto_data.get('comprobante'),
                registrado_por=gasto_data.get('registrado_por')
            )
            return gasto
        else:
            app.logger.warning(f"Gasto con ID {gasto_id} no encontrado.")
            return None
    except Exception as e:
        app.logger.error(f"Error al obtener gasto por ID: {e}")
        return None



def list_gastos_by_organizacion(organizacion_id, page=1, per_page=10, categoria=None, fecha_desde=None, fecha_hasta=None, search=None):
    """
    Lista los gastos de una organización con paginación y múltiples filtros.
    """
    try:
        skip = (page - 1) * per_page
        
        # Filtro base: Solo gastos de esta organización
        query = {'organizacion_id': ObjectId(organizacion_id)}
        
        # --- Filtros Opcionales ---
        
        # 1. Por Categoría (Exacta)
        if categoria and categoria != "":
            query['categoria'] = categoria
            
        # 2. Búsqueda por Texto (Regex en Descripción o Proveedor)
        if search and search != "":
            query['$or'] = [
                {'descripcion': {'$regex': search, '$options': 'i'}},
                {'proveedor': {'$regex': search, '$options': 'i'}}
            ]

        # 3. Rango de Fechas
        if fecha_desde and fecha_hasta:
            try:
                desde = datetime.strptime(fecha_desde, "%Y-%m-%d")
                hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d")
                # Ajustamos 'hasta' para incluir el final del día (23:59:59)
                hasta = hasta.replace(hour=23, minute=59, second=59)
                query['fecha'] = {'$gte': desde, '$lte': hasta}
            except ValueError:
                pass # Si las fechas no son válidas, las ignoramos

        # --- Ejecución de la Consulta ---
        
        total = mongo.db.gastos.count_documents(query)
        
        cursor = (
            mongo.db.gastos.find(query)
            .skip(skip)
            .limit(per_page)
            .sort('fecha', -1) # Ordenar: Más recientes primero
        )
        
        # Convertimos los documentos BSON a objetos Gasto
        gastos = [
            Gasto(
                id=g['_id'],
                organizacion_id=g['organizacion_id'],
                descripcion=g.get('descripcion'),
                monto=g.get('monto'),
                categoria=g.get('categoria'),
                fecha=g.get('fecha'),
                proveedor=g.get('proveedor'),
                comprobante=g.get('comprobante'),
                registrado_por=g.get('registrado_por')
            ) for g in cursor
        ]
        
        # Construimos el objeto de paginación
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': ceil(total / per_page),
            'has_prev': page > 1,
            'has_next': page < ceil(total / per_page),
            'prev_num': page - 1,
            'next_num': page + 1
        }
        
        return gastos, pagination
        
    except Exception as e:
        print(f"Error al listar gastos: {e}")
        # En caso de error, devolvemos lista vacía para no romper la vista
        return [], {'page': 1, 'pages': 0, 'total': 0}
    
def eliminar_gasto(organizacion_id, gasto_id):
    try:
        resultado = mongo.db.gastos.delete_one({"_id": ObjectId(gasto_id), "organizacion_id": ObjectId(organizacion_id)})
        if resultado.deleted_count == 1:
            app.logger.info(f"Gasto con ID {gasto_id} eliminado exitosamente.")
            return True
        else:
            app.logger.warning(f"Gasto con ID {gasto_id} no encontrado para eliminar.")
            return False
    except Exception as e:
        app.logger.error(f"Error al eliminar gasto: {e}")
        return False


