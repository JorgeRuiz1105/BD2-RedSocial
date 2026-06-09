import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connections import get_postgres_connection


def poblar_base_datos_desde_excel(ruta_archivo):
    conn = get_postgres_connection()
    if not conn:
        return

    if not os.path.exists(ruta_archivo):
        print(f"Archivo no encontrado: {ruta_archivo}")
        return

    cursor = conn.cursor()

    queries = {
        "Usuarios": """
                    INSERT INTO usuarios (id_usuario, nombre, email, fecha_registro, pais)
                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id_usuario) DO NOTHING;
                    """,
        "Publicaciones": """
                         INSERT INTO publicaciones (id_publicacion, texto_contenido, fecha_publicacion, likes_contador,
                                                    autor_id)
                         VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id_publicacion) DO NOTHING;
                         """,
        "Comentarios": """
                       INSERT INTO comentarios (id_comentario, contenido, fecha_comentario, usuario_id, publicacion_id)
                       VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id_comentario) DO NOTHING;
                       """,
        "Amistades": """
                     INSERT INTO amistades (id_amistad, fecha_amistad, estado, usuario_solicitante_id,
                                            usuario_receptor_id)
                     VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id_amistad) DO NOTHING;
                     """
    }

    try:
        excel_data = pd.read_excel(ruta_archivo, sheet_name=None)
        orden_hojas = ["Usuarios", "Publicaciones", "Comentarios", "Amistades"]

        # Estructuras para guardar los IDs válidos y filtrar datos huérfanos
        usuarios_validos = set()
        publicaciones_validas = set()

        for hoja in orden_hojas:
            if hoja in excel_data:
                df = excel_data[hoja]
                df = df.where(pd.notnull(df), None)

                filas_insertadas = 0
                filas_omitidas = 0

                for _, fila in df.iterrows():
                    # Lógica de validación (Data Cleaning)
                    if hoja == "Usuarios":
                        usuarios_validos.add(fila['id_usuario'])

                    elif hoja == "Publicaciones":
                        if fila['autor_id'] not in usuarios_validos:
                            filas_omitidas += 1
                            continue  # Saltamos la fila huérfana
                        publicaciones_validas.add(fila['id_publicacion'])

                    elif hoja == "Comentarios":
                        if fila['usuario_id'] not in usuarios_validos or fila[
                            'publicacion_id'] not in publicaciones_validas:
                            filas_omitidas += 1
                            continue

                    elif hoja == "Amistades":
                        if fila['usuario_solicitante_id'] not in usuarios_validos or fila[
                            'usuario_receptor_id'] not in usuarios_validos:
                            filas_omitidas += 1
                            continue

                    # Si pasa las validaciones, ejecutamos el insert
                    cursor.execute(queries[hoja], tuple(fila))
                    filas_insertadas += 1

                print(f"Hoja '{hoja}': {filas_insertadas} insertadas, {filas_omitidas} omitidas (datos sucios).")
            else:
                print(f"Advertencia: La hoja '{hoja}' no existe en el archivo Excel.")

        conn.commit()
        print("Migración de Excel a PostgreSQL completada con éxito.")

    except Exception as e:
        conn.rollback()
        print(f"Error en la transacción: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_excel = os.path.join(base_dir, "data", "datos.xlsx")
    poblar_base_datos_desde_excel(ruta_excel)