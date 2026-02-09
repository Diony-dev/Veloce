from flask_login import UserMixin


class Usuario(UserMixin):
    def __init__(self, id, organizacion_id, nombre, correo, contraseña, rol, departamento, foto):
        self.id = id if id else None
        self.organizacion_id = organizacion_id
        self.nombre = nombre
        self.correo = correo
        self.contraseña = contraseña
        self.rol = rol
        self.departamento = departamento
        self.foto = foto if foto else 'default.jpg'
        
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'correo': self.correo,
            'contraseña': self.contraseña,
            'rol': self.rol,
            'departamento': self.departamento,
            'foto': self.foto,
            'organizacion_id': self.organizacion_id
        }
    def is_admin(self):
        return self.rol == 'admin'