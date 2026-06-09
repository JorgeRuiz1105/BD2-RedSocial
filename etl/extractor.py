import json
import sys
import os

# Agregamos la ruta principal para que encuentre la carpeta database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connections import get_postgres_connection
from psycopg2.extras import RealDictCursor


def extraer_feed_noticias():
    """Extrae la vista del feed de noticias, la devuelve como JSON y la guarda en un archivo"""
    conn = get_postgres_connection()
    if not conn:
        return None

    cursor = None
    try:
        # Usamos RealDictCursor para que el resultado sea un diccionario
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM vista_feed_noticias;")
        filas = cursor.fetchall()

        # Convertimos las fechas a string para que sean compatibles con JSON
        for fila in filas:
            if 'fecha_publicacion' in fila and fila['fecha_publicacion']:
                fila['fecha_publicacion'] = fila['fecha_publicacion'].isoformat()

        # Convertimos a string JSON formateado
        feed_json = json.dumps(filas, indent=4, ensure_ascii=False)

        # Lógica nueva: Guardar el archivo físico en la carpeta data
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruta_json = os.path.join(base_dir, "data", "feed_noticias_export.json")

        with open(ruta_json, 'w', encoding='utf-8') as f:
            f.write(feed_json)

        print(f"Archivo JSON guardado físicamente en: {ruta_json}")

        return feed_json

    except Exception as e:
        print(f"Error en la extracción: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Bloque de prueba
if __name__ == "__main__":
    print("Extrayendo Feed de Noticias de PostgreSQL...")
    datos_json = extraer_feed_noticias()
    if datos_json:
        print("¡Éxito! La extracción y guardado finalizaron correctamente.")
    else:
        print("No se obtuvieron datos.")