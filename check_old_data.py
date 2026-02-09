from app import create_app, mongo
import json

app = create_app()

with app.app_context():
    # Buscar facturas que contengan "Dato antiguo" en el campo apellido del cliente
    query = {"cliente.apellido": "(Dato antiguo)"}
    count = mongo.db.facturas.count_documents(query)
    print(f"Facturas con '(Dato antiguo)': {count}")
    
    if count > 0:
        ejemplo = mongo.db.facturas.find_one(query)
        print("Ejemplo:", ejemplo.get('cliente'))
