from datetime import datetime

class Gasto:
    def __init__(self, id, organizacion_id, descripcion, monto, categoria, fecha, proveedor=None, comprobante=None, registrado_por=None):
        self.id = id if id else None
        self.organizacion_id = organizacion_id
        
        self.descripcion = descripcion  # Ej: "Pago de Internet"
        self.monto = float(monto) if monto else 0.0
        
        # Categorías sugeridas: "Servicios", "Nómina", "Alquiler", "Insumos", "Impuestos", "Otros"
        self.categoria = categoria      
        
        # Manejo robusto de fechas
        if isinstance(fecha, str):
            try:
                # Intenta formato fecha YYYY-MM-DD
                self.fecha = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                self.fecha = datetime.now()
        else:
            self.fecha = fecha if fecha else datetime.now()
            
        self.proveedor = proveedor      # Ej: "Claro", "Edeeste"
        self.comprobante = comprobante  # URL o número de referencia
        self.registrado_por = registrado_por # Usuario que registró

    def to_dict(self):
        return {
            'id': self.id,
            'organizacion_id': self.organizacion_id,
            'descripcion': self.descripcion,
            'monto': self.monto,
            'categoria': self.categoria,
            'fecha': self.fecha,
            'proveedor': self.proveedor,
            'comprobante': self.comprobante,
            'registrado_por': self.registrado_por
        }