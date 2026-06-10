import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connections import (
    get_postgres_connection,
    get_mongo_connection,
    get_cassandra_connection,
    get_redis_connection
)


def realizar_benchmark():
    print("Iniciando prueba de rendimiento de consultas (Benchmarking)...\n")
    print("Consulta a probar: Obtener el Feed de Noticias completo (Datos + Autores + Conteo de Likes/Comentarios)\n")

    resultados = {}

    # 1. PostgreSQL
    try:
        conn_pg = get_postgres_connection()
        if conn_pg is not None:
            inicio = time.time()
            cursor = conn_pg.cursor()
            cursor.execute("SELECT * FROM vista_feed_noticias;")
            _ = cursor.fetchall()
            fin = time.time()
            resultados['PostgreSQL'] = (fin - inicio) * 1000  # Convertir a milisegundos
            conn_pg.close()
    except Exception as e:
        print(f"Error en PostgreSQL: {e}")

    # 2. MongoDB
    try:
        mongo_client = get_mongo_connection()
        if mongo_client is not None:
            db = mongo_client["red_social_db"]
            coleccion = db["feed_noticias"]
            inicio = time.time()
            _ = list(coleccion.find({}))
            fin = time.time()
            resultados['MongoDB'] = (fin - inicio) * 1000
    except Exception as e:
        print(f"Error en MongoDB: {e}")

    # 3. Cassandra
    try:
        cass_session = get_cassandra_connection()
        if cass_session is not None:
            inicio = time.time()
            _ = list(cass_session.execute("SELECT * FROM red_social.feed_noticias;"))
            fin = time.time()
            resultados['Cassandra'] = (fin - inicio) * 1000
    except Exception as e:
        print(f"Error en Cassandra: {e}")

    # 4. Redis
    try:
        redis_client = get_redis_connection()
        if redis_client is not None:
            inicio = time.time()
            _ = redis_client.get("cache_feed_noticias")
            fin = time.time()
            resultados['Redis'] = (fin - inicio) * 1000
    except Exception as e:
        print(f"Error en Redis: {e}")

    if resultados:
        print("-" * 50)
        print("=== RESULTADOS DEL BENCHMARK (Milisegundos) ===")
        print("-" * 50)

        # Ordenamos el diccionario por los valores (milisegundos)
        for db, ms in sorted(resultados.items(), key=lambda item: item[1]):
            print(f"| {db:12} | {ms:10.4f} ms |")
        print("-" * 50)
    else:
        print("No se pudieron obtener resultados. Revisa las conexiones.")


if __name__ == "__main__":
    realizar_benchmark()