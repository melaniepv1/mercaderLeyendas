from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QSlider, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QDialog, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsEllipseItem, QScrollArea, QSpinBox, QProgressDialog, QListWidget, QListWidgetItem, QInputDialog)
from PyQt5.QtGui import QPixmap, QBrush, QColor, QPen
from PyQt5.QtCore import Qt, QTimer
import sys
import math
import psycopg2
import os

conn = psycopg2.connect(
    dbname="mercaderleyendas",
    user="postgres",
    password="1234",
    host="localhost",
    port="5433"
)
cursor = conn.cursor()



# ---------------------- VENTANA PRINCIPAL DEL JUEGO ----------------------
class GameWindow(QWidget):
    def __init__(self, id_partida, nombre_personaje, ciudad_inicio, producto_elegido):
        super().__init__()
        self.setWindowTitle("Mercader de Leyendas - Partida en curso")
        self.setFixedSize(500, 300)
        
        layout = QVBoxLayout()

        label_titulo = QLabel(f"Bienvenido, {nombre_personaje}")
        label_titulo.setStyleSheet("font: bold 16pt; color: #335;")
        layout.addWidget(label_titulo)

        layout.addWidget(QLabel(f"Ciudad de inicio: {ciudad_inicio}"))
        layout.addWidget(QLabel(f"Producto elegido: {producto_elegido}"))

        self.setLayout(layout)


# ---------------------- PRECONFIGURACIÓN ----------------------
class PreconfigWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preconfiguración")
        self.setFixedSize(400, 400)
        self.config = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        titulo = QLabel("Preconfiguración:")
        titulo.setStyleSheet("font: bold 16pt Georgia; color: #bfb563;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        self.input_nombre_jugador = QLineEdit()
        layout.addWidget(QLabel("Nombre de usuario del jugador:"))
        layout.addWidget(self.input_nombre_jugador)

        semana_layout = QHBoxLayout()
        semana_label = QLabel("1 semana:")
        self.combo_semana = QComboBox()
        self.combo_semana.addItems(["1 segundo", "2 segundos", "5 segundos", "10 segundos"])
        self.combo_semana.setCurrentIndex(1)
        semana_layout.addWidget(semana_label)
        semana_layout.addWidget(self.combo_semana)
        layout.addLayout(semana_layout)

        self.slider_oro = self.crear_slider("Monedas de oro")
        self.slider_vasijas = self.crear_slider("Vasijas")
        self.slider_camellos = self.crear_slider("Camellos")
        layout.addLayout(self.slider_oro["layout"])
        layout.addLayout(self.slider_vasijas["layout"])
        layout.addLayout(self.slider_camellos["layout"])

        botones_layout = QHBoxLayout()
        btn_salir = QPushButton("Salir")
        btn_salir.clicked.connect(self.close)
        btn_salir.setStyleSheet(self.estilo_boton())

        btn_iniciar = QPushButton("Iniciar")
        btn_iniciar.clicked.connect(self.procesar_jugador)
        btn_iniciar.setStyleSheet(self.estilo_boton())

        botones_layout.addWidget(btn_salir)
        botones_layout.addWidget(btn_iniciar)
        layout.addLayout(botones_layout)

        self.setLayout(layout)

# Sliders configurables para recursos iniciales

    def crear_slider(self, etiqueta):
        layout = QVBoxLayout()
        label = QLabel(f"{etiqueta}: 0")
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(500)
        slider.valueChanged.connect(lambda value: label.setText(f"{etiqueta}: {value}"))
        layout.addWidget(label)
        layout.addWidget(slider)
        return {"layout": layout, "slider": slider}

    def estilo_boton(self):
        return """
        QPushButton {
            background-color: #c6b26b;
            color: white;
            font-weight: bold;
            font-size: 12px;
            padding: 5px 15px;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #e6d47f;
        }
        """

# En vez de guardar directamente, primero se intenta recuperar o crear nuevo jugador

    def procesar_jugador(self):
        nombre_jugador = self.input_nombre_jugador.text().strip()

        if not nombre_jugador:
            QMessageBox.warning(self, "Faltan datos", "Debe ingresar el nombre del jugador.")
            return

        self.intentar_recuperar_partida(nombre_jugador)

# Implementación de recuperación o creación de partida

    def intentar_recuperar_partida(self, nombre_jugador):
        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        try:
            # Buscar si existe un jugador con partida pausada
            cursor.execute("""
                SELECT p.id_partida, j.id_jugador, p.semana_actual
                FROM sch_mercaderleyendas.jugador j
                JOIN sch_mercaderleyendas.partida p ON j.id_jugador = p.id_jugador
                WHERE j.nombre_usuario = %s
                AND p.estado_partida = 'pausada'
                ORDER BY p.id_partida DESC
                LIMIT 1;
            """, (nombre_jugador,))
            resultado = cursor.fetchone()

            if resultado:
                id_partida, id_jugador, semana_actual = resultado

                respuesta = QMessageBox.question(
                    self,
                    "Partida Pausada Encontrada",
                    f"🔎 Se encontró una partida pausada de {nombre_jugador}.\n¿Deseas continuarla?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if respuesta == QMessageBox.Yes:
                    # Cambiar estado de partida a activa
                    cursor.execute("""
                        UPDATE sch_mercaderleyendas.partida
                        SET estado_partida = 'activa'
                        WHERE id_partida = %s;
                    """, (id_partida,))
                    conn.commit()
                    conn.close()

                    # Abrir mapa continuando la partida
                    self.mapa = MapaCiudadesWindow(id_jugador, id_partida)
                    self.mapa.semana_actual = semana_actual
                    self.mapa.iniciar_cronometro_semanal()
                    self.mapa.show()
                    self.close()
                else:
                    conn.close()
                    self.input_nombre_jugador.clear()
                    self.input_nombre_jugador.setFocus()
                return

            # Si no hay partida pausada, crear nuevo jugador
            conn.close()
            self.guardar_configuracion(nombre_jugador)

        except Exception as e:
            if conn and not conn.closed:
                conn.rollback()
                conn.close()

            QMessageBox.critical(self, "Error", f"❌ Error al procesar jugador: {e}")


    # Crea nuevo jugador 

    def guardar_configuracion(self, nombre_jugador):
        nombre_personaje = "Kiran"

        velocidad_map = {
            "1 segundo": 1,
            "2 segundos": 2,
            "5 segundos": 5,
            "10 segundos": 10
        }
        velocidad = velocidad_map[self.combo_semana.currentText()]
        oro = self.slider_oro["slider"].value()
        vasijas = self.slider_vasijas["slider"].value()
        camellos = self.slider_camellos["slider"].value()

        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO sch_mercaderleyendas.jugador (nombre_usuario)
                VALUES (%s) RETURNING id_jugador;
            """, (nombre_jugador,))
            id_jugador = cursor.fetchone()[0]
            conn.commit() 
            conn.close()

            self.abrir_ventana_ciudad_producto(id_jugador, nombre_personaje, velocidad, oro, vasijas, camellos)

        except Exception as e:
            if conn and not conn.closed:
                conn.rollback()
                conn.close()

            QMessageBox.critical(self, "Error", f"❌ No se pudo crear el jugador.\n{e}")

    def abrir_ventana_ciudad_producto(self, id_jugador, nombre_personaje, velocidad_juego, oro, vasijas, camellos):
        self.dialogo = SeleccionCiudadProducto(id_jugador, nombre_personaje, velocidad_juego, oro, vasijas, camellos, ventana_preconfig=self)
        self.dialogo.show()
        self.close()
 


# ---------------------- SELECCIÓN DE CIUDAD Y PRODUCTO ----------------------

class SeleccionCiudadProducto(QDialog):
    def __init__(self, id_jugador, nombre_personaje, velocidad_juego, oro, vasijas, camellos, parent=None, ventana_preconfig=None):
        super().__init__(parent)
        self.ventana_preconfig = ventana_preconfig
        self.setWindowTitle("Iniciar partida - Ciudad y Producto")
        self.setFixedSize(400, 250)

        self.id_jugador = id_jugador
        self.nombre_personaje = nombre_personaje
        self.velocidad_juego = velocidad_juego
        self.oro = oro
        self.vasijas = vasijas
        self.camellos = camellos

        self.conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        self.cursor = self.conn.cursor()

        self.ciudades_productos = self.obtener_ciudades_y_productos()

        self.label_ciudad = QLabel("Seleccione una ciudad para iniciar:")
        self.combo_ciudad = QComboBox()
        self.combo_ciudad.addItems(self.ciudades_productos.keys())

        self.label_producto = QLabel("Seleccione el producto a producir:")
        self.combo_producto = QComboBox()

        self.boton_confirmar = QPushButton("Confirmar selección")
        self.boton_confirmar.clicked.connect(self.confirmar)

        self.combo_ciudad.currentTextChanged.connect(self.actualizar_productos)

        layout = QVBoxLayout()
        layout.addWidget(self.label_ciudad)
        layout.addWidget(self.combo_ciudad)
        layout.addWidget(self.label_producto)
        layout.addWidget(self.combo_producto)
        layout.addWidget(self.boton_confirmar)
        self.setLayout(layout)

        self.actualizar_productos()


# Consulta ciudades y productos disponibles para iniciar partida.

    def obtener_ciudades_y_productos(self):
        ciudades_productos = {}
        self.cursor.execute("""
            SELECT c.nombre_ciudad, p.nombre_producto
            FROM sch_mercaderleyendas.ciudad_produce_producto cpp
            JOIN sch_mercaderleyendas.ciudad c ON cpp.id_ciudad = c.id_ciudad
            JOIN sch_mercaderleyendas.producto p ON cpp.id_producto = p.id_producto
            ORDER BY c.nombre_ciudad;
        """)
        for nombre_ciudad, nombre_producto in self.cursor.fetchall():
            ciudades_productos.setdefault(nombre_ciudad, []).append(nombre_producto)
        return ciudades_productos



# Actualiza lista de productos cuando se cambia la ciudad seleccionada.

    def actualizar_productos(self):
        ciudad = self.combo_ciudad.currentText()
        productos = self.ciudades_productos.get(ciudad, [])
        self.combo_producto.clear()
        self.combo_producto.addItems(productos)


# Inserta los datos de partida, personaje e inventario inicial al confirmar la selección.

    def confirmar(self):
        ciudad = self.combo_ciudad.currentText()
        producto = self.combo_producto.currentText()

        if not (ciudad and producto):
            QMessageBox.warning(self, "Faltan datos", "Debes seleccionar una ciudad y un producto.")
            return

        try:
            self.cursor.execute("SELECT id_ciudad FROM sch_mercaderleyendas.ciudad WHERE nombre_ciudad = %s", (ciudad,))
            resultado_ciudad = self.cursor.fetchone()
            if resultado_ciudad is None:
                QMessageBox.critical(self, "Error", f"No se encontró la ciudad '{ciudad}' en la base de datos.")
                return
            id_ciudad = resultado_ciudad[0]

            self.cursor.execute("SELECT id_producto FROM sch_mercaderleyendas.producto WHERE nombre_producto = %s", (producto,))
            resultado_producto = self.cursor.fetchone()
            if resultado_producto is None:
                QMessageBox.critical(self, "Error", f"No se encontró el producto '{producto}' en la base de datos.")
                return
            id_producto = resultado_producto[0]

            self.cursor.execute("""
                INSERT INTO sch_mercaderleyendas.personaje (nombre_personaje, id_ciudad_actual, id_jugador)
                VALUES (%s, %s, %s) RETURNING id_personaje;
            """, (self.nombre_personaje, id_ciudad, self.id_jugador))
            self.cursor.fetchone()
            self.conn.commit()

            self.cursor.execute("""
                INSERT INTO sch_mercaderleyendas.partida (id_jugador, estado_partida, fecha_inicio_partida, velocidad_juego)
                VALUES (%s, 'activa', CURRENT_DATE, %s) RETURNING id_partida;
            """, (self.id_jugador, self.velocidad_juego))
            resultado_partida = self.cursor.fetchone()
            self.conn.commit()

            if resultado_partida is None:
                QMessageBox.critical(self, "Error", "No se pudo crear la partida.")
                return
            id_partida = resultado_partida[0]

            self.cursor.execute("""
                INSERT INTO sch_mercaderleyendas.producto_inicial (id_partida, id_producto)
                VALUES (%s, %s);
            """, (id_partida, id_producto))
            self.conn.commit()

            self.cursor.execute("""
                INSERT INTO sch_mercaderleyendas.inventario (id_jugador, id_producto, cantidad_productos)
                VALUES (%s, %s, 5)
                ON CONFLICT (id_jugador, id_producto) DO UPDATE 
                SET cantidad_productos = sch_mercaderleyendas.inventario.cantidad_productos + 5;
            """, (self.id_jugador, id_producto))
            self.conn.commit()

            def get_id_producto(nombre):
                self.cursor.execute("SELECT id_producto FROM sch_mercaderleyendas.producto WHERE nombre_producto = %s", (nombre,))
                res = self.cursor.fetchone()
                if res is None:
                    raise Exception(f"No se encontró el producto '{nombre}' en la base de datos.")
                return res[0]

            id_oro = get_id_producto('Monedas de oro')
            id_vasijas = get_id_producto('Vasijas')
            id_camellos = get_id_producto('Camellos')

            self.cursor.execute("""
                INSERT INTO sch_mercaderleyendas.inventario (id_jugador, id_producto, cantidad_productos)
                VALUES (%s, %s, %s), (%s, %s, %s), (%s, %s, %s)
            """, (
                self.id_jugador, id_oro, self.oro,
                self.id_jugador, id_vasijas, self.vasijas,
                self.id_jugador, id_camellos, self.camellos
            ))

            self.conn.commit()
            self.conn.close()

            self.mapa_window = MapaCiudadesWindow(self.id_jugador, id_partida)
            self.mapa_window.show()

            self.game_window = GameWindow(id_partida, self.nombre_personaje, ciudad, producto)

            self.game_window.show()

            self.close()

        except Exception as e:
            try:
                if self.conn and not self.conn.closed:
                    self.conn.rollback()
                    self.conn.close()
            except:
                pass
            QMessageBox.critical(self, "Error", str(e))


#---------------------- INVENTARIO ----------------------

class VentanaInventario(QDialog):
    def __init__(self, id_jugador, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventario del Jugador")
        self.setFixedSize(600, 500)
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        contenedor = QWidget()
        layout_contenedor = QVBoxLayout(contenedor)

        self.conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT p.nombre_producto, i.cantidad_productos, p.tipo_producto
            FROM sch_mercaderleyendas.inventario i
            JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
            WHERE i.id_jugador = %s
            ORDER BY p.tipo_producto, p.nombre_producto;
        """, (id_jugador,))
        productos = cursor.fetchall()
        self.conn.close()

        categorias = {'comercial': [], 'herramientas': [], 'logistica': []}
        for nombre, cantidad, tipo in productos:
            categorias[tipo].append((nombre, cantidad))

        for categoria, items in categorias.items():
            seccion = QVBoxLayout()
            seccion.addWidget(QLabel(f"<b>{categoria.capitalize()}</b>"))
            fila = QHBoxLayout()
            for nombre, cantidad in items:
                widget = self.crear_widget_producto(nombre, cantidad)
                fila.addWidget(widget)
            seccion.addLayout(fila)
            layout_contenedor.addLayout(seccion)

        scroll.setWidget(contenedor)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)


