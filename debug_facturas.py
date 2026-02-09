from app import create_app, mongo
from bson import ObjectId

app = create_app()

with app.app_context():
    # Obtener una factura reciente
    factura = mongo.db.facturas.find_one()
    print("--- DOCUMENTO FACTURA ---")
    print(factura)
    if factura:
        print("\nTIPO DE CAMPO 'cliente':", type(factura.get('cliente')))
