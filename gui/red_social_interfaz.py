import sys
import json
import os
import psycopg2

# Asegurar que Python encuentre los módulos de las carpetas database y etl
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QScrollArea,
                             QFrame, QLineEdit, QMessageBox, QStackedWidget, QTabWidget)
from PyQt6.QtCore import Qt

from database.connections import get_postgres_connection
from etl.load_redis import actualizar_cache_redis, obtener_cache_redis
from etl.load_mongo import cargar_feed_mongodb
from etl.load_cassandra import cargar_feed_cassandra


class TarjetaPublicacion(QFrame):
    """Componente visual para renderizar cada publicación del Feed de manera moderna"""

    def __init__(self, datos_post, callback_refrescar, usuario_actual_id):
        super().__init__()
        self.setObjectName("PostCard")
        self.datos = datos_post
        self.callback_refrescar = callback_refrescar
        self.usuario_actual_id = usuario_actual_id
        self.id_publicacion = datos_post.get("id_publicacion")
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(16, 16, 16, 16)

        # Cabecera del Post
        autor = self.datos.get("autor_publicacion", "Usuario")
        fecha = str(self.datos.get("fecha_publicacion", ""))[:10]
        lbl_cabecera = QLabel(f"<b>{autor}</b> <font color='#65676b'>• {fecha}</font>")
        layout_principal.addWidget(lbl_cabecera)

        # Contenido Textual
        lbl_contenido = QLabel(self.datos.get("texto_contenido", ""))
        lbl_contenido.setWordWrap(True)
        lbl_contenido.setStyleSheet("font-size: 15px; margin-top: 5px; margin-bottom: 5px;")
        layout_principal.addWidget(lbl_contenido)

        # Contadores
        self.lbl_contadores = QLabel(
            f"{self.datos.get('likes_contador', 0)} Me gusta   •   {self.datos.get('total_comentarios', 0)} Comentarios")
        self.lbl_contadores.setStyleSheet("color: #65676b; border-bottom: 1px solid #e4e6eb; padding-bottom: 8px;")
        layout_principal.addWidget(self.lbl_contadores)

        # Botones de Acción
        layout_acciones = QHBoxLayout()
        self.btn_like = QPushButton("👍 Me gusta")
        self.btn_comentar = QPushButton("💬 Comentar")
        layout_acciones.addWidget(self.btn_like)
        layout_acciones.addWidget(self.btn_comentar)
        layout_principal.addLayout(layout_acciones)

        # Contenedor de Comentarios (Desplegable)
        self.contenedor_comentarios = QWidget()
        self.layout_comentarios = QVBoxLayout(self.contenedor_comentarios)

        layout_input = QHBoxLayout()
        self.input_comentario = QLineEdit()
        self.input_comentario.setPlaceholderText("Escribe un comentario...")
        self.btn_enviar_comentario = QPushButton("Enviar")
        self.btn_enviar_comentario.setStyleSheet("background-color: #1877f2; color: white;")

        layout_input.addWidget(self.input_comentario)
        layout_input.addWidget(self.btn_enviar_comentario)
        self.layout_comentarios.addLayout(layout_input)

        self.contenedor_comentarios.setVisible(False)
        layout_principal.addWidget(self.contenedor_comentarios)

        # Eventos
        self.btn_like.clicked.connect(self.registrar_like_db)
        self.btn_comentar.clicked.connect(self.conmutar_comentarios)
        self.btn_enviar_comentario.clicked.connect(self.registrar_comentario_db)

    def registrar_like_db(self):
        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE publicaciones SET likes_contador = likes_contador + 1 WHERE id_publicacion = %s;",
                    (self.id_publicacion,))
                conn.commit()
                self.sincronizar_ecosistema()
            finally:
                conn.close()

    def conmutar_comentarios(self):
        visible = self.contenedor_comentarios.isVisible()
        if not visible:
            self.cargar_comentarios_desde_db()
        self.contenedor_comentarios.setVisible(not visible)

    def cargar_comentarios_desde_db(self):
        while self.layout_comentarios.count() > 1:
            widget = self.layout_comentarios.takeAt(1).widget()
            if widget: widget.deleteLater()

        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                               SELECT u.nombre, c.contenido
                               FROM comentarios c
                                        JOIN usuarios u ON c.usuario_id = u.id_usuario
                               WHERE c.publicacion_id = %s
                               ORDER BY c.id_comentario ASC;
                               """, (self.id_publicacion,))

                for nombre, contenido in cursor.fetchall():
                    lbl_item = QLabel(f"<b>{nombre}:</b> {contenido}")
                    lbl_item.setStyleSheet("background-color: #f0f2f5; padding: 8px; border-radius: 12px;")
                    lbl_item.setWordWrap(True)
                    self.layout_comentarios.addWidget(lbl_item)
            finally:
                conn.close()

    def registrar_comentario_db(self):
        texto = self.input_comentario.text().strip()
        if not texto: return
        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(MAX(id_comentario), 0) + 1 FROM comentarios;")
                nuevo_id = cursor.fetchone()[0]
                cursor.execute("""
                               INSERT INTO comentarios (id_comentario, contenido, fecha_comentario, usuario_id,
                                                        publicacion_id)
                               VALUES (%s, %s, NOW(), %s, %s);
                               """, (nuevo_id, texto, self.usuario_actual_id, self.id_publicacion))
                conn.commit()
                self.input_comentario.clear()
                self.sincronizar_ecosistema()
                self.cargar_comentarios_desde_db()
            finally:
                conn.close()

    def sincronizar_ecosistema(self):
        actualizar_cache_redis()
        cargar_feed_mongodb()
        cargar_feed_cassandra()
        self.callback_refrescar()


class RedSocialInteractiva(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CoreFeed - Ecosistema Políglota")
        self.resize(600, 850)
        self.aplicar_estilos()

        self.usuario_actual_id = None
        self.usuario_actual_nombre = None

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.crear_pantalla_login()
        self.crear_pantalla_principal()

    def crear_pantalla_login(self):
        widget_login = QWidget()
        layout = QVBoxLayout(widget_login)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_titulo = QLabel("Iniciar Sesión")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #1877f2; margin-bottom: 20px;")

        self.input_id_login = QLineEdit()
        self.input_id_login.setPlaceholderText("Ingresa tu ID de Usuario (Ej: 1, 14, 25)")
        self.input_id_login.setFixedWidth(260)

        btn_login = QPushButton("Entrar al Feed")
        btn_login.setStyleSheet("background-color: #1877f2; color: white; padding: 10px; font-size: 14px;")
        btn_login.setFixedWidth(260)
        btn_login.clicked.connect(self.procesar_login)

        layout.addWidget(lbl_titulo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.input_id_login, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_login, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stacked_widget.addWidget(widget_login)

    def crear_pantalla_principal(self):
        self.widget_principal = QWidget()
        layout_base = QVBoxLayout(self.widget_principal)
        layout_base.setContentsMargins(12, 12, 12, 12)

        # Mensaje de bienvenida superior
        self.lbl_bienvenida = QLabel("")
        self.lbl_bienvenida.setStyleSheet("font-size: 18px; font-weight: bold; color: #050505; margin-bottom: 5px;")
        layout_base.addWidget(self.lbl_bienvenida)

        # =========================================================================
        # BANDEJA DE AMISTADES SEPARADA POR SECCIONES INDEPENDIENTES
        # =========================================================================
        marco_amistades = QFrame()
        marco_amistades.setObjectName("FriendBox")
        marco_amistades.setStyleSheet(
            "background-color: #ffffff; border-radius: 8px; border: 1px solid #e4e6eb; padding: 8px;")
        layout_amistades = QVBoxLayout(marco_amistades)

        # Formulario para mandar solicitudes ejecutando el Procedure
        layout_enviar = QHBoxLayout()
        self.input_id_amigo = QLineEdit()
        self.input_id_amigo.setPlaceholderText("ID del usuario que quieres agregar...")
        btn_agregar = QPushButton("Enviar Solicitud")
        btn_agregar.setStyleSheet("background-color: #1877f2; color: white;")
        btn_agregar.clicked.connect(self.enviar_solicitud_amistad)
        layout_enviar.addWidget(self.input_id_amigo)
        layout_enviar.addWidget(btn_agregar)
        layout_amistades.addLayout(layout_enviar)

        # Creación del QTabWidget para segmentar la información de las Vistas SQL
        self.tabs_amistades = QTabWidget()

        self.tab_pendientes = QWidget()
        self.tab_enviadas = QWidget()  # Nuevo apartado
        self.tab_amigos = QWidget()

        self.layout_pendientes = QVBoxLayout(self.tab_pendientes)
        self.layout_pendientes.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.layout_enviadas = QVBoxLayout(self.tab_enviadas)  # Layout nuevo apartado
        self.layout_enviadas.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.layout_amigos = QVBoxLayout(self.tab_amigos)
        self.layout_amigos.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.tabs_amistades.addTab(self.tab_pendientes, "Solicitudes Recibidas")
        self.tabs_amistades.addTab(self.tab_enviadas, "Solicitudes Enviadas")  # Pestaña nueva agregada
        self.tabs_amistades.addTab(self.tab_amigos, "Mis Amigos Aceptados")
        layout_amistades.addWidget(self.tabs_amistades)

        layout_base.addWidget(marco_amistades)

        # Área de Scroll del Feed Principal (Consumido desde Redis Caché)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: transparent;")

        self.contenedor_feed = QWidget()
        self.layout_feed = QVBoxLayout(self.contenedor_feed)
        self.layout_feed.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_feed.setSpacing(16)

        self.scroll_area.setWidget(self.contenedor_feed)
        layout_base.addWidget(self.scroll_area)

        self.stacked_widget.addWidget(self.widget_principal)

    def procesar_login(self):
        user_id = self.input_id_login.text().strip()
        if not user_id.isdigit():
            QMessageBox.warning(self, "Error de Validación", "El ID de usuario debe ser numérico.")
            return

        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id_usuario, nombre FROM usuarios WHERE id_usuario = %s;", (user_id,))
                usuario = cursor.fetchone()

                if usuario:
                    self.usuario_actual_id = usuario[0]
                    self.usuario_actual_nombre = usuario[1]
                    self.lbl_bienvenida.setText(f"Bienvenido de nuevo, {self.usuario_actual_nombre}")

                    self.cargar_bandeja_amistades()
                    self.cargar_y_renderizar_feed()
                    self.stacked_widget.setCurrentIndex(1)
                else:
                    QMessageBox.warning(self, "No Encontrado",
                                        "El ID ingresado no corresponde a ningún usuario registrado.")
            finally:
                conn.close()

    def enviar_solicitud_amistad(self):
        id_amigo = self.input_id_amigo.text().strip()
        if not id_amigo.isdigit(): return

        if int(id_amigo) == self.usuario_actual_id:
            QMessageBox.warning(self, "Validación", "No puedes enviarte una solicitud a ti mismo.")
            self.input_id_amigo.clear()
            return

        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Ejecutamos el Stored Procedure preventivo
                cursor.execute("CALL crear_amistad(%s, %s);", (self.usuario_actual_id, int(id_amigo)))
                conn.commit()
                QMessageBox.information(self, "Éxito", "¡Solicitud enviada correctamente!")
                self.input_id_amigo.clear()
                self.sincronizar_ecosistema()
            except psycopg2.Error as e:
                # Captura el RAISE EXCEPTION personalizado disparado desde Postgres
                QMessageBox.warning(self, "Aviso del Sistema", str(e).split('\n')[0])
                conn.rollback()
            finally:
                conn.close()

    def cargar_bandeja_amistades(self):
        self.cargar_solicitudes_pendientes()
        self.cargar_solicitudes_enviadas()  # Llamado al nuevo apartado de renderizado
        self.cargar_lista_amigos()

    def cargar_solicitudes_pendientes(self):
        """Apartado 1: Limpia y renderiza las solicitudes pendientes usando 'vista_solicitudes_pendientes'"""
        while self.layout_pendientes.count() > 0:
            widget = self.layout_pendientes.takeAt(0).widget()
            if widget: widget.deleteLater()

        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Consultamos la vista analítica para las solicitudes destinadas al usuario actual
                cursor.execute("""
                               SELECT id_amistad, usuario_solicitante
                               FROM vista_solicitudes_pendientes
                               WHERE usuario_receptor = %s;
                               """, (self.usuario_actual_nombre,))

                pendientes = cursor.fetchall()
                if not pendientes:
                    self.layout_pendientes.addWidget(QLabel("No tienes solicitudes de amistad pendientes."))
                    return

                for id_amistad, solicitante in pendientes:
                    fila = QHBoxLayout()
                    fila.addWidget(QLabel(f"<b>{solicitante}</b> quiere conectar contigo."))

                    btn_aceptar = QPushButton("Aceptar")
                    btn_aceptar.setStyleSheet("background-color: #31a24c; color: white; padding: 4px 10px;")
                    btn_aceptar.clicked.connect(
                        lambda checked, a_id=id_amistad: self.gestionar_solicitud(a_id, 'ACEPTADA'))

                    btn_rechazar = QPushButton("Rechazar")
                    btn_rechazar.setStyleSheet("background-color: #e41e3f; color: white; padding: 4px 10px;")
                    btn_rechazar.clicked.connect(
                        lambda checked, a_id=id_amistad: self.gestionar_solicitud(a_id, 'RECHAZADA'))

                    fila.addWidget(btn_aceptar)
                    fila.addWidget(btn_rechazar)

                    contenedor_fila = QWidget()
                    contenedor_fila.setLayout(fila)
                    self.layout_pendientes.addWidget(contenedor_fila)
            finally:
                conn.close()

    def cargar_solicitudes_enviadas(self):
        """Apartado Nuevo: Limpia y renderiza las solicitudes que el usuario actual ha mandado a otros y siguen pendientes"""
        while self.layout_enviadas.count() > 0:
            widget = self.layout_enviadas.takeAt(0).widget()
            if widget: widget.deleteLater()

        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Filtramos la vista analítica donde el solicitante es el usuario que inició sesión
                cursor.execute("""
                               SELECT id_amistad, usuario_receptor
                               FROM vista_solicitudes_pendientes
                               WHERE usuario_solicitante = %s;
                               """, (self.usuario_actual_nombre,))

                enviadas = cursor.fetchall()
                if not enviadas:
                    self.layout_enviadas.addWidget(QLabel("No has enviado ninguna solicitud de amistad pendiente."))
                    return

                for id_amistad, receptor in enviadas:
                    fila = QHBoxLayout()
                    fila.addWidget(QLabel(f"Le enviaste una solicitud a <b>{receptor}</b>."))

                    btn_cancelar = QPushButton("Cancelar")
                    btn_cancelar.setStyleSheet("background-color: #e41e3f; color: white; padding: 4px 10px;")
                    # Si se cancela, se elimina el registro pendiente usando la misma función de gestión
                    btn_cancelar.clicked.connect(
                        lambda checked, a_id=id_amistad: self.gestionar_solicitud(a_id, 'CANCELADA'))

                    fila.addWidget(btn_cancelar)

                    contenedor_fila = QWidget()
                    contenedor_fila.setLayout(fila)
                    self.layout_enviadas.addWidget(contenedor_fila)
            finally:
                conn.close()

    def cargar_lista_amigos(self):
        """Apartado 2: Limpia y renderiza las solicitudes consolidadas usando 'vista_amistades_consolidadas'"""
        while self.layout_amigos.count() > 0:
            widget = self.layout_amigos.takeAt(0).widget()
            if widget: widget.deleteLater()

        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Consultamos la vista analítica donde el usuario actual forma parte (ya sea como u1 o u2)
                cursor.execute("""
                               SELECT usuario_1, usuario_2
                               FROM vista_amistades_consolidadas
                               WHERE usuario_1 = %s
                                  OR usuario_2 = %s;
                               """, (self.usuario_actual_nombre, self.usuario_actual_nombre))

                amigos = cursor.fetchall()
                if not amigos:
                    self.layout_amigos.addWidget(
                        QLabel("Tu lista de amigos está vacía. ¡Agrega usuarios mediante su ID!"))
                    return

                for u1, u2 in amigos:
                    # Determinamos el nombre del amigo saltando nuestro propio nombre
                    nombre_amigo = u2 if u1 == self.usuario_actual_nombre else u1
                    lbl_amigo = QLabel(f"👤 {nombre_amigo}")
                    lbl_amigo.setStyleSheet(
                        "font-size: 13px; padding: 4px; background-color: #f0f2f5; margin-bottom: 2px; border-radius: 4px;")
                    self.layout_amigos.addWidget(lbl_amigo)
            finally:
                conn.close()

    def gestionar_solicitud(self, id_amistad, accion):
        conn = get_postgres_connection()
        if conn:
            try:
                cursor = conn.cursor()
                if accion == 'ACEPTADA':
                    cursor.execute("UPDATE amistades SET estado = 'ACEPTADA' WHERE id_amistad = %s;", (id_amistad,))
                    msj = "¡Solicitud aceptada!"
                elif accion == 'CANCELADA':
                    cursor.execute("DELETE FROM amistades WHERE id_amistad = %s;", (id_amistad,))
                    msj = "Solicitud de amistad cancelada."
                else:
                    cursor.execute("DELETE FROM amistades WHERE id_amistad = %s;", (id_amistad,))
                    msj = "Solicitud rechazada correctamente."

                conn.commit()
                QMessageBox.information(self, "Bandeja de Entrada", msj)
                self.sincronizar_ecosistema()
            finally:
                conn.close()

    def cargar_y_renderizar_feed(self):
        while self.layout_feed.count() > 0:
            widget = self.layout_feed.takeAt(0).widget()
            if widget: widget.deleteLater()

        datos_json = obtener_cache_redis()
        if not datos_json:
            lbl_error = QLabel("La caché de Redis está inactiva o vacía.")
            self.layout_feed.addWidget(lbl_error)
            return

        posts = json.loads(datos_json)
        for post in posts:
            tarjeta = TarjetaPublicacion(post, self.cargar_y_renderizar_feed, self.usuario_actual_id)
            self.layout_feed.addWidget(tarjeta)

    def sincronizar_ecosistema(self):
        """Pipeline que orquesta el refresco en cascada de los motores relacionales y NoSQL"""
        actualizar_cache_redis()
        cargar_feed_mongodb()
        cargar_feed_cassandra()
        # Refrescar los elementos de la interfaz en caliente
        self.cargar_bandeja_amistades()
        self.cargar_y_renderizar_feed()

    def aplicar_estilos(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f2f5; }
            QLineEdit { border: 1px solid #ccd0d5; border-radius: 6px; padding: 6px; background-color: #f0f2f5; }
            QLineEdit:focus { border: 1px solid #1877f2; }
            QPushButton { border-radius: 6px; padding: 6px 12px; font-weight: bold; }
            QTabWidget::pane { border: 1px solid #e4e6eb; background: white; border-radius: 4px; }
            QTabBar::tab { background: #f2f3f5; border: 1px solid #e4e6eb; padding: 6px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: white; border-bottom-color: white; font-weight: bold; color: #1877f2; }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RedSocialInteractiva()
    ventana.show()
    sys.exit(app.exec())