# Carga los productos del inventario en un ScrollArea con imágenes si existen.

    def crear_widget_producto(self, nombre, cantidad):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        filename = self.normalizar_nombre(nombre) + ".png"
        if os.path.exists(filename):
            pixmap = QPixmap(filename).scaled(64, 64, Qt.KeepAspectRatio)
        else:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.lightGray)

        img = QLabel()
        img.setPixmap(pixmap)
        img.setAlignment(Qt.AlignCenter)

        label = QLabel(f"{nombre} ({cantidad})")
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(img)
        layout.addWidget(label)
        return widget


# Normaliza el nombre de productos para buscar imágenes.

    def normalizar_nombre(self, nombre):
        nombre = nombre.lower().replace(" ", "_")
        return nombre.replace("á", "a").replace("é", "e").replace("í", "i")\
                     .replace("ó", "o").replace("ú", "u").replace("ñ", "n")



# ---------------------- VIAJES ----------------------

class VentanaViaje(QDialog):
    def __init__(self, id_jugador, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar destino")
        self.setFixedSize(350, 200)
        self.id_jugador = id_jugador
        self.id_caravana_actual = None
        

        layout = QVBoxLayout()
        label = QLabel("Seleccione ciudad destino:")
        self.combo_destino = QComboBox()
        self.obtener_ciudades_disponibles()

        btn_continuar = QPushButton("Verificar recursos")
        btn_continuar.clicked.connect(self.verificar_recursos)

        layout.addWidget(label)
        layout.addWidget(self.combo_destino)
        layout.addWidget(btn_continuar)
        self.setLayout(layout)


# Carga ciudades disponibles para viajar desde la ciudad actual del jugador.

    def obtener_ciudades_disponibles(self):
        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c2.nombre_ciudad
            FROM sch_mercaderleyendas.personaje p
            JOIN sch_mercaderleyendas.ciudad c2 ON p.id_ciudad_actual = c2.id_ciudad
            WHERE p.id_jugador = %s;
        """, (self.id_jugador,))
        self.ciudad_actual = cursor.fetchone()[0]

        cursor.execute("""
            SELECT DISTINCT c.nombre_ciudad
            FROM sch_mercaderleyendas.ruta r
            JOIN sch_mercaderleyendas.ciudad c ON r.id_ciudad_destino = c.id_ciudad
            JOIN sch_mercaderleyendas.personaje p ON r.id_ciudad_origen = p.id_ciudad_actual
            WHERE p.id_jugador = %s;
        """, (self.id_jugador,))
        ciudades = cursor.fetchall()
        conn.close()

        for ciudad in ciudades:
            self.combo_destino.addItem(ciudad[0])



# Verifica si el jugador tiene recursos suficientes para viajar a la ciudad destino.

    def verificar_recursos(self):
        destino = self.combo_destino.currentText()

        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        cursor.execute(""" -- obtener ruta
            SELECT r.semanas_distancia, r.tipo_transporte, r.personal_minimo, r.personal_maximo
            FROM sch_mercaderleyendas.ruta r
            JOIN sch_mercaderleyendas.ciudad o ON r.id_ciudad_origen = o.id_ciudad
            JOIN sch_mercaderleyendas.ciudad d ON r.id_ciudad_destino = d.id_ciudad
            WHERE o.nombre_ciudad = %s AND d.nombre_ciudad = %s;
        """, (self.ciudad_actual, destino))
        ruta_data = cursor.fetchone()
        if not ruta_data:
            QMessageBox.warning(self, "Error", "No se encontró una ruta entre estas ciudades.")
            conn.close()
            return

        semanas, tipo_ruta, personal_min, personal_max = ruta_data
        dias = semanas * 7
        personas = round((personal_min + personal_max) / 2)

        # obtener consumos logísticos
        cursor.execute("""
            SELECT p.nombre_producto,
                CASE 
                    WHEN %s = 'terrestre' THEN plc.consumo_tierra_por_persona_por_dia
                    ELSE plc.consumo_mar_por_persona_por_dia
                END AS consumo_diario
            FROM sch_mercaderleyendas.producto p
            JOIN sch_mercaderleyendas.producto_logistico_consumo plc ON p.id_producto = plc.id_producto_logistico;
        """, (tipo_ruta,))
        consumos = cursor.fetchall()

        requerimientos = {
            nombre: consumo_diario * personas * dias
            for nombre, consumo_diario in consumos
        }

        cursor.execute(""" -- inventario logístico
            SELECT p.nombre_producto, i.cantidad_productos
            FROM sch_mercaderleyendas.inventario i
            JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
            WHERE i.id_jugador = %s AND p.tipo_producto = 'logistica';
        """, (self.id_jugador,))
        inventario = dict(cursor.fetchall())

        cursor.execute(""" -- camellos disponibles
            SELECT cantidad_productos FROM sch_mercaderleyendas.inventario i
            JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
            WHERE i.id_jugador = %s AND p.nombre_producto = 'Camellos';
        """, (self.id_jugador,))
        camellos_disponibles = cursor.fetchone()
        camellos_disponibles = camellos_disponibles[0] if camellos_disponibles else 0

        cursor.execute(""" -- vasijas disponibles
            SELECT cantidad_productos FROM sch_mercaderleyendas.inventario i
            JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
            WHERE i.id_jugador = %s AND p.nombre_producto = 'Vasijas';
        """, (self.id_jugador,))
        vasijas_disponibles = cursor.fetchone()
        vasijas_disponibles = vasijas_disponibles[0] if vasijas_disponibles else 0

        conn.close()

        # precios logísticos
        precios = {
            'Agua': (10, 0.1),
            'carne': (1, 0.2) if tipo_ruta == 'terrestre' else (1, 0.3),
            'Vino': (3, 1.0) if tipo_ruta == 'terrestre' else (3, 1.5)
        }

        resumen = (
            f"🧭 Viaje de {semanas} semanas ({dias} días)\n"
            f"Tipo de ruta: {tipo_ruta}\n"
            f"Rango sugerido: {personal_min}–{personal_max} personas\n"
            f"Usando: {personas} personas (promedio)\n\n"
        )

        suficiente = True
        costo_total = 0
        alforjas_requeridas = 0
        peso_carne = 0
        faltantes = {}

        for nombre, cantidad_requerida in requerimientos.items():
            disponible = inventario.get(nombre, 0)
            unidad, precio = precios.get(nombre, (1, 0))

            faltante = max(0, cantidad_requerida - disponible)
            unidades_necesarias = math.ceil((faltante / unidad) + 5)
            costo_recurso = unidades_necesarias * precio
            costo_total += costo_recurso

            if nombre == 'Agua' or nombre == 'Vino':
                alforjas_requeridas += math.ceil(cantidad_requerida / 10)
            elif nombre.lower() == 'carne':
                peso_carne += cantidad_requerida

            resumen += (
                f"- {nombre}: necesita {cantidad_requerida:.1f} ({disponible} disponible)\n"
                f"    → {unidades_necesarias} unidades a ₡{precio:.2f} cada una = ₡{costo_recurso:.2f}\n"
            )

            if disponible < cantidad_requerida:
                suficiente = False
                faltantes[nombre] = {
                    "faltan": cantidad_requerida - disponible,
                    "unidad": unidad,
                    "precio_unitario": precio
                }

        camellos_para_alforjas = math.ceil(alforjas_requeridas / 2)
        camellos_para_carne = math.ceil(peso_carne / 60)
        camellos_requeridos = camellos_para_alforjas + camellos_para_carne

        if camellos_disponibles < camellos_requeridos:
            suficiente = False

        if vasijas_disponibles < alforjas_requeridas:
            suficiente = False

        resumen += f"\n\n🐪 Camellos necesarios: {camellos_requeridos} (disponibles: {camellos_disponibles})"
        resumen += f"\n🪣 Vasijas necesarias: {alforjas_requeridas} (disponibles: {vasijas_disponibles})"
        resumen += f"\n💰 Costo total estimado para este viaje sumando algunas unidades extra: ₡{costo_total:.2f}\n"

        # mostrar selección de mercancías
        self.ventana_seleccion_mercancias = VentanaSeleccionMercancias(self.id_jugador)
        if self.ventana_seleccion_mercancias.exec_() == QDialog.Accepted:
            self.productos_seleccionados = self.ventana_seleccion_mercancias.obtener_productos_seleccionados()

            if suficiente:
                self.crear_caravana(destino, personas)
                
                try:
                    conn_viaje = psycopg2.connect(
                        dbname="mercaderleyendas",
                        user="postgres",
                        password="1234",
                        host="localhost",
                        port="5433"
                    )
                    cursor_viaje = conn_viaje.cursor()

                    cursor_viaje.execute("""
                        SELECT r.tipo_transporte, r.semanas_distancia, r.id_ruta
                        FROM sch_mercaderleyendas.ruta r
                        JOIN sch_mercaderleyendas.ciudad o ON r.id_ciudad_origen = o.id_ciudad
                        JOIN sch_mercaderleyendas.ciudad d ON r.id_ciudad_destino = d.id_ciudad
                        WHERE o.nombre_ciudad = %s AND d.nombre_ciudad = %s;
                    """, (self.ciudad_actual, destino))
                    tipo_viaje, semanas_duracion, id_ruta = cursor_viaje.fetchone()

                    cursor_viaje.execute("""
                        INSERT INTO sch_mercaderleyendas.viaje (tipo_viaje, duracion_viaje, id_caravana, fecha_inicio, id_jugador, id_ruta)
                        VALUES (%s, %s, %s, CURRENT_DATE, %s, %s)
                        RETURNING id_viaje;
                    """, (tipo_viaje, semanas_duracion, self.id_caravana_actual, self.id_jugador, id_ruta))

                    id_viaje_creado = cursor_viaje.fetchone()[0]
                    self.id_viaje_actual = id_viaje_creado

                    conn_viaje.commit()
                    conn_viaje.close()

                except Exception as e:
                    print(f"❌ Error al crear el viaje: {e}")

                self.realizar_viaje(destino, semanas)



            else:
                respuesta = QMessageBox.question(
                    self, "Recursos insuficientes", resumen + "\n\n¿Deseas comprar automáticamente lo necesario?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                )
                if respuesta == QMessageBox.Yes:
                    ventana = VentanaCompraNecesaria(self.id_jugador, faltantes, self, costo_total=costo_total)
                    if ventana.exec_() == QDialog.Accepted:
                        self.crear_caravana(destino, personas)
                        try:
                            conn_viaje = psycopg2.connect(
                                dbname="mercaderleyendas",
                                user="postgres",
                                password="1234",
                                host="localhost",
                                port="5433"
                            )
                            cursor_viaje = conn_viaje.cursor()

                            cursor_viaje.execute("""
                                SELECT r.tipo_transporte, r.semanas_distancia, r.id_ruta
                                FROM sch_mercaderleyendas.ruta r
                                JOIN sch_mercaderleyendas.ciudad o ON r.id_ciudad_origen = o.id_ciudad
                                JOIN sch_mercaderleyendas.ciudad d ON r.id_ciudad_destino = d.id_ciudad
                                WHERE o.nombre_ciudad = %s AND d.nombre_ciudad = %s;
                            """, (self.ciudad_actual, destino))
                            tipo_viaje, semanas_duracion, id_ruta = cursor_viaje.fetchone()

                            cursor_viaje.execute("""
                                INSERT INTO sch_mercaderleyendas.viaje (tipo_viaje, duracion_viaje, id_caravana, fecha_inicio, id_jugador, id_ruta)
                                VALUES (%s, %s, %s, CURRENT_DATE, %s, %s)
                                RETURNING id_viaje;
                            """, (tipo_viaje, semanas_duracion, self.id_caravana_actual, self.id_jugador, id_ruta))

                            id_viaje_creado = cursor_viaje.fetchone()[0]
                            self.id_viaje_actual = id_viaje_creado

                            conn_viaje.commit()
                            conn_viaje.close()

                        except Exception as e:
                            print(f"❌ Error al crear el viaje: {e}")


                        self.realizar_viaje(destino, semanas)


        else:
            QMessageBox.information(self, "Cancelado", "No seleccionaste mercancías para el viaje.")



# Abre ventana de compra de recursos logísticos.

    def abrir_ventana_compra_logistica(self):
            ventana = VentanaCompraLogistica(self.id_jugador, self.ciudad_actual, self)
            ventana.exec_()


# Crea la caravana para el viaje, asignando productos seleccionados.
    def crear_caravana(self, destino, personas):
        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        try:
            # Buscar la partida activa
            cursor.execute("""
                SELECT id_partida
                FROM sch_mercaderleyendas.partida
                WHERE id_jugador = %s AND estado_partida = 'activa'
                ORDER BY id_partida DESC
                LIMIT 1;
            """, (self.id_jugador,))
            partida_activa = cursor.fetchone()
            if not partida_activa:
                QMessageBox.warning(self, "Error", "No hay partida activa para asignar la caravana.")
                conn.close()
                return
            id_partida = partida_activa[0]

            # Buscar la ruta
            cursor.execute("""
                SELECT r.id_ruta
                FROM sch_mercaderleyendas.ruta r
                JOIN sch_mercaderleyendas.ciudad o ON r.id_ciudad_origen = o.id_ciudad
                JOIN sch_mercaderleyendas.ciudad d ON r.id_ciudad_destino = d.id_ciudad
                WHERE o.nombre_ciudad = %s AND d.nombre_ciudad = %s;
            """, (self.ciudad_actual, destino))
            id_ruta = cursor.fetchone()[0]

            # Insertar nueva caravana (incluyendo id_partida)
            cursor.execute("""
                INSERT INTO sch_mercaderleyendas.caravana (id_ruta, estado_caravana, personal, id_partida)
                VALUES (%s, 'en ruta', %s, %s)
                RETURNING id_caravana;
            """, (id_ruta, personas, id_partida))
            id_caravana = cursor.fetchone()[0]
            conn.commit()

            # Insertar productos en la caravana
            for nombre_producto in self.productos_seleccionados:
                cursor.execute("""
                    SELECT id_producto
                    FROM sch_mercaderleyendas.producto
                    WHERE nombre_producto = %s;
                """, (nombre_producto,))
                id_producto = cursor.fetchone()[0]
            

                cursor.execute("""
                    SELECT cantidad_productos
                    FROM sch_mercaderleyendas.inventario
                    WHERE id_jugador = %s AND id_producto = %s;
                """, (self.id_jugador, id_producto))
                cantidad_disponible = cursor.fetchone()
                cantidad = cantidad_disponible[0] if cantidad_disponible else 0

                if cantidad > 0:
                    cursor.execute("""
                        INSERT INTO sch_mercaderleyendas.producto_caravana (id_caravana, id_producto, cantidad_producto)
                        VALUES (%s, %s, %s);
                    """, (id_caravana, id_producto, cantidad))
                    conn.commit()

                    # Descontar del inventario
                    cursor.execute("""
                        UPDATE sch_mercaderleyendas.inventario
                        SET cantidad_productos = cantidad_productos - %s
                        WHERE id_jugador = %s AND id_producto = %s;
                    """, (cantidad, self.id_jugador, id_producto))
                    conn.commit()

            self.id_caravana_actual = id_caravana

        except Exception as e:
            if conn and not conn.closed:
                conn.rollback()
            QMessageBox.critical(self, "Error", f"❌ Error al crear la caravana: {e}")

        finally:
            conn.close()

# Simula el viaje a la ciudad destino, descontando recursos consumidos.

    def realizar_viaje(self, destino, semanas_duracion):
        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT velocidad_juego
                FROM sch_mercaderleyendas.partida
                WHERE id_jugador = %s AND estado_partida = 'activa'
                ORDER BY id_partida DESC
                LIMIT 1;
            """, (self.id_jugador,))
            velocidad = cursor.fetchone()[0]

            duracion_total = int(semanas_duracion * velocidad * 1000)

            progreso = QProgressDialog("Viajando...", None, 0, 0, self)
            progreso.setWindowTitle("🧭 En camino...")
            progreso.setWindowModality(Qt.WindowModal)
            progreso.setCancelButton(None)
            progreso.show()

            def terminar_viaje():
                progreso.cancel()
                try:
                    # Obtener la id_ciudad_destino
                    cursor.execute("SELECT id_ciudad FROM sch_mercaderleyendas.ciudad WHERE nombre_ciudad = %s", (destino,))
                    id_ciudad_destino = cursor.fetchone()[0]

                    # Actualizar la ciudad del personaje
                    cursor.execute("""
                        UPDATE sch_mercaderleyendas.personaje
                        SET id_ciudad_actual = %s
                        WHERE id_jugador = %s;
                    """, (id_ciudad_destino, self.id_jugador))

                    # Obtener IDs de productos logísticos
                    cursor.execute("""
                        SELECT p.nombre_producto, p.id_producto
                        FROM sch_mercaderleyendas.producto p
                        WHERE p.nombre_producto IN ('Agua', 'carne', 'Vino', 'Vasijas', 'Camellos');
                    """)
                    ids = {nombre.lower(): id_producto for nombre, id_producto in cursor.fetchall()}

                    # Obtener información de la ruta
                    cursor.execute("""
                        SELECT r.semanas_distancia, r.tipo_transporte, r.personal_minimo, r.personal_maximo
                        FROM sch_mercaderleyendas.ruta r
                        JOIN sch_mercaderleyendas.ciudad o ON r.id_ciudad_origen = o.id_ciudad
                        JOIN sch_mercaderleyendas.ciudad d ON r.id_ciudad_destino = d.id_ciudad
                        WHERE o.nombre_ciudad = %s AND d.nombre_ciudad = %s;
                    """, (self.ciudad_actual, destino))
                    semanas, tipo_ruta, pmin, pmax = cursor.fetchone()
                    dias = semanas * 7
                    personas = round((pmin + pmax) / 2)

                    # Obtener consumos por persona y día
                    cursor.execute("""
                        SELECT p.nombre_producto,
                            CASE WHEN %s = 'terrestre'
                                THEN plc.consumo_tierra_por_persona_por_dia
                                ELSE plc.consumo_mar_por_persona_por_dia
                            END AS consumo_diario
                        FROM sch_mercaderleyendas.producto p
                        JOIN sch_mercaderleyendas.producto_logistico_consumo plc
                        ON p.id_producto = plc.id_producto_logistico;
                    """, (tipo_ruta,))
                    consumos = cursor.fetchall()

                    vasijas_usadas = 0
                    total_consumo_carne = 0

                    for nombre, consumo_diario in consumos:
                        nombre_lower = nombre.lower()
                        total_consumo = consumo_diario * personas * dias

                        if nombre_lower in ('agua', 'vino'):
                            unidades_necesarias = math.ceil(total_consumo / 10)

                            cursor.execute("""
                                SELECT cantidad_productos
                                FROM sch_mercaderleyendas.inventario
                                WHERE id_jugador = %s AND id_producto = %s;
                            """, (self.id_jugador, ids[nombre_lower]))
                            actual = cursor.fetchone()
                            cantidad_actual = actual[0] if actual else 0

                            cantidad_a_rebajar = min(cantidad_actual, unidades_necesarias)

                            cursor.execute("""
                                UPDATE sch_mercaderleyendas.inventario
                                SET cantidad_productos = cantidad_productos - %s
                                WHERE id_jugador = %s AND id_producto = %s;
                            """, (cantidad_a_rebajar, self.id_jugador, ids[nombre_lower]))

                            vasijas_usadas += cantidad_a_rebajar

                        elif nombre_lower == 'carne':
                            cursor.execute("""
                                SELECT cantidad_productos
                                FROM sch_mercaderleyendas.inventario
                                WHERE id_jugador = %s AND id_producto = %s;
                            """, (self.id_jugador, ids[nombre_lower]))
                            actual = cursor.fetchone()
                            cantidad_actual = actual[0] if actual else 0

                            cantidad_a_rebajar = min(cantidad_actual, total_consumo)

                            cursor.execute("""
                                UPDATE sch_mercaderleyendas.inventario
                                SET cantidad_productos = cantidad_productos - %s
                                WHERE id_jugador = %s AND id_producto = %s;
                            """, (cantidad_a_rebajar, self.id_jugador, ids[nombre_lower]))

                            total_consumo_carne += total_consumo

                    # Rebajar vasijas
                    cursor.execute("""
                        SELECT cantidad_productos
                        FROM sch_mercaderleyendas.inventario
                        WHERE id_jugador = %s AND id_producto = %s;
                    """, (self.id_jugador, ids['vasijas']))
                    actual_vasijas = cursor.fetchone()
                    cantidad_vasijas_actual = actual_vasijas[0] if actual_vasijas else 0

                    cantidad_a_rebajar_vasijas = min(cantidad_vasijas_actual, vasijas_usadas)

                    cursor.execute("""
                        UPDATE sch_mercaderleyendas.inventario
                        SET cantidad_productos = cantidad_productos - %s
                        WHERE id_jugador = %s AND id_producto = %s;
                    """, (cantidad_a_rebajar_vasijas, self.id_jugador, ids['vasijas']))

                    # Rebajar camellos
                    camellos_para_vasijas = math.ceil(vasijas_usadas / 2)
                    camellos_para_carne = math.ceil(total_consumo_carne / 60)
                    camellos_usados = camellos_para_vasijas + camellos_para_carne

                    cursor.execute("""
                        SELECT cantidad_productos
                        FROM sch_mercaderleyendas.inventario
                        WHERE id_jugador = %s AND id_producto = %s;
                    """, (self.id_jugador, ids['camellos']))
                    actual_camellos = cursor.fetchone()
                    cantidad_camellos_actual = actual_camellos[0] if actual_camellos else 0

                    cantidad_a_rebajar_camellos = min(cantidad_camellos_actual, camellos_usados)

                    cursor.execute("""
                        UPDATE sch_mercaderleyendas.inventario
                        SET cantidad_productos = cantidad_productos - %s
                        WHERE id_jugador = %s AND id_producto = %s;
                    """, (cantidad_a_rebajar_camellos, self.id_jugador, ids['camellos']))

                    # Evaluar misión
                    cursor.execute("""
                        SELECT id_viaje
                        FROM sch_mercaderleyendas.viaje
                        WHERE id_caravana = %s
                        ORDER BY id_viaje DESC
                        LIMIT 1;
                    """, (self.id_caravana_actual,))
                    resultado = cursor.fetchone()

                    if resultado:
                        id_viaje = resultado[0]
                        cursor.execute("SELECT sch_mercaderleyendas.evaluar_mision(%s);", (id_viaje,))
                        resultado_mision = cursor.fetchone()[0]

                        if resultado_mision == 'Éxito':
                            QMessageBox.information(self, "Resultado del viaje", "🚩 ¡La caravana llegó exitosamente!")
                        else:
                            QMessageBox.warning(self, "Resultado del viaje", "⚠️ ¡La caravana fracasó en el viaje!")

                        self.ciudad_actual = destino

                    conn.commit()
                    QMessageBox.information(self, "Llegaste", f"🏙️ Has llegado a {destino}. El viaje ha finalizado.")
                    self.close()

                except Exception as e:
                    if conn and not conn.closed:
                        conn.rollback()
                    QMessageBox.critical(self, "Error", str(e))

                finally:
                    if conn and not conn.closed:
                        conn.close()

            QTimer.singleShot(duracion_total, terminar_viaje)

        except Exception as e:
            if conn and not conn.closed:
                conn.rollback()
                conn.close()
            QMessageBox.critical(self, "Error", f"Ocurrió un error durante el viaje: {e}")

        

