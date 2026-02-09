from app import mongo
from bson import ObjectId
from datetime import datetime, timedelta

# ==========================================
# 1. KPIs PARA EL DASHBOARD PRINCIPAL
# ==========================================

def get_kpis_mes_actual(organizacion_id):
    """
    Calcula los indicadores clave (KPIs) del mes en curso:
    - Total Ingresos (Facturas Pagadas)
    - Total Gastos
    - Beneficio Neto
    - Cantidad de Facturas Pendientes
    """
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1) # Primer día del mes actual

    # PIPELINE 1: Total Ingresos del Mes
    pipeline_ingresos = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id),
            "estado": "Pagado",
            "fecha_emision": {"$gte": start_date}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    res_ingresos = list(mongo.db.facturas.aggregate(pipeline_ingresos))
    total_ingresos = res_ingresos[0]['total'] if res_ingresos else 0.0

    # PIPELINE 2: Total Gastos del Mes
    pipeline_gastos = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id),
            "fecha": {"$gte": start_date}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$monto"}}}
    ]
    res_gastos = list(mongo.db.gastos.aggregate(pipeline_gastos))
    total_gastos = res_gastos[0]['total'] if res_gastos else 0.0

    # CONSULTA SIMPLE: Conteo de Facturas Pendientes
    # No requiere pipeline complejo, count_documents es más eficiente aquí
    count_pendientes = mongo.db.facturas.count_documents({
        "organizacion_id": ObjectId(organizacion_id),
        "estado": {"$in": ["Enviado", "Vencido", "Borrador", "Pendiente"]}
    })

    return {
        "ingresos_mes": total_ingresos,
        "gastos_mes": total_gastos,
        "beneficio_neto": total_ingresos - total_gastos,
        "facturas_pendientes": count_pendientes
    }

# ==========================================
# 2. GRÁFICOS DEL DASHBOARD
# ==========================================

def get_comparativa_anual(organizacion_id, year=None):
    """
    Genera dos arrays (Ingresos y Gastos) mes a mes para el gráfico de barras.
    Retorna datos listos para Chart.js.
    """
    if not year:
        year = datetime.now().year

    # Inicializamos arrays con 12 ceros (Enero a Diciembre)
    ingresos = [0] * 12
    gastos = [0] * 12

    # PIPELINE 1: Ingresos por Mes (Facturas)
    pipeline_facturas = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id),
            "estado": "Pagado"
        }},
        # Paso intermedio: Convertir string a fecha si es necesario
        {"$addFields": {
            "fecha_obj": {"$toDate": "$fecha_emision"}
        }},
        {"$match": {
            "$expr": {"$eq": [{"$year": "$fecha_obj"}, int(year)]}
        }},
        {"$group": {
            "_id": {"$month": "$fecha_obj"}, # Agrupa por mes (retorna número 1-12)
            "total": {"$sum": "$total"}
        }}
    ]
    
    try:
        for doc in mongo.db.facturas.aggregate(pipeline_facturas):
            if doc["_id"] is not None:
                mes_idx = doc["_id"] - 1 # Ajuste índice (0 para Enero)
                if 0 <= mes_idx < 12:
                    ingresos[mes_idx] = doc["total"]
    except Exception as e:
        print(f"Error en pipeline facturas: {e}")

    # PIPELINE 2: Gastos por Mes
    pipeline_gastos = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id)
        }},
        # Paso intermedio: Convertir string a fecha si es necesario
        {"$addFields": {
            "fecha_obj": {"$toDate": "$fecha"}
        }},
        {"$match": {
            "$expr": {"$eq": [{"$year": "$fecha_obj"}, int(year)]}
        }},
        {"$group": {
            "_id": {"$month": "$fecha_obj"},
            "total": {"$sum": "$monto"}
        }}
    ]

    try:
        for doc in mongo.db.gastos.aggregate(pipeline_gastos):
            if doc["_id"] is not None:
                mes_idx = doc["_id"] - 1
                if 0 <= mes_idx < 12:
                    gastos[mes_idx] = doc["total"]
    except Exception as e:
        print(f"Error en pipeline gastos: {e}")

    return {
        "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
        "ingresos": ingresos,
        "gastos": gastos
    }

def get_gastos_por_categoria(organizacion_id):
    """
    Agrupa gastos por categoría para el gráfico de dona.
    """
    pipeline = [
        {"$match": {"organizacion_id": ObjectId(organizacion_id)}},
        {"$group": {
            "_id": "$categoria", # Agrupa por campo categoría
            "total": {"$sum": "$monto"} # Suma los montos
        }},
        {"$sort": {"total": -1}} # Ordena de mayor gasto a menor
    ]
    data = list(mongo.db.gastos.aggregate(pipeline))
    
    # Aseguramos que retornamos listas serializables
    return {
        "labels": [str(d["_id"]) if d["_id"] else "Sin Categoría" for d in data],
        "data": [float(d["total"]) for d in data]
    }

