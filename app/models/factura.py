# En app/models/factura.py

class Factura:
    def __init__(self, id, organizacion_id, invoice_num, vendedor, cliente, fecha_emision, items, total, estado, forma_pago, ):
        self.id = id if id else None
        self.organizacion_id = organizacion_id
        self.invoice_num = invoice_num
        self.vendedor = vendedor
        self.fecha_emision = fecha_emision
        self.items = items
        self.total = total
        self.estado = estado if estado else 'pendiente'
        self.forma_pago = forma_pago if forma_pago else 'efectivo'

        # --- LÓGICA DEFENSIVA MEJORADA ---

        if not cliente:
            # Caso 1: No se proporcionó cliente
            self.cliente_id = None
            self.cliente = None

        elif isinstance(cliente, dict):
            # Caso 2: El cliente es un DICCI (cargado desde MongoDB)
            # Esto es lo normal.
            self.cliente = cliente
            # Usamos .get() para evitar errores si falta la clave 'id'
            self.cliente_id = cliente.get('id') 

        elif hasattr(cliente, 'id'):
            # Caso 3: El cliente es un OBJETO (al crear una nueva factura)
            # (Ej. un objeto de la clase Cliente)
            self.cliente_id = cliente.id
            self.cliente = {
                'nombre': cliente.nombre,
                'apellido': cliente.apellido,
                'id': cliente.id,
                'correo': cliente.correo,
                'telefono': cliente.telefono,
                'identificacion': cliente.identificacion
            }
        
        elif isinstance(cliente, str):
            # Caso 4: DATO INCORRECTO (el 'cliente' es un string)
            # ESTO ES LO QUE CAUSA TU ERROR. 
            # Lo manejamos elegantemente.
            self.cliente_id = None # No podemos saber el ID
            self.cliente = {
                'nombre': cliente, # Guardamos el string como el nombre
                'apellido': '(Dato antiguo)', # Indicamos que es dato antiguo
                'id': None
                # Rellenamos el resto para que la plantilla no falle
            }
        
        else:
            # Otro caso inesperado
            self.cliente_id = None
            self.cliente = {'nombre': 'Error de datos'}