# ---------------------- COMPRA DE PRODUCTOS LOGÍSTICOS PARA VIAJAR ----------------------

class VentanaCompraLogistica(QDialog):
    def __init__(self, id_jugador, ciudad_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compra de productos logísticos y herramientas")
        self.setFixedSize(400, 220)
        self.id_jugador = id_jugador
        self.ciudad_actual = ciudad_actual

        layout = QVBoxLayout()

        self.label_info = QLabel("Seleccione producto a comprar:")
        layout.addWidget(self.label_info)

        self.combo_productos = QComboBox()
        layout.addWidget(self.combo_productos)

        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(1)
        self.spin_cantidad.setMaximum(10000)
        layout.addWidget(self.spin_cantidad)

        self.btn_comprar = QPushButton("Comprar")
        self.btn_comprar.clicked.connect(self.realizar_compra)
        layout.addWidget(self.btn_comprar)

        self.setLayout(layout)

        self.cargar_productos_disponibles()



# Carga productos logísticos y herramientas disponibles para comprar.

    def cargar_productos_disponibles(self):
        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id_producto, nombre_producto, costo_terrestre, cantidad_unidad
            FROM sch_mercaderleyendas.producto
            WHERE tipo_producto IN ('logistica', 'herramientas');
        """)
        self.productos = cursor.fetchall()

        self.combo_productos.clear()
        for prod in self.productos:
            nombre = prod[1]
            precio = prod[2]
            unidad = prod[3]
            unidad_texto = f"por {unidad}" if unidad else ""
            self.combo_productos.addItem(f"{nombre} (₡{precio} {unidad_texto})", prod)

        conn.close()



# Realiza la compra de productos logísticos y actualiza inventario y monedas de oro.

    def realizar_compra(self):
        producto = self.combo_productos.currentData()
        cantidad_deseada = self.spin_cantidad.value()
        id_producto, nombre_producto, precio_unidad, cantidad_por_unidad = producto

        # Si no tiene unidad definida, asumimos 1 unidad = 1 producto
        cantidad_por_unidad = cantidad_por_unidad if cantidad_por_unidad else 1
        unidades_necesarias = math.ceil(cantidad_deseada / cantidad_por_unidad)
        total_costo = unidades_necesarias * precio_unidad

        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id_producto FROM sch_mercaderleyendas.producto
            WHERE nombre_producto = 'Monedas de oro'
            LIMIT 1;
        """)
        id_oro = cursor.fetchone()
        if not id_oro:
            QMessageBox.warning(self, "Error", "No se encontró el producto 'Monedas de oro'.")
            conn.close()
            return
        id_oro = id_oro[0]

        cursor.execute("""
            SELECT cantidad_productos FROM sch_mercaderleyendas.inventario
            WHERE id_jugador = %s AND id_producto = %s;
        """, (self.id_jugador, id_oro))
        oro_actual = cursor.fetchone()
        oro_disponible = oro_actual[0] if oro_actual else 0

        if oro_disponible < total_costo:
            QMessageBox.warning(self, "Oro insuficiente", f"Necesitas ₡{total_costo}, pero solo tienes ₡{oro_disponible}.")
            conn.close()
            return

        cursor.execute("""
            UPDATE sch_mercaderleyendas.inventario
            SET cantidad_productos = cantidad_productos - %s
            WHERE id_jugador = %s AND id_producto = %s;
        """, (total_costo, self.id_jugador, id_oro))
        conn.commit()

        cursor.execute("""
            INSERT INTO sch_mercaderleyendas.inventario (id_jugador, id_producto, cantidad_productos)
            VALUES (%s, %s, %s)
            ON CONFLICT (id_jugador, id_producto)
            DO UPDATE SET cantidad_productos = inventario.cantidad_productos + EXCLUDED.cantidad_productos;
        """, (self.id_jugador, id_producto, unidades_necesarias))
        conn.commit()
        conn.close()

        QMessageBox.information(
            self, "Compra realizada",
            f"Has comprado {cantidad_deseada} unidades de {nombre_producto} por ₡{total_costo}.\n"
            f"(Paquetes pagados: {unidades_necesarias} de {cantidad_por_unidad})"
        )
        self.close()



