import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connections import get_redis_connection
from etl.extractor import extraer_feed_noticias

def actualizar_cache_redis():
    r = get_redis_connection()
    if not r:
        return False

    datos_json = extraer_feed_noticias()
    if not datos_json:
        return False

    try:
        # Guardamos el JSON completo con una llave.
        # setex (llave, tiempo_vida_segundos, valor)
        # 3600 segundos = 1 hora de caché
        r.setex('cache_feed_noticias', 3600, datos_json)
        print("Caché de Redis actualizada correctamente.")
        return True
    except Exception as e:
        print(f"Error guardando en Redis: {e}")
        return False

def obtener_cache_redis():
    r = get_redis_connection()
    if not r:
        return None

    try:
        datos_cacheados = r.get('cache_feed_noticias')
        if datos_cacheados:
            print("Datos obtenidos desde la caché de Redis.")
            return datos_cacheados
        else:
            print("Caché vacía o expirada.")
            return None
    except Exception as e:
        print(f"Error leyendo de Redis: {e}")
        return None

if __name__ == "__main__":
    actualizar_cache_redis()
    obtener_cache_redis()