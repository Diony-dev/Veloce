class Producto:
    def __init__(self, id, organizacion_id, nombre, precio, codigo=None, descripcion=None, tipo='Servicio', stock=0):
        self.id = id if id else None
        self.organizacion_id = organizacion_id
        self.nombre = nombre
        self.precio = float(precio) if precio else 0.0
        self.codigo = codigo
        self.descripcion = descripcion
        self.tipo = tipo # 'Servicio' o 'Producto'
        self.stock = int(stock) if stock else 0
        self.activo = True

    def to_dict(self):
        return {
            'organizacion_id': self.organizacion_id,
            'nombre': self.nombre,
            'precio': self.precio,
            'codigo': self.codigo,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'stock': self.stock,
            'activo': self.activo
        }