class VentanaCompraNecesaria(QDialog):
    def __init__(self, id_jugador, faltantes, parent=None, costo_total=0):
        super().__init__(parent)
        self.setWindowTitle("Comprar lo necesario para viajar")
        self.setFixedSize(500, 400)
        self.id_jugador = id_jugador
        self.faltantes = faltantes
        self.costo_total = costo_total
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        resumen = "📋 Productos faltantes para el viaje:\n\n"
        self.costo_total = 0

        for producto, datos in self.faltantes.items():
            cantidad_faltante = datos["faltan"]
            unidad = datos["unidad"]
            precio_unitario = datos["precio_unitario"]

            unidades_necesarias = math.ceil((cantidad_faltante / unidad) + 5)
            costo = unidades_necesarias * precio_unitario
            self.costo_total += costo

            resumen += (
                f"- {producto}: necesitas {cantidad_faltante:.1f}, "
                f"comprarás {unidades_necesarias} unidades → ₡{costo:.2f}\n"
            )

        resumen += f"\n💰 Total estimado a pagar: ₡{self.costo_total:.2f}"

        self.label_resumen = QLabel(resumen)
        layout.addWidget(self.label_resumen)

        botones_layout = QHBoxLayout()

        btn_confirmar = QPushButton("Confirmar compra")
        btn_confirmar.clicked.connect(self.confirmar_compra)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        botones_layout.addWidget(btn_confirmar)
        botones_layout.addWidget(btn_cancelar)

        layout.addLayout(botones_layout)
        self.setLayout(layout)

    # Ejecuta la compra automática de productos faltantes descontando oro.
    def confirmar_compra(self):
        try:
            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()

            # Verificar si tiene suficiente oro
            cursor.execute("""
                SELECT id_producto
                FROM sch_mercaderleyendas.producto
                WHERE nombre_producto = 'Monedas de oro';
            """)
            id_oro = cursor.fetchone()[0]

            cursor.execute("""
                SELECT cantidad_productos
                FROM sch_mercaderleyendas.inventario
                WHERE id_jugador = %s AND id_producto = %s;
            """, (self.id_jugador, id_oro))
            resultado_oro = cursor.fetchone()
            oro_disponible = resultado_oro[0] if resultado_oro else 0

            if oro_disponible < self.costo_total:
                QMessageBox.warning(self, "Oro insuficiente", f"No tienes suficiente oro.\nNecesitas ₡{self.costo_total:.2f} y solo tienes ₡{oro_disponible:.2f}.")
                conn.close()
                self.reject()
                return

            # Insertar los productos
            for producto, datos in self.faltantes.items():
                cantidad_faltante = datos["faltan"]
                unidad = datos["unidad"]

                unidades_necesarias = math.ceil((cantidad_faltante / unidad) + 5)

                cursor.execute("""
                    SELECT id_producto
                    FROM sch_mercaderleyendas.producto
                    WHERE nombre_producto = %s;
                """, (producto,))
                resultado = cursor.fetchone()
                conn.commit()

                if resultado:
                    id_producto = resultado[0]

                    cursor.execute("""
                        INSERT INTO sch_mercaderleyendas.inventario (id_jugador, id_producto, cantidad_productos)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id_jugador, id_producto)
                        DO UPDATE SET cantidad_productos = inventario.cantidad_productos + EXCLUDED.cantidad_productos;
                    """, (self.id_jugador, id_producto, unidades_necesarias))
                    conn.commit()
                else:
                    print(f"⚠️ Producto {producto} no encontrado en la base de datos. No se insertó.")

            # Descontar monedas de oro
            cursor.execute("""
                UPDATE sch_mercaderleyendas.inventario
                SET cantidad_productos = cantidad_productos - %s
                WHERE id_jugador = %s AND id_producto = %s;
            """, (self.costo_total, self.id_jugador, id_oro))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Compra realizada", "¡Los recursos faltantes fueron comprados exitosamente!")
            self.accept()

        except Exception as e:
            print(f"❌ Error en compra automática: {e}")
            QMessageBox.critical(self, "Error", "No se pudo realizar la compra automática.")
            self.reject()



