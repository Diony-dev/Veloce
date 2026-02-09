class Organizacion:
    def __init__(self, organizacion_id, nombre, direccion, telefono, email, rnc, logo, moneda='RD$'):
        self.organizacion_id = organizacion_id if organizacion_id else None
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.email = email
        self.rnc = rnc
        self.logo = logo if logo else 'default_logo.png'
        self.moneda = moneda

    def to_dict(self):
        return {
            'organizacion_id': self.organizacion_id,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'email': self.email,
            'rnc': self.rnc,
            'logo': self.logo,
            'moneda': self.moneda
        }
