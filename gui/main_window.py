import sys
import json
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView)

from etl.load_excel import poblar_base_datos_desde_excel
from etl.load_mongo import cargar_feed_mongodb
from etl.load_cassandra import cargar_feed_cassandra
from etl.load_redis import actualizar_cache_redis, obtener_cache_redis


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestor Políglota - Red Social")
        self.resize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.btn_cargar_pg = QPushButton("1. Cargar Datos Excel a PostgreSQL")
        self.btn_ejecutar_etl = QPushButton("2. Ejecutar ETL (Mongo, Cassandra, Redis)")
        self.btn_ver_feed = QPushButton("3. Cargar Feed desde Redis")

        self.tabla_feed = QTableWidget()
        self.tabla_feed.setColumnCount(6)
        self.tabla_feed.setHorizontalHeaderLabels([
            "ID", "Autor", "Contenido", "Fecha", "Likes", "Comentarios"
        ])
        self.tabla_feed.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.layout.addWidget(self.btn_cargar_pg)
        self.layout.addWidget(self.btn_ejecutar_etl)
        self.layout.addWidget(self.btn_ver_feed)
        self.layout.addWidget(self.tabla_feed)

        self.btn_cargar_pg.clicked.connect(self.cargar_postgres)
        self.btn_ejecutar_etl.clicked.connect(self.ejecutar_etl_completo)
        self.btn_ver_feed.clicked.connect(self.mostrar_feed_redis)

    def cargar_postgres(self):
        # Obtenemos la ruta absoluta desde la raíz del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Construimos la ruta exacta al archivo Excel
        ruta_excel = os.path.join(base_dir, "data", "datos.xlsx")

        try:
            poblar_base_datos_desde_excel(ruta_excel)
            QMessageBox.information(self, "Éxito", "Datos cargados en PostgreSQL correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al cargar PostgreSQL: {str(e)}")

    def ejecutar_etl_completo(self):
        try:
            mongo_ok = cargar_feed_mongodb()
            cass_ok = cargar_feed_cassandra()
            redis_ok = actualizar_cache_redis()

            if mongo_ok and cass_ok and redis_ok:
                QMessageBox.information(self, "Éxito", "Proceso ETL ejecutado hacia Mongo, Cassandra y Redis.")
            else:
                QMessageBox.warning(self, "Advertencia",
                                    "El ETL finalizó, pero algunos destinos fallaron. Revisa la consola.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo en el proceso ETL: {str(e)}")

    def mostrar_feed_redis(self):
        datos_json = obtener_cache_redis()
        if not datos_json:
            QMessageBox.warning(self, "Sin Datos", "La caché de Redis está vacía. Ejecuta el ETL primero.")
            return

        datos = json.loads(datos_json)
        self.tabla_feed.setRowCount(len(datos))

        for row_idx, fila in enumerate(datos):
            self.tabla_feed.setItem(row_idx, 0, QTableWidgetItem(str(fila.get("id_publicacion", ""))))
            self.tabla_feed.setItem(row_idx, 1, QTableWidgetItem(str(fila.get("autor_publicacion", ""))))
            self.tabla_feed.setItem(row_idx, 2, QTableWidgetItem(str(fila.get("texto_contenido", ""))))
            self.tabla_feed.setItem(row_idx, 3, QTableWidgetItem(str(fila.get("fecha_publicacion", ""))))
            self.tabla_feed.setItem(row_idx, 4, QTableWidgetItem(str(fila.get("likes_contador", ""))))
            self.tabla_feed.setItem(row_idx, 5, QTableWidgetItem(str(fila.get("total_comentarios", ""))))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())