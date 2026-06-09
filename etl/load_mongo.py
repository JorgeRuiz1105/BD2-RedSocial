import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connections import get_mongo_connection
from etl.extractor import extraer_feed_noticias


def cargar_feed_mongodb():
    db = get_mongo_connection()
    if db is None:
        return False

    datos_json = extraer_feed_noticias()
    if not datos_json:
        return False

    datos_dict = json.loads(datos_json)
    coleccion = db["feed_noticias"]

    coleccion.delete_many({})

    if datos_dict:
        coleccion.insert_many(datos_dict)
        print("Carga en MongoDB completada.")
        return True

    return False

if __name__ == "__main__":
    cargar_feed_mongodb()