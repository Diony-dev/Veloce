import datetime


class Cliente:
    def __init__(self, id, nombre, apellido ,correo, telefono, organizacion_id,created_at ,identificacion=None, ):
        self.id = id if id else None
        self.organizacion_id = organizacion_id
        self.nombre = nombre
        self.apellido = apellido
        self.correo = correo
        self.telefono = telefono
        self.created_at = created_at
        self.identificacion = identificacion

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'correo': self.correo,
            'telefono': self.telefono,
            'identificacion': self.identificacion,
        }