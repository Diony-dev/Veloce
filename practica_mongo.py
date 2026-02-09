import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from pprint import pprint
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configuración de la conexión
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    print("Error: No se encontró MONGO_URI en el archivo .env")
    exit(1)

try:
    client = MongoClient(MONGO_URI)
    # Si el URI incluye el nombre de la base de datos, get_database() lo usará.
    # Si no, puedes especificarlo: client['nombre_de_tu_db']
    db = client.get_database() 
    print(f"Conectado exitosamente a la base de datos: {db.name}")
except Exception as e:
    print(f"Error de conexión: {e}")
    exit(1)

def ejecutar_pipeline(coleccion, pipeline):
    """
    Ejecuta un pipeline de agregación en una colección específica y muestra los resultados.
    """
    print(f"\n--- Ejecutando pipeline en '{coleccion}' ---")
    try:
        resultados = list(db[coleccion].aggregate(pipeline))
        
        if not resultados:
            print("No se encontraron resultados.")
        else:
            print(f"Se encontraron {len(resultados)} documentos:")
            for i, doc in enumerate(resultados, 1):
                print(f"\nResultado #{i}:")
                pprint(doc)
    except Exception as e:
        print(f"Error al ejecutar el pipeline: {e}")

# --- ZONA DE PRUEBAS ---

if __name__ == "__main__":
    print("Script de práctica de Agregaciones MongoDB iniciado.")
    
    # ---------------------------------------------------------
    # EJEMPLO 1: Agrupar facturas por estado y sumar totales
    # ---------------------------------------------------------
    pipeline_ejemplo = [
        {


            "$group": {
                "_id": "$estado",
                "cantidad_facturas": {"$sum": 1},
                "total_vendido": {"$sum": "$total"}
            }
        },
        {
            "$sort": {"total_vendido": -1}
        }
    ]
    
    # Para ejecutar, descomenta la línea de abajo:
    # ejecutar_pipeline('facturas', pipeline_ejemplo)


    # ---------------------------------------------------------
    # EJEMPLO 2: Filtrar facturas de un cliente específico (usando regex)
    # ---------------------------------------------------------
    pipeline_busqueda = [
        {
            "$match": {
                "cliente.nombre": {"$regex": "Juan", "$options": "i"}
            }
        },
        {
            "$project": {
                "invoice_num": 1,
                "cliente.nombre": 1,
                "total": 1,
                "fecha_emision": 1
            }
        },
        {
            "$limit": 5
        }
    ]
    
    # ejecutar_pipeline('facturas', pipeline_busqueda)

    
    # ---------------------------------------------------------
    # ESPACIO PARA TUS PRUEBAS
    # Escribe tu pipeline aquí y llama a ejecutar_pipeline()
    # ---------------------------------------------------------
    
    # mi_pipeline = [ ... ]
    # ejecutar_pipeline('nombre_coleccion', mi_pipeline)
ejecutar_pipeline('facturas', pipeline_ejemplo) 

