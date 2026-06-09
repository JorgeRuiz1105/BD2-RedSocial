import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connections import get_cassandra_connection


def setup_cassandra():
    session = get_cassandra_connection()
    if not session:
        return

    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS red_social 
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
    """)

    session.set_keyspace('red_social')

    session.execute("""
                    CREATE TABLE IF NOT EXISTS feed_noticias
                    (
                        id_publicacion
                        int
                        PRIMARY
                        KEY,
                        autor_publicacion
                        text,
                        texto_contenido
                        text,
                        fecha_publicacion
                        text,
                        likes_contador
                        int,
                        total_comentarios
                        int
                    )
                    """)
    print("Esquema de Cassandra configurado.")


if __name__ == "__main__":
    setup_cassandra()