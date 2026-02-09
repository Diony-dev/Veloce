

from app.database import mongo
from bson.objectid import ObjectId
import re # Necesitamos 're' para extraer el número secuencial si usas el formato FCT-ORG-AÑO-SECUENCIA
from datetime import datetime
import random
from app.models.factura import Factura
        
def generar_numero_factura_timestamp(prefijo="F"):
        """Usa timestamp + random para evitar colisiones"""
        timestamp = int(datetime.now().timestamp())
        random_suffix = random.randint(100, 999)
        return f"{prefijo}-{timestamp}{random_suffix}"
    
def generar_numero_factura_fecha(prefijo="F"):
        """Usa fecha y conteo del día - RECOMENDADO"""
        hoy = datetime.now()
        fecha_str = hoy.strftime("%Y%m%d")
        
        # Contar facturas de hoy
        inicio_dia = datetime(hoy.year, hoy.month, hoy.day)
        facturas_hoy = mongo.db.facturas.count_documents({
            'creado_en': {'$gte': inicio_dia}
        })
        
        secuencia = facturas_hoy + 1
        return f"{prefijo}-{fecha_str}-{secuencia:04d}"
        
def procesar_items(descripciones, cantidades, precios_unitarios):
    items = []
    for desc, cant, precio in zip(descripciones, cantidades, precios_unitarios):
        try:
            item = {
                'descripcion': desc,
                'cantidad': int(cant),
                'precio_unitario': float(precio),
                'total': int(cant) * float(precio)
            }
            items.append(item)
        except ValueError as e:
            print(f"Error al procesar el item: {e}")
    return items

def filtro_facturas_por_cliente(organizacion_id,cliente_nombre):
    """Retorna un filtro para buscar facturas por cliente"""
    try:
        factura_data = mongo.db.facturas.find({'organizacion_id': ObjectId(organizacion_id),
                                               'cliente.nombre':{ '$regex':cliente_nombre, '$options':'i' } },)
        facturas = [Factura(
            id=factura_data['_id'],
            organizacion_id=factura_data['organizacion_id'],
            invoice_num=factura_data['invoice_num'],
            vendedor=factura_data['vendedor'],
            cliente=factura_data['cliente'],
            fecha_emision=factura_data['fecha_emision'],
            items=factura_data['items'],
            total=factura_data['total'],)]
        return facturas
    except Exception as e:
        print(f"Error al convertir cliente_nombre a ObjectId: {e}")
        return []