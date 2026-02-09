from app import mongo
from bson import ObjectId
from datetime import datetime

def get_cuentas_por_cobrar(organizacion_id):
    """
    Retorna todas las facturas que están pendientes de pago.
    Estados considerados deuda: 'Pendiente', 'Enviado', 'Vencido'
    """
    pipeline = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id),
            "estado": {"$in": ["Pendiente", "Enviado", "Vencido"]}
        }},
        {"$project": {
            "invoice_num": 1,
            "cliente": 1,
            "fecha_emision": 1,
            "total": 1,
            "estado": 1,
            "dias_vencido": {
                "$divide": [
                    {"$subtract": [datetime.now(), "$fecha_emision"]},
                    1000 * 60 * 60 * 24 # Milisegundos a días
                ]
            }
        }},
        {"$sort": {"fecha_emision": 1}} # Las más antiguas primero
    ]
    return list(mongo.db.facturas.aggregate(pipeline))

def get_reporte_fiscal(organizacion_id, fecha_inicio, fecha_fin):
    """
    Genera reporte para impuestos (ITBIS).
    Asume que el TOTAL guardado incluye ITBIS (18%).
    """
    start = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    end = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    pipeline = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id),
            "estado": "Pagado", # Solo facturas pagadas o emitidas? Usualmente emitidas validas.
            "fecha_emision": {"$gte": start, "$lte": end}
        }},
        {"$project": {
            "fecha": "$fecha_emision",
            "ncf": "$invoice_num", # Asumiendo invoice_num como referencia fiscal
            "cliente": "$cliente",
            "total_facturado": "$total",
            # Calculo inverso del ITBIS (Total = Base + 18% Base => Total = 1.18 Base => Base = Total / 1.18)
            "base_imponible": {"$divide": ["$total", 1.18]},
            "itbis_calculado": {"$subtract": ["$total", {"$divide": ["$total", 1.18]}]}
        }},
        {"$sort": {"fecha": 1}}
    ]
    return list(mongo.db.facturas.aggregate(pipeline))

def get_ventas_por_rango(organizacion_id, fecha_inicio, fecha_fin):
    """
    Reporte simple de ventas por rango.
    """
    start = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    end = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    pipeline = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id),
            "estado": "Pagado",
            "fecha_emision": {"$gte": start, "$lte": end}
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha_emision"}},
            "total_ventas": {"$sum": "$total"},
            "cantidad_facturas": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    return list(mongo.db.facturas.aggregate(pipeline))

def get_gastos_por_rango(organizacion_id, fecha_inicio, fecha_fin):
    """
    Reporte de gastos por rango de fechas (Cuentas por Pagar / Egresos).
    """
    start = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    end = datetime.strptime(fecha_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    pipeline = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id),
            "fecha": {"$gte": start, "$lte": end}
        }},
        {"$sort": {"fecha": 1}}
    ]
    return list(mongo.db.gastos.aggregate(pipeline))