# ---------------------- SELECCIONAR MERCANCIA PARA VIAJAR ----------------------

class VentanaSeleccionMercancias(QDialog):
    def __init__(self, id_jugador, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Mercancías para el Viaje")
        self.setFixedSize(400, 400)
        self.id_jugador = id_jugador
        self.productos_seleccionados = {}

        layout = QVBoxLayout()

        label = QLabel("Selecciona los productos a enviar:")
        layout.addWidget(label)

        self.lista_productos = QListWidget()
        self.lista_productos.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.lista_productos)

        botones = QHBoxLayout()
        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.clicked.connect(self.accept)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_confirmar)
        botones.addWidget(btn_cancelar)

        layout.addLayout(botones)
        self.setLayout(layout)

        self.cargar_productos_comerciales()

    def cargar_productos_comerciales(self):
        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.nombre_producto, i.cantidad_productos
            FROM sch_mercaderleyendas.inventario i
            JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
            WHERE i.id_jugador = %s AND p.tipo_producto = 'comercial';
        """, (self.id_jugador,))
        productos = cursor.fetchall()
        conn.close()

        for nombre, cantidad in productos:
            item = QListWidgetItem(f"{nombre}")
            item.setData(Qt.UserRole, (nombre, cantidad))
            self.lista_productos.addItem(item)

    def obtener_productos_seleccionados(self):
        seleccionados = self.lista_productos.selectedItems()
        productos = {}
        for item in seleccionados:
            nombre, cantidad = item.data(Qt.UserRole)
            productos[nombre] = cantidad
        return productos



# ---------------------- UTILIDADES DE PRODUCTOS Y PRECIOS PARA TRANSACCIONES ----------------------


# Utilidad: Devuelve productos disponibles para comprar en la ciudad actual.

def obtener_productos_para_comprar(ciudad_actual):
    conn = psycopg2.connect(
        dbname="mercaderleyendas",
        user="postgres",
        password="1234",
        host="localhost",
        port="5433"
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nombre_producto
        FROM sch_mercaderleyendas.ciudad_produce_producto cpp
        JOIN sch_mercaderleyendas.ciudad c ON cpp.id_ciudad = c.id_ciudad
        JOIN sch_mercaderleyendas.producto p ON cpp.id_producto = p.id_producto
        WHERE c.nombre_ciudad = %s;
    """, (ciudad_actual,))
    productos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return productos



