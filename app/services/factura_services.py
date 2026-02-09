from flask import current_app
from app.database import mongo
from app.models.factura import Factura
from bson.objectid import ObjectId
import re
from datetime import datetime
from math import ceil

def create_factura(organizacion_id, invoice_num, cliente, vendedor, items, total, fecha, estado='pendiente', forma_pago='efectivo'):
    try:

        

                    
        # Movido el insert para después de la validación
        factura_data = mongo.db.facturas.insert_one(
             {
                'organizacion_id': ObjectId(organizacion_id),
                'invoice_num': invoice_num,
                'cliente':{
                    'id': cliente.id,
                    'nombre': cliente.nombre,
                    'apellido': cliente.apellido,
                    'correo': cliente.correo,
                    'telefono': cliente.telefono,
                    'identificacion': cliente.identificacion,
                },
                'cliente_id': cliente.id,
                'vendedor': vendedor,
                'items': items,
                'total': total,
                'fecha_emision': fecha,
                'estado': estado,
                'forma_pago': forma_pago
            }
        )
        
        # --- DESCONTAR STOCK ---
        from app.services.producto_services import decrease_stock
        for item in items:
            # Asumimos que si tiene 'producto_id' viene del inventario
            # El campo puede venir como 'id' o 'producto_id' dependiendo de cómo lo mande el frontend
            prod_id = item.get('producto_id') or item.get('id') 
            
            # Solo intentamos descontar si tenemos un ID válido (mongo object id lookalike)
            if prod_id and len(str(prod_id)) == 24:
                try:
                    cantidad = float(item.get('cantidad', 0))
                    if cantidad > 0:
                        decrease_stock(prod_id, cantidad)
                except ValueError:
                    pass

        return str(factura_data.inserted_id)
    except Exception as e:
        print(f"Error al crear la factura: {e}")
        return None
    
def get_factura_by_id(factura_id):
    factura_data = mongo.db.facturas.find_one({'_id': ObjectId(factura_id)})
    if factura_data:
        return Factura(
            id=factura_data['_id'],
            organizacion_id=factura_data['organizacion_id'],
            invoice_num=factura_data['invoice_num'],
            vendedor=factura_data['vendedor'],
            cliente=factura_data['cliente'],
            fecha_emision=factura_data['fecha_emision'],
            items=factura_data['items'],
            total=factura_data['total'],
            estado=factura_data['estado'],
            forma_pago=factura_data.get('forma_pago', 'efectivo')
        )
    return None