def get_top_clientes(organizacion_id, limit=5):
    """
    Obtiene los clientes que más dinero han generado (Facturas Pagadas).
    """
    pipeline = [
        {"$match": {
            "organizacion_id": ObjectId(organizacion_id), 
            "estado": "Pagado"
        }},
        # Paso intermedio: Normalizar nombre del cliente
        {"$addFields": {
            "nombre_completo": {
                "$cond": {
                    "if": {"$eq": [{"$type": "$cliente"}, "string"]},
                    "then": "$cliente",
                    "else": {"$concat": [
                        {"$ifNull": ["$cliente.nombre", ""]}, 
                        " ", 
                        {"$cond": {
                            "if": {"$eq": ["$cliente.apellido", "(Dato antiguo)"]},
                            "then": "",
                            "else": {"$ifNull": ["$cliente.apellido", ""]}
                        }}
                    ]}
                }
            },
            "group_id": {"$ifNull": ["$cliente_id", "$cliente"]}
        }},
        {"$group": {
            "_id": "$group_id", 
            "nombre_cliente": {"$first": "$nombre_completo"}, 
            "apellido_cliente": {"$first": ""}, # Ya concatenamos todo en nombre_cliente
            "total_gastado": {"$sum": "$total"},
            "count": {"$sum": 1} # Cuenta cuántas facturas ha pagado
        }},
        {"$sort": {"total_gastado": -1}}, # Orden Descendente
        {"$limit": limit}
    ]
    return list(mongo.db.facturas.aggregate(pipeline))

# ==========================================
# 3. REPORTE DE CUADRE DIARIO
# ==========================================

def get_cuadre_diario(organizacion_id, fecha=None):
    """
    Obtiene el detalle transaccional de un día específico.
    No usa aggregate complejo, sino consultas find() directas para obtener el detalle fila por fila.
    """
    if not fecha:
        fecha = datetime.now()
    elif isinstance(fecha, str):
        try:
            fecha = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            fecha = datetime.now()

    # Definir rango exacto del día (00:00:00 a 23:59:59)
    start_date = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 1. Obtener Facturas Pagadas (Ingresos)
    cursor_ingresos = mongo.db.facturas.find({
        "organizacion_id": ObjectId(organizacion_id),
        "estado": "Pagado",
        "fecha_emision": {"$gte": start_date, "$lte": end_date}
    }).sort("fecha_emision", 1)

    ingresos_detalles = []
    total_ingresos = 0.0
    total_efectivo = 0.0
    total_bancos = 0.0

    for f in cursor_ingresos:
        # Manejo defensivo por si el cliente es un string antiguo o dict
        nombre_cliente = "Cliente General"
        if isinstance(f.get("cliente"), dict):
            nombre_cliente = f"{f['cliente'].get('nombre', '')} {f['cliente'].get('apellido', '')}"
        elif isinstance(f.get("cliente"), str):
            nombre_cliente = f.get("cliente")

        forma_pago = f.get('forma_pago', 'efectivo') or 'efectivo' # Default a efectivo para seguridad
        
        ingresos_detalles.append({
            "hora": f["fecha_emision"].strftime("%H:%M"),
            "numero": f.get("invoice_num", "-"),
            "cliente": nombre_cliente,
            "vendedor": f.get("vendedor", "-"),
            "forma_pago": forma_pago,
            "total": f.get("total", 0.0)
        })
        
        # Segregación para el cuadre
        if forma_pago == 'efectivo':
            total_efectivo += f.get("total", 0.0)
        else:
            total_bancos += f.get("total", 0.0)
            
        total_ingresos += f.get("total", 0.0)

    # 2. Obtener Gastos (Egresos)
    cursor_gastos = mongo.db.gastos.find({
        "organizacion_id": ObjectId(organizacion_id),
        "fecha": {"$gte": start_date, "$lte": end_date}
    }).sort("fecha", 1)

    gastos_detalles = []
    total_gastos = 0.0

    for g in cursor_gastos:
        gastos_detalles.append({
            "hora": g["fecha"].strftime("%H:%M"),
            "descripcion": g.get("descripcion", "-"),
            "categoria": g.get("categoria", "-"),
            "registrado_por": g.get("registrado_por", "-"),
            "monto": g.get("monto", 0.0)
        })
        total_gastos += g.get("monto", 0.0)

    return {
        "fecha": fecha,
        "resumen": {
            "total_ingresos": total_ingresos,
            "total_efectivo": total_efectivo,
            "total_bancos": total_bancos,
            "total_gastos": total_gastos,
            "balance_neto": total_ingresos - total_gastos,
            "cant_ventas": len(ingresos_detalles),
            "cant_gastos": len(gastos_detalles)
        },
        "detalles_ingresos": ingresos_detalles,
        "detalles_gastos": gastos_detalles
    }