# Utilidad: Devuelve productos que la ciudad actual acepta para vender.

def obtener_productos_para_vender(ciudad_actual):
    conn = psycopg2.connect(
        dbname="mercaderleyendas",
        user="postgres",
        password="1234",
        host="localhost",
        port="5433"
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.nombre_producto
        FROM sch_mercaderleyendas.ciudad_consume_producto ccp
        JOIN sch_mercaderleyendas.ciudad c ON ccp.id_ciudad = c.id_ciudad
        JOIN sch_mercaderleyendas.producto p ON ccp.id_producto = p.id_producto
        WHERE c.nombre_ciudad = %s;
    """, (ciudad_actual,))
    productos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return productos


# Calcula el precio de compra o venta de un producto, dependiendo de si hay precio especial o no.

def calcular_precio_producto(nombre_producto, tipo_transaccion, ciudad_actual):
    conn = psycopg2.connect(
        dbname="mercaderleyendas",
        user="postgres",
        password="1234",
        host="localhost",
        port="5433"
    )
    cursor = conn.cursor()
    
    if nombre_producto.lower() == 'vasijas':
        conn.close()
        return 5
    if nombre_producto.lower() == 'camellos':
        conn.close()
        return 20
    
    if nombre_producto.lower() == 'carne':
        conn.close()
        return 2 

    cursor.execute("""
        SELECT precio_base
        FROM sch_mercaderleyendas.precio_producto pp
        JOIN sch_mercaderleyendas.producto p ON pp.id_producto = p.id_producto
        WHERE p.nombre_producto = %s
        AND pp.id_ciudad = (SELECT id_ciudad FROM sch_mercaderleyendas.ciudad WHERE nombre_ciudad = %s)
    """, (nombre_producto, ciudad_actual))
    precio = cursor.fetchone()
    
    if precio:
        conn.close()
        return precio[0]
    else:
        if tipo_transaccion == 'compra':
            cursor.execute("""
                SELECT 1
                FROM sch_mercaderleyendas.ciudad_produce_producto cpp
                JOIN sch_mercaderleyendas.ciudad c ON cpp.id_ciudad = c.id_ciudad
                JOIN sch_mercaderleyendas.producto p ON cpp.id_producto = p.id_producto
                WHERE c.nombre_ciudad = %s AND p.nombre_producto = %s;
            """, (ciudad_actual, nombre_producto))
            es_producido = cursor.fetchone()
            conn.close()
            if es_producido:
                return 1
            else:
                return 2
        elif tipo_transaccion == 'venta':
            conn.close()
            return 2

    conn.close()
    return 9999


# ---------------------- TRANSACCIONES ----------------------

class VentanaTransacciones(QDialog):
    def __init__(self, id_jugador, ciudad_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transacciones")
        self.setFixedSize(300, 150)
        self.id_jugador = id_jugador
        self.ciudad_actual = ciudad_actual

        layout = QVBoxLayout()
        label = QLabel("Selecciona el tipo de transacción:")

        self.combo_opcion = QComboBox()
        self.combo_opcion.addItems(["Compra", "Venta"])

        boton_continuar = QPushButton("Continuar")
        boton_continuar.clicked.connect(self.abrir_ventana_tipo)

        layout.addWidget(label)
        layout.addWidget(self.combo_opcion)
        layout.addWidget(boton_continuar)
        self.setLayout(layout)

    def abrir_ventana_tipo(self):
        tipo = self.combo_opcion.currentText()
        if tipo == "Compra":
            self.ventana = VentanaCompraProductos(self.id_jugador, self.ciudad_actual)
        else:
            self.ventana = VentanaVentaProductos(self.id_jugador, self.ciudad_actual)
        self.ventana.exec_()
        self.close()

class VentanaCompraProductos(QDialog):
    def __init__(self, id_jugador, ciudad_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compra de Productos")
        self.setFixedSize(400, 300)
        self.id_jugador = id_jugador
        self.ciudad_actual = ciudad_actual

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Producto a comprar:"))

        self.combo_productos = QComboBox()
        self.cargar_productos_disponibles()
        layout.addWidget(self.combo_productos)

        layout.addWidget(QLabel("Cantidad a comprar:"))
        self.input_cantidad = QLineEdit()
        layout.addWidget(self.input_cantidad)

        self.btn_comprar = QPushButton("Comprar")
        self.btn_comprar.clicked.connect(self.comprar_producto)
        layout.addWidget(self.btn_comprar)

        self.setLayout(layout)

    def cargar_productos_disponibles(self):
        productos = obtener_productos_para_comprar(self.ciudad_actual)
        self.combo_productos.addItems(productos)

    def comprar_producto(self):
        producto = self.combo_productos.currentText()
        try:
            cantidad = int(self.input_cantidad.text())
            if cantidad <= 0:
                raise ValueError("Cantidad inválida")
        except:
            QMessageBox.warning(self, "Error", "Ingrese una cantidad válida.")
            return

        conn = psycopg2.connect(
            dbname="mercaderleyendas", user="postgres", password="1234", host="localhost", port="5433"
        )
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id_producto FROM sch_mercaderleyendas.producto
                WHERE nombre_producto = %s;
            """, (producto,))
            id_producto = cursor.fetchone()[0]

            precio_unitario = calcular_precio_producto(producto, tipo_transaccion='compra', ciudad_actual=self.ciudad_actual)
            costo_total = precio_unitario * cantidad

            cursor.execute("""
                SELECT cantidad_productos FROM sch_mercaderleyendas.inventario
                WHERE id_jugador = %s AND id_producto = (
                    SELECT id_producto FROM sch_mercaderleyendas.producto WHERE nombre_producto = 'Monedas de oro'
                );
            """, (self.id_jugador,))
            disponible = cursor.fetchone()[0]

            if disponible < costo_total:
                QMessageBox.warning(self, "Error", f"No tienes suficiente oro (Disponible: ₡{disponible}, Costo: ₡{costo_total}).")
                conn.close()
                return

            cursor.execute("""
                UPDATE sch_mercaderleyendas.inventario
                SET cantidad_productos = cantidad_productos - %s
                WHERE id_jugador = %s AND id_producto = (
                    SELECT id_producto FROM sch_mercaderleyendas.producto WHERE nombre_producto = 'Monedas de oro'
                );
            """, (costo_total, self.id_jugador))
            conn.commit()
            cursor.execute("""
                INSERT INTO sch_mercaderleyendas.inventario (id_jugador, id_producto, cantidad_productos)
                VALUES (%s, %s, %s)
                ON CONFLICT (id_jugador, id_producto)
                DO UPDATE SET cantidad_productos = inventario.cantidad_productos + EXCLUDED.cantidad_productos;
            """, (self.id_jugador, id_producto, cantidad))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Compra", f"¡Compra realizada! Pagaste ₡{costo_total}.")
            self.close()

        except Exception as e:
            if conn and not conn.closed:
                conn.rollback()
                conn.close()

            QMessageBox.critical(self, "Error", str(e))


