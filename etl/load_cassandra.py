import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connections import get_cassandra_connection
from etl.extractor import extraer_feed_noticias

def cargar_feed_cassandra():
    session = get_cassandra_connection()
    if not session:
        return False

    session.set_keyspace('red_social')

    datos_json = extraer_feed_noticias()
    if not datos_json:
        return False

    datos_dict = json.loads(datos_json)

    query_insert = """
        INSERT INTO feed_noticias 
        (id_publicacion, autor_publicacion, texto_contenido, fecha_publicacion, likes_contador, total_comentarios) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    try:
        for fila in datos_dict:
            session.execute(query_insert, (
                fila['id_publicacion'],
                fila['autor_publicacion'],
                fila['texto_contenido'],
                fila['fecha_publicacion'],
                fila['likes_contador'],
                fila['total_comentarios']
            ))
        print("Carga en Cassandra completada.")
        return True
    except Exception as e:
        print(f"Error insertando en Cassandra: {e}")
        return False

if __name__ == "__main__":
    cargar_feed_cassandra()