def list_facturas_by_organizacion(organizacion_id, page=1, per_page=10, cliente=None, fecha_desde=None, fecha_hasta=None):
    skip = (page - 1) * per_page
    query = {'organizacion_id': ObjectId(organizacion_id)}

    # Filtro por cliente (búsqueda parcial)
    if cliente:
        query['cliente.nombre'] = {'$regex': re.escape(cliente), '$options': 'i'}

    # Filtro por fechas
    if fecha_desde and fecha_hasta:
        try:
            desde = datetime.strptime(fecha_desde, "%Y-%m-%d")
            hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d")
            query['fecha_emision'] = {'$gte': desde, '$lte': hasta}
        except ValueError:
            pass

    total = mongo.db.facturas.count_documents(query)
    cursor = (
        mongo.db.facturas.find(query)
        .skip(skip)
        .limit(per_page)
        .sort('fecha_emision', -1)
    )

    facturas = [
        Factura(
            id=f['_id'],
            organizacion_id=f['organizacion_id'],
            invoice_num=f['invoice_num'],
            vendedor=f['vendedor'],
            cliente=f['cliente'],
            fecha_emision=f['fecha_emision'],
            items=f['items'],
            total=f['total'],
            estado=f['estado'],
            forma_pago=f.get('forma_pago', 'efectivo')
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

    return facturas, pagination


def update_factura_estado(factura_id, nuevo_estado):
    try:
        result = (mongo.db.facturas.update_one(
            {'_id': ObjectId(factura_id)},
            {'$set': {'estado': nuevo_estado}}
        ))
        return result.modified_count > 0
    except Exception as e:
        print(f"Error al actualizar el estado de la factura: {e}")
        return False
    
def modificar_factura(factura_id, factura_data):
    try:
        result = mongo.db.facturas.update_one(
            {'_id': ObjectId(factura_id)},
            {'$set': factura_data}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error al modificar la factura: {e}")
        return False
    
def buscar_facturas(organizacion_id, criterio_busqueda='alan', skip=0, limit=12):
    try:
        factura_cursor = mongo.db.facturas.find({
            'organizacion_id': ObjectId(organizacion_id),
            '$or': [
                {'cliente.nombre': {'$regex': criterio_busqueda, '$options': 'i'}},
                {'vendedor.nombre': {'$regex': criterio_busqueda, '$options': 'i'}},
                {'estado': {'$regex': criterio_busqueda, '$options': 'i'}}
            ]
        }).sort('fecha_emision', -1).skip(skip).limit(limit)
        facturas = [Factura(
            id=factura_data['_id'],
            organizacion_id=factura_data['organizacion_id'],
            invoice_num=factura_data['invoice_num'],
            vendedor=factura_data['vendedor'],
            cliente=factura_data['cliente'],
            fecha_emision=factura_data['fecha_emision'],
            items=factura_data['items'],
            total=factura_data['total'],
            estado=factura_data['estado'],
            forma_pago=factura_data.get('forma_pago', 'efectivo')
        ) for factura_data in factura_cursor]
        return facturas
    except Exception as e:
        print(f"Error al buscar facturas: {e}")
        return []
    
def generate_invoice_number(organizacion_id):
    try:
        ultima_factura = mongo.db.facturas.find({'organizacion_id': ObjectId(organizacion_id)}).sort('invoice_num', -1).limit(1)
        if ultima_factura.count() > 0:
            ultimo_numero = ultima_factura[0]['invoice_num']
            nuevo_numero = int(ultimo_numero) + 1
        else:
            nuevo_numero = 1
        return str(nuevo_numero).zfill(6)  # Rellenar con ceros a la izquierda hasta 6 dígitos
    except Exception as e:
        print(f"Error al generar el número de factura: {e}")
        return None
    
def count_facturas_by_organizacion(organizacion_id):
    try:
        count = mongo.db.facturas.count_documents({'organizacion_id': ObjectId(organizacion_id)})
        return count
    except Exception as e:
        print(f"Error al contar las facturas: {e}")
        return 0
    
    
def eliminar_fact(factura_id):
    try:
        result = mongo.db.facturas.delete_one({'_id': ObjectId(factura_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error al eliminar la factura: {e}")
        return False
    
    
def list_facturas_by_criterio(organizacion_id, criterio_busqueda, skip=0, limit=12):
    factura_cursor = mongo.db.facturas.find({
        'organizacion_id': ObjectId(organizacion_id),
        '$or': [
            {'cliente.nombre': {'$regex': criterio_busqueda, '$options': 'i'}},
            {'vendedor.nombre': {'$regex': criterio_busqueda, '$options': 'i'}},
            {'estado': {'$regex': criterio_busqueda, '$options': 'i'}}
        ]
    }).skip(skip).limit(limit).sort('fecha_emision', -1)
    
    facturas = [
        Factura(
            id=f['_id'],
            organizacion_id=f['organizacion_id'],
            invoice_num=f['invoice_num'],
            vendedor=f['vendedor'],
            cliente=f['cliente'],
            fecha_emision=f['fecha_emision'],
            items=f['items'],
            total=f['total'],
            estado=f.get('estado', 'pendiente'),
            forma_pago=f.get('forma_pago', 'efectivo')
        ) for f in factura_cursor
    ]
    return facturas


def list_facturas_filtradas(organizacion_id, filters, skip=0, limit=12):
    """
    Busca facturas con filtros específicos
    
    Args:
        organizacion_id: ID de la organización
        filters: dict con filtros {
            'cliente': str,
            'vendedor': str, 
            'estado': str,
            'fecha_desde': date,
            'fecha_hasta': date
        }
    """
    query = {'organizacion_id': ObjectId(organizacion_id)}
    
    # Construir query dinámicamente
    if filters.get('cliente'):
        query['cliente.nombre'] = {
            '$regex': re.escape(filters['cliente']), 
            '$options': 'i'
        }
    
    if filters.get('vendedor'):
        query['vendedor.nombre'] = {
            '$regex': re.escape(filters['vendedor']), 
            '$options': 'i'
        }
    
    if filters.get('estado'):
        query['estado'] = filters['estado']  # Búsqueda exacta para estado
    
    # Filtro por rango de fechas
    if filters.get('fecha_desde') or filters.get('fecha_hasta'):
        fecha_query = {}
        if filters.get('fecha_desde'):
            fecha_query['$gte'] = filters['fecha_desde']
        if filters.get('fecha_hasta'):
            fecha_query['$lte'] = filters['fecha_hasta']
        query['fecha_emision'] = fecha_query
    
    factura_cursor = mongo.db.facturas.find(query)\
        .skip(skip).limit(limit)\
        .sort('fecha_emision', -1)
    
    # Aseguramos que f tenga forma_pago antes de desempaquetar o instanciamos explícitamente
    facturas_obj = []
    for f in factura_cursor:
        # Inyectamos el default si no existe para que **f funcione si las claves coinciden con los argumentos
        # Pero es mejor ser explícito:
        facturas_obj.append(Factura(
            id=f.get('_id'),
            organizacion_id=f.get('organizacion_id'),
            invoice_num=f.get('invoice_num'),
            vendedor=f.get('vendedor'),
            cliente=f.get('cliente'),
            fecha_emision=f.get('fecha_emision'),
            items=f.get('items', []),
            total=f.get('total'),
            estado=f.get('estado'),
            forma_pago=f.get('forma_pago', 'efectivo')
        ))
    return facturas_obj


def list_facturas_by_cliente(cliente_id, page=1, per_page=5):
    """
    Obtiene las facturas paginadas para un CLIENTE ESPECÍFICO.
    Usa el campo 'cliente_id' (que es un ObjectId).
    """
    try:
        skip = (page - 1) * per_page
        
        # --- LÓGICA DE CONSULTA CORREGIDA ---
        # Buscamos una coincidencia EXACTA del 'cliente_id'
        # Convertimos el string cliente_id de la URL a un ObjectId
        query = {'cliente_id': ObjectId(cliente_id)}

        total = mongo.db.facturas.count_documents(query)
        cursor = (
            mongo.db.facturas.find(query)
            .skip(skip)
            .limit(per_page)
            .sort('fecha_emision', -1)
        )

        facturas = []
        for f in cursor:
            # Reconstruye el objeto Factura
            # Nota: 'cliente' aquí es el DICT incrustado, ¡lo cual es perfecto!
            facturas.append(Factura(
                id=f['_id'],
                organizacion_id=f.get('organizacion_id'),
                invoice_num=f.get('invoice_num'),
                vendedor=f.get('vendedor'),
                cliente=f.get('cliente'), # El dict incrustado
                fecha_emision=f.get('fecha_emision'),
                items=f.get('items', []),
                total=f.get('total'),
                estado=f.get('estado'),
                forma_pago=f.get('forma_pago', 'efectivo')
            ))
        
        # Tu lógica de paginación manual
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

        return facturas, pagination

    except Exception as e:
        # Maneja el caso de un ObjectId inválido
        current_app.logger.error(f"Error al buscar facturas por cliente {cliente_id}: {e}")
        return [], {'page': page, 'per_page': per_page, 'total': 0, 'pages': 0}


    