class VentanaVentaProductos(QDialog):
    def __init__(self, id_jugador, ciudad_actual, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Venta de Productos")
        self.setFixedSize(400, 300)
        self.id_jugador = id_jugador
        self.ciudad_actual = ciudad_actual

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Producto a vender:"))

        self.combo_productos = QComboBox()
        self.cargar_productos_vendibles()
        layout.addWidget(self.combo_productos)

        layout.addWidget(QLabel("Cantidad a vender:"))
        self.input_cantidad = QLineEdit()
        layout.addWidget(self.input_cantidad)

        btn_vender = QPushButton("Vender")
        btn_vender.clicked.connect(self.vender_producto)
        layout.addWidget(btn_vender)

        self.setLayout(layout)

    def cargar_productos_vendibles(self):
        productos = obtener_productos_para_vender(self.ciudad_actual)
        self.combo_productos.addItems(productos)

    def vender_producto(self):
        producto = self.combo_productos.currentText()
        try:
            cantidad = int(self.input_cantidad.text())
            if cantidad <= 0:
                raise ValueError("Cantidad inválida")
        except:
            QMessageBox.warning(self, "Error", "Ingrese una cantidad válida.")
            return

        try:
            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()

            # Buscar ID del producto
            cursor.execute("""
                SELECT id_producto FROM sch_mercaderleyendas.producto
                WHERE nombre_producto = %s;
            """, (producto,))
            resultado = cursor.fetchone()
            if not resultado:
                QMessageBox.warning(self, "Error", f"Producto {producto} no encontrado.")
                conn.close()
                return
            id_producto = resultado[0]

            # Verificar que esté en una caravana
            cursor.execute("""
                SELECT pc.id_producto
                FROM sch_mercaderleyendas.producto_caravana pc
                JOIN sch_mercaderleyendas.caravana c ON pc.id_caravana = c.id_caravana
            """)
            productos_caravana = [row[0] for row in cursor.fetchall()]

            if id_producto not in productos_caravana:
                QMessageBox.warning(self, "Producto no permitido", "❌ Este producto no fue transportado en la caravana. No puedes venderlo.")
                conn.close()
                return

            # Verificar cantidad en inventario
            cursor.execute("""
                SELECT cantidad_productos FROM sch_mercaderleyendas.inventario
                WHERE id_jugador = %s AND id_producto = %s;
            """, (self.id_jugador, id_producto))
            resultado_inventario = cursor.fetchone()
            if resultado_inventario is None or resultado_inventario[0] < cantidad:
                QMessageBox.warning(self, "Error", "No tienes suficientes productos para vender.")
                conn.close()
                return

            # Buscar precio de venta
            cursor.execute("""
                SELECT c.id_ciudad
                FROM sch_mercaderleyendas.personaje p
                JOIN sch_mercaderleyendas.ciudad c ON p.id_ciudad_actual = c.id_ciudad
                WHERE p.id_jugador = %s;
            """, (self.id_jugador,))
            id_ciudad = cursor.fetchone()[0]

            cursor.execute("""
                SELECT precio_base
                FROM sch_mercaderleyendas.precio_producto
                WHERE id_ciudad = %s AND id_producto = %s;
            """, (id_ciudad, id_producto))
            resultado_precio = cursor.fetchone()
            precio_unitario = resultado_precio[0] if resultado_precio else 2  # Default 2

            total_monedas = precio_unitario * cantidad

            confirmar = QMessageBox.question(
                self,
                "Confirmar venta",
                f"Vas a vender {cantidad} unidades de {producto} por ₡{total_monedas} monedas.\n¿Deseas continuar?",
                QMessageBox.Yes | QMessageBox.No
            )

            if confirmar != QMessageBox.Yes:
                conn.close()
                return

            # Descontar productos vendidos
            cursor.execute("""
                UPDATE sch_mercaderleyendas.inventario
                SET cantidad_productos = cantidad_productos - %s
                WHERE id_jugador = %s AND id_producto = %s;
            """, (cantidad, self.id_jugador, id_producto))
            conn.commit()

            # Sumar monedas de oro
            cursor.execute("""
                SELECT id_producto FROM sch_mercaderleyendas.producto
                WHERE nombre_producto = 'Monedas de oro';
            """)
            id_oro = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO sch_mercaderleyendas.inventario (id_jugador, id_producto, cantidad_productos)
                VALUES (%s, %s, %s)
                ON CONFLICT (id_jugador, id_producto)
                DO UPDATE SET cantidad_productos = inventario.cantidad_productos + EXCLUDED.cantidad_productos;
            """, (self.id_jugador, id_oro, total_monedas))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Venta realizada", f"¡Has vendido {cantidad} {producto} por ₡{total_monedas} monedas!")
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ---------------------- VISUALIZACIÓN DEL MAPA ----------------------

class MapaCiudadesWindow(QWidget):
    def __init__(self, id_jugador, id_partida):
        super().__init__()
        self.setWindowTitle("Mapa de Ciudades")
        self.id_jugador = id_jugador
        self.id_partida = id_partida

        # Inicializar semana_actual desde base de datos
        self.semana_actual = self.obtener_semana_actual()

        self.timer_guardado = QTimer(self)
        self.timer_guardado.timeout.connect(self.guardar_partida)
        self.timer_guardado.start(2 * 60 * 1000)

        layout = QVBoxLayout(self)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        # Mostrar semana actual
        self.label_semanas = QLabel(f"📅 Semana: {self.semana_actual}")

        # Mostrar autoguardado
        self.label_autoguardado = QLabel("")

        semanas_layout = QHBoxLayout()
        semanas_layout.addWidget(self.label_semanas)
        semanas_layout.addStretch()
        semanas_layout.addWidget(self.label_autoguardado)

        layout.addLayout(semanas_layout)

        self.iniciar_cronometro_semanal()

        # Cargar fondo
        try:
            fondo = QPixmap("mapa.jpg")
            if fondo.isNull():
                raise Exception("Imagen no encontrada o inválida")
            self.scene.addItem(QGraphicsPixmapItem(fondo))
            self.scene.setSceneRect(0, 0, fondo.width(), fondo.height())
            self.setFixedSize(fondo.width(), fondo.height() + 40)
        except Exception as e:
            self.scene.setSceneRect(0, 0, 1020, 765)
            self.setFixedSize(1020, 805)
            print(f"⚠️ No se pudo cargar el fondo del mapa: {e}")

        self.dibujar_ciudades()

        # Botones principales
        botones_layout = QHBoxLayout()

        # Botón cambiar velocidad
        btn_cambiar_velocidad = QPushButton("Velocidad")
        btn_cambiar_velocidad.setFixedSize(100, 30)
        btn_cambiar_velocidad.clicked.connect(self.cambiar_velocidad)
        botones_layout.addWidget(btn_cambiar_velocidad)

        # Botón viajar
        btn_viajar = QPushButton("Viajar")
        btn_viajar.setFixedSize(100, 30)
        btn_viajar.clicked.connect(self.abrir_ventana_viaje)
        botones_layout.addWidget(btn_viajar)

        # Botón inventario
        btn_inventario = QPushButton("Inventario")
        btn_inventario.setFixedSize(100, 30)
        btn_inventario.clicked.connect(self.abrir_inventario)
        botones_layout.addWidget(btn_inventario)

        # Botón transacciones
        btn_transacciones = QPushButton("Transacción")
        btn_transacciones.setFixedSize(100, 30)
        btn_transacciones.clicked.connect(self.abrir_transacciones)
        botones_layout.addWidget(btn_transacciones)

        # Botón Guardar
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setFixedSize(100, 30)
        btn_guardar.clicked.connect(self.guardar_partida)
        botones_layout.addWidget(btn_guardar)

        # Botón Pausar
        btn_pausar = QPushButton("Pausar partida")
        btn_pausar.setFixedSize(100, 30)
        btn_pausar.clicked.connect(self.pausar_partida)
        botones_layout.addWidget(btn_pausar)

        # Botón Finalizar
        btn_finalizar = QPushButton("Finalizar partida")
        btn_finalizar.setFixedSize(100, 30)
        btn_finalizar.clicked.connect(lambda: self.finalizar_partida("manual"))
        botones_layout.addWidget(btn_finalizar)


        layout.addLayout(botones_layout)
 
        # Temporizador de autoguardado
        
        self.timer_guardado = QTimer(self)
        self.timer_guardado.timeout.connect(lambda: self.guardar_partida(mostrar_mensaje=False))
        self.timer_guardado.start(2 * 60 * 1000) 



# Dibuja las ciudades del mapa como puntos en un QGraphicsScene.

    def dibujar_ciudades(self):
        try:
            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT nombre_ciudad, coordenada_x, coordenada_y FROM sch_mercaderleyendas.ciudad;")
            ciudades = cursor.fetchall()
            conn.close()

            for nombre, x, y in ciudades:
                punto = QGraphicsEllipseItem(x - 4, y - 4, 8, 8)
                punto.setBrush(QBrush(QColor("darkred")))
                punto.setPen(QPen(Qt.black))
                self.scene.addItem(punto)
        except Exception as e:
            print(f"⚠️ Error al cargar ciudades: {e}")



# Inicializa un temporizador que simula el avance del tiempo (semanas) en el juego.

    def iniciar_cronometro_semanal(self):
        try:
            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT velocidad_juego
                FROM sch_mercaderleyendas.partida
                WHERE id_jugador = %s AND estado_partida = 'activa'
                ORDER BY id_partida DESC LIMIT 1;
            """, (self.id_jugador,))
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                segundos_por_semana = int(resultado[0])

                if hasattr(self, 'timer_semanas') and self.timer_semanas.isActive():
                    self.timer_semanas.stop()

                self.timer_semanas = QTimer(self)
                self.timer_semanas.timeout.connect(self.avanzar_semana)
                self.timer_semanas.start(segundos_por_semana * 1000)

        except Exception as e:
            print(f"⚠️ Error al iniciar cronómetro semanal: {e}")



# Lógica para aumentar en 1 semana el contador del juego y registrar avance en base de datos.


    def avanzar_semana(self):
        self.semana_actual += 1
        self.label_semanas.setText(f"📅 Semana: {self.semana_actual}")

        try:
            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()

            # Registrar avance de semana
            cursor.execute("""
                INSERT INTO sch_mercaderleyendas.avance_tiempo (id_jugador, semana_simulada)
                VALUES (%s, %s);
            """, (self.id_jugador, self.semana_actual))
            conn.commit()

            # Verificar si se agotó el tiempo
            if self.semana_actual >= 156:
                conn.close()
                self.finalizar_partida("tiempo agotado")
                return

            # Verificar si hay camellos disponibles
            cursor.execute("""
                SELECT cantidad_productos
                FROM sch_mercaderleyendas.inventario i
                JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
                WHERE i.id_jugador = %s AND p.nombre_producto = 'Camellos';
            """, (self.id_jugador,))
            camellos = cursor.fetchone()
            camellos_disponibles = camellos[0] if camellos else 0

            # Verificar si tiene la habilidad "Leena"
            cursor.execute("""
                SELECT COUNT(*)
                FROM sch_mercaderleyendas.jugador_habilidad jh
                JOIN sch_mercaderleyendas.habilidad h ON jh.id_habilidad = h.id_habilidad
                WHERE jh.id_jugador = %s AND h.nombre_habilidad = 'Leena';
            """, (self.id_jugador,))
            tiene_leena = cursor.fetchone()[0] > 0

            conn.commit()

            if camellos_disponibles == 0 and not tiene_leena:
                conn.close()
                self.finalizar_partida("sin recursos")
                return

        except Exception as e:
            if conn:
                conn.rollback()
            QMessageBox.critical(self, "Error", str(e))

        finally:
            if conn:
                conn.close()


