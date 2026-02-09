from app.database import mongo
from app.models.producto import Producto
from bson.objectid import ObjectId
import math
import re

def create_producto(organizacion_id, nombre, precio, codigo=None, descripcion=None, tipo='Servicio', stock=0):
    try:
        if not codigo:
            codigo = generate_next_sku(organizacion_id)

        nuevo_producto = Producto(
            id=None,
            organizacion_id=organizacion_id,
            nombre=nombre,
            precio=precio,
            codigo=codigo,
            descripcion=descripcion,
            tipo=tipo,
            stock=stock
        )
        result = mongo.db.productos.insert_one(nuevo_producto.to_dict())
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error creating product: {e}")
        return None

def generate_next_sku(organizacion_id):
    """Genera un SKU secuencial automático (ej. PROD-00001) para la organización."""
    try:
        # Buscar el último producto creado con un SKU automático (que empiece por PROD-)
        last_prod = mongo.db.productos.find_one(
            {
                "organizacion_id": ObjectId(organizacion_id),
                "codigo": {"$regex": "^PROD-"}
            },
            sort=[("_id", -1)]
        )
        
        if last_prod and 'codigo' in last_prod:
            # Extraer el número
            last_code = last_prod['codigo']
            try:
                # Asumimos formato PROD-XXXXX
                number_part = int(last_code.split('-')[1])
                new_number = number_part + 1
            except (IndexError, ValueError):
                new_number = 1
        else:
            new_number = 1
            
        return f"PROD-{str(new_number).zfill(5)}"
    except Exception as e:
        print(f"Error generating SKU: {e}")
        import uuid
        return f"PROD-{uuid.uuid4().hex[:6].upper()}"

def get_producto_by_id(producto_id):
    try:
        data = mongo.db.productos.find_one({"_id": ObjectId(producto_id)})
        if data:
            return Producto(
                id=str(data['_id']),
                organizacion_id=data['organizacion_id'],
                nombre=data['nombre'],
                precio=data['precio'],
                codigo=data.get('codigo'),
                descripcion=data.get('descripcion'),
                tipo=data.get('tipo', 'Servicio'),
                stock=data.get('stock', 0)
            )
        return None
    except Exception as e:
        print(f"Error getting product: {e}")
        return None

def list_productos_by_organizacion(organizacion_id, page=1, per_page=10, search=None):
    try:
        query = {"organizacion_id": ObjectId(organizacion_id), "activo": True}
        
        if search:
            # Búsqueda por nombre o código (case insensitive)
            regex = re.compile(search, re.IGNORECASE)
            query["$or"] = [
                {"nombre": {"$regex": regex}},
                {"codigo": {"$regex": regex}}
            ]

        total_productos = mongo.db.productos.count_documents(query)
        total_pages = math.ceil(total_productos / per_page)
        
        skip = (page - 1) * per_page
        cursor = mongo.db.productos.find(query).skip(skip).limit(per_page)
        
        productos = []
        for data in cursor:
            productos.append(Producto(
                id=str(data['_id']),
                organizacion_id=data['organizacion_id'],
                nombre=data['nombre'],
                precio=data['precio'],
                codigo=data.get('codigo'),
                descripcion=data.get('descripcion'),
                tipo=data.get('tipo', 'Servicio'),
                stock=data.get('stock', 0)
            ))
            
        pagination = {
            'page': page,
            'pages': total_pages,
            'total': total_productos,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1,
            'next_num': page + 1
        }
        
        return productos, pagination
    except Exception as e:
        print(f"Error listing products: {e}")
        return [], None

def update_producto(producto_id, data):
    try:
        # Filtrar campos vacíos o nulos si es necesario, pero aquí asumimos que data trae lo que se va a cambiar
        # Asegurar tipos
        if 'precio' in data:
            data['precio'] = float(data['precio'])
        if 'stock' in data:
            data['stock'] = int(data['stock'])
            
        mongo.db.productos.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": data}
        )
        return True
    except Exception as e:
        print(f"Error updating product: {e}")
        return False

def delete_producto(producto_id):
    try:
        # Soft delete
        mongo.db.productos.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": {"activo": False}}
        )
        return True
    except Exception as e:
        print(f"Error deleting product: {e}")
        return False

def search_productos_by_nombre_codigo(organizacion_id, query_str):
    try:
        query = {
            "organizacion_id": ObjectId(organizacion_id),
            "activo": True
        }
        
        if query_str:
            regex = re.compile(query_str, re.IGNORECASE)
            query["$or"] = [
                {"nombre": {"$regex": regex}},
                {"codigo": {"$regex": regex}}
            ]
            
        cursor = mongo.db.productos.find(query).limit(10)
        
        productos = []
        for data in cursor:
            productos.append(Producto(
                id=str(data['_id']),
                organizacion_id=data['organizacion_id'],
                nombre=data['nombre'],
                precio=data['precio'],
                codigo=data.get('codigo'),
                descripcion=data.get('descripcion'),
                tipo=data.get('tipo', 'Servicio'),
                stock=data.get('stock', 0)
            ))
        return productos
    except Exception as e:
        print(f"Error searching products: {e}")
        return []

def check_stock_availability(producto_id, cantidad_requerida):
    """
    Verifica si hay SUFICIENTE stock para una cantidad requerida.
    Retorna (True, None) si todo OK.
    Retorna (False, mensaje_error) si no alcanza.
    """
    try:
        if not producto_id or len(str(producto_id)) != 24:
            return True, None # Si no es un ID válido, asumimos que es ítem manual sin stock
            
        prod = mongo.db.productos.find_one({"_id": ObjectId(producto_id)})
        if not prod:
            return True, None # Producto no existe, quizás borrado, pase
            
        # Si es servicio, no validamos stock
        if prod.get('tipo') == 'Servicio':
            return True, None
            
        current_stock = int(prod.get('stock', 0))
        if current_stock < cantidad_requerida:
            return False, f"Stock insuficiente para '{prod['nombre']}' (Stock: {current_stock}, Solicitado: {cantidad_requerida})"
            
        return True, None
    except Exception as e:
        print(f"Error checking stock: {e}")
        # En caso de error, bloqueamos por seguridad
        return False, "Error verificando inventario"

def get_producto_by_sku(organizacion_id, sku):
    """Busca un producto por su código SKU."""
    try:
        data = mongo.db.productos.find_one({
            "organizacion_id": ObjectId(organizacion_id),
            "codigo": sku
        })
        if data:
            return Producto(
                id=str(data['_id']),
                organizacion_id=data['organizacion_id'],
                nombre=data['nombre'],
                precio=data['precio'],
                codigo=data.get('codigo'),
                descripcion=data.get('descripcion'),
                tipo=data.get('tipo', 'Servicio'),
                stock=data.get('stock', 0)
            )
        return None
    except Exception as e:
        print(f"Error finding product by SKU: {e}")
        return None

def decrease_stock(producto_id, quantity):
    """Disminuye el stock de un producto si es de tipo 'Producto'."""
    try:
        # Primero verificamos si es un producto físico
        prod_data = mongo.db.productos.find_one({"_id": ObjectId(producto_id)})
        if not prod_data:
            return False
            
        is_service = prod_data.get('tipo') == 'Servicio'
        
        if not is_service:
            # Atomic update decrinsing stock
            mongo.db.productos.update_one(
                {"_id": ObjectId(producto_id)},
                {"$inc": {"stock": -int(quantity)}}
            )
            return True
        return True # Si es servicio no hacemos nada pero retornamos éxito
    except Exception as e:
        print(f"Error decreasing stock: {e}")
        return False