# Obtener la semana actual desde la base de datos.
    
    def obtener_semana_actual(self):
        try:
            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT semana_actual
                FROM sch_mercaderleyendas.partida
                WHERE id_partida = %s;
            """, (self.id_partida,))
            resultado = cursor.fetchone()
            conn.close()

            if resultado and resultado[0] is not None:
                return resultado[0]
            else:
                return 1

        except Exception as e:
            print(f"⚠️ Error al obtener semana actual: {e}")
            return 1


# Abre el inventario del jugador.

    def abrir_inventario(self): 
        ventana = VentanaInventario(self.id_jugador)
        ventana.exec_()



# Abre la ventana para iniciar un viaje.

    def abrir_ventana_viaje(self):
        ventana = VentanaViaje(self.id_jugador)
        ventana.exec_()



# Abre ventana de transacciones en ciudad actual.

    def abrir_transacciones(self):
        conn = psycopg2.connect(
            dbname="mercaderleyendas",
            user="postgres",
            password="1234",
            host="localhost",
            port="5433"
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.nombre_ciudad
            FROM sch_mercaderleyendas.personaje p
            JOIN sch_mercaderleyendas.ciudad c ON p.id_ciudad_actual = c.id_ciudad
            WHERE p.id_jugador = %s;
        """, (self.id_jugador,))
        ciudad_actual = cursor.fetchone()[0]
        conn.close()

        ventana = VentanaTransacciones(self.id_jugador, ciudad_actual)
        ventana.exec_()


# Guarda el estado de la partida como finalizada manualmente.

    def guardar_partida(self, mostrar_mensaje=True):
        try:
            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()

            # Buscar partida activa
            cursor.execute("""
                SELECT id_partida
                FROM sch_mercaderleyendas.partida
                WHERE id_jugador = %s AND estado_partida = 'activa'
                ORDER BY id_partida DESC
                LIMIT 1;
            """, (self.id_jugador,))
            partida = cursor.fetchone()
            if not partida:
                if mostrar_mensaje:
                    QMessageBox.warning(self, "Error", "No hay partida activa para guardar.")
                conn.close()
                return
            id_partida = partida[0]

            # Contar caravanas completadas de la partida
            cursor.execute("""
                SELECT COUNT(*)
                FROM sch_mercaderleyendas.caravana
                WHERE estado_caravana = 'exitosa'
                AND id_partida = %s;
            """, (id_partida,))
            caravanas_completadas = cursor.fetchone()[0]

            # Obtener inventario
            cursor.execute("""
                SELECT pr.nombre_producto, i.cantidad_productos
                FROM sch_mercaderleyendas.inventario i
                JOIN sch_mercaderleyendas.producto pr ON i.id_producto = pr.id_producto
                WHERE i.id_jugador = %s;
            """, (self.id_jugador,))
            inventario = cursor.fetchall()
            recursos_texto = ", ".join([f"{nombre}: {cantidad}" for nombre, cantidad in inventario]) if inventario else "Sin recursos"

            # Obtener monedas de oro
            cursor.execute("""
                SELECT cantidad_productos
                FROM sch_mercaderleyendas.inventario i
                JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
                WHERE i.id_jugador = %s AND p.nombre_producto = 'Monedas de oro';
            """, (self.id_jugador,))
            resultado_oro = cursor.fetchone()
            monedas_oro = resultado_oro[0] if resultado_oro else 0

            # Actualizar datos de la partida
            cursor.execute("""
                UPDATE sch_mercaderleyendas.partida
                SET caravanas_completadas = %s,
                    recursos_restantes = %s,
                    ranking_final = %s,
                    semana_actual = %s
                WHERE id_partida = %s;
            """, (caravanas_completadas, recursos_texto, monedas_oro, self.semana_actual, id_partida))

            conn.commit()
            conn.close()

            self.label_autoguardado.setText("📝 Partida guardada.")
            QTimer.singleShot(5000, lambda: self.label_autoguardado.setText(""))

        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", f"❌ Error: {e}")


# Pausa la partida, deteniendo el avance de semanas y el autoguardado.

    def pausar_partida(self):
        try:
            # Primero guardamos todo correctamente
            self.guardar_partida(mostrar_mensaje=False)

            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()

            # Buscar partida activa
            cursor.execute("""
                SELECT id_partida
                FROM sch_mercaderleyendas.partida
                WHERE id_jugador = %s AND estado_partida = 'activa'
                ORDER BY id_partida DESC
                LIMIT 1;
            """, (self.id_jugador,))
            partida = cursor.fetchone()
            if not partida:
                QMessageBox.warning(self, "Error", "No hay partida activa para pausar.")
                conn.close()
                return

            id_partida = partida[0]

            # Actualizar la partida como 'pausada'
            cursor.execute("""
                UPDATE sch_mercaderleyendas.partida
                SET estado_partida = 'pausada'
                WHERE id_partida = %s;
            """, (id_partida,))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Partida pausada", "⏸️ ¡Tu partida fue guardada y pausada!")
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error al pausar partida", f"❌ Error: {e}")


# Cambia la velocidad de la semana en el juego.
    def cambiar_velocidad(self):
        opciones = ["1 segundo", "2 segundos", "5 segundos", "10 segundos"]
        
        combo, ok = QInputDialog.getItem(
            self,
            "Cambiar velocidad de semana",
            "Seleccione duración de semana:",
            opciones,
            editable=False
        )

        if ok and combo:
            nuevo_valor = int(combo.split()[0])
            
            # Detener timer viejo
            self.timer_semanas.stop()

            # Empezar timer nuevo
            self.timer_semanas.start(nuevo_valor * 1000)

            # Actualizar la base de datos
            try:
                conn = psycopg2.connect(
                    dbname="mercaderleyendas",
                    user="postgres",
                    password="1234",
                    host="localhost",
                    port="5433"
                )
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE sch_mercaderleyendas.partida
                    SET velocidad_juego = %s
                    WHERE id_jugador = %s
                    AND estado_partida = 'activa';
                """, (nuevo_valor, self.id_jugador))

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Velocidad actualizada", f"✅ Nueva duración de semana: {nuevo_valor} segundos.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"❌ Error al actualizar velocidad: {e}")


# Finaliza la partida por tiempo agotado o falta de camellos si no ha encontrado a Leena.

    def finalizar_partida(self, razon):
        try:
            conn = psycopg2.connect(
                dbname="mercaderleyendas",
                user="postgres",
                password="1234",
                host="localhost",
                port="5433"
            )
            cursor = conn.cursor()

            # Buscar partida activa
            cursor.execute("""
                SELECT id_partida
                FROM sch_mercaderleyendas.partida
                WHERE id_jugador = %s AND estado_partida = 'activa'
                ORDER BY id_partida DESC
                LIMIT 1;
            """, (self.id_jugador,))
            partida = cursor.fetchone()
            if not partida:
                conn.close()
                return
            id_partida = partida[0]

            # Contar caravanas completadas
            cursor.execute("""
                SELECT COUNT(*)
                FROM sch_mercaderleyendas.caravana
                WHERE estado_caravana = 'exitosa'
                AND id_partida = %s;
            """, (id_partida,))
            caravanas_completadas = cursor.fetchone()[0]

            # Obtener inventario
            cursor.execute("""
                SELECT pr.nombre_producto, i.cantidad_productos
                FROM sch_mercaderleyendas.inventario i
                JOIN sch_mercaderleyendas.producto pr ON i.id_producto = pr.id_producto
                WHERE i.id_jugador = %s;
            """, (self.id_jugador,))
            inventario = cursor.fetchall()
            recursos_texto = ", ".join([f"{nombre}: {cantidad}" for nombre, cantidad in inventario]) if inventario else "Sin recursos"

            # Obtener monedas de oro
            cursor.execute("""
                SELECT cantidad_productos
                FROM sch_mercaderleyendas.inventario i
                JOIN sch_mercaderleyendas.producto p ON i.id_producto = p.id_producto
                WHERE i.id_jugador = %s AND p.nombre_producto = 'Monedas de oro';
            """, (self.id_jugador,))
            resultado_oro = cursor.fetchone()
            monedas_oro = resultado_oro[0] if resultado_oro else 0

            # Cerrar partida
            cursor.execute("""
                UPDATE sch_mercaderleyendas.partida
                SET estado_partida = 'finalizada',
                    fecha_fin_partida = CURRENT_DATE,
                    razon_fin = %s,
                    caravanas_completadas = %s,
                    recursos_restantes = %s,
                    ranking_final = %s,
                    semana_actual = %s
                WHERE id_partida = %s;
            """, (razon, caravanas_completadas, recursos_texto, monedas_oro, self.semana_actual, id_partida))

            conn.commit()
            conn.close()

            # Mostrar mensaje de fin
            if razon == "tiempo agotado":
                mensaje = "⏳ ¡El tiempo de aventuras ha terminado!"
            elif razon == "sin recursos":
                mensaje = "🐪 ¡No puedes continuar, no hay camellos!"
            elif razon == "manual":
                mensaje = "🏁 ¡Has finalizado la partida manualmente!"
            else:
                mensaje = "🏁 ¡La partida ha terminado!"
            QMessageBox.information(
                self,
                "🏁 Fin de la Aventura",
                f"{mensaje}\n\n"
                f"🪙 Monedas de oro: ₡{monedas_oro}\n"
                f"🏆 Ranking final: {monedas_oro} puntos\n\n"
                "¡Gracias por jugar."
            )

            if hasattr(self, "timer_guardado"):
                self.timer_guardado.stop()

            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Error al finalizar partida: {e}")

# ---------------------- INICIAR APLICACIÓN ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = PreconfigWindow()
    ventana.show()
    sys.exit(app.exec_())