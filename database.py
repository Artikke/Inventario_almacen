import sqlite3
import os
import shutil
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")

CICLO_DIAS = 20  # Duración de cada ciclo en días


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def backup_db():
    """Respalda la base de datos con timestamp."""
    if not os.path.exists(DB_PATH):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"inventario_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    # Mantener solo los últimos 10 respaldos
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")],
        reverse=True,
    )
    for old in backups[10:]:
        os.remove(os.path.join(BACKUP_DIR, old))
    return dest


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        lider TEXT NOT NULL DEFAULT '',
        emoji TEXT NOT NULL DEFAULT '🏢'
    );

    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL DEFAULT 'General',
        unidad TEXT NOT NULL DEFAULT 'pieza',
        stock_almacen INTEGER NOT NULL DEFAULT 0,
        minimo_reorden INTEGER NOT NULL DEFAULT 0,
        activo INTEGER NOT NULL DEFAULT 1,
        fecha_creacion TEXT NOT NULL DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS ciclos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        numero INTEGER NOT NULL DEFAULT 1,
        fecha_inicio TEXT NOT NULL,
        fecha_cierre TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'abierto'
    );

    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_id INTEGER NOT NULL,
        ciclo_id INTEGER NOT NULL,
        fecha_pedido TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'pendiente',
        notas TEXT,
        prioridad TEXT NOT NULL DEFAULT 'normal',
        FOREIGN KEY (area_id) REFERENCES areas(id),
        FOREIGN KEY (ciclo_id) REFERENCES ciclos(id)
    );

    CREATE TABLE IF NOT EXISTS detalle_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        cantidad_entregada INTEGER DEFAULT 0,
        FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    );

    CREATE TABLE IF NOT EXISTS inventario_area (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL DEFAULT 0,
        ultima_actualizacion TEXT,
        FOREIGN KEY (area_id) REFERENCES areas(id),
        FOREIGN KEY (producto_id) REFERENCES productos(id),
        UNIQUE(area_id, producto_id)
    );

    CREATE TABLE IF NOT EXISTS log_actividad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        usuario TEXT,
        area TEXT,
        accion TEXT NOT NULL,
        detalle TEXT
    );
    """)

    # --- Áreas con emojis ---
    areas = [
        ("Talento Humano", "", "👥"),
        ("Mesa de Atención al Cliente", "", "📞"),
        ("Contabilidad", "", "📒"),
        ("Finanzas", "", "💰"),
        ("Crédito y Cobranza", "", "💳"),
        ("Abastecimiento y Compras", "", "🛒"),
        ("Tecnología de Información (TI)", "", "💻"),
        ("Business Intelligence (BI)", "", "📊"),
    ]
    for nombre, lider, emoji in areas:
        conn.execute(
            "INSERT OR IGNORE INTO areas (nombre, lider, emoji) VALUES (?, ?, ?)",
            (nombre, lider, emoji),
        )

    conn.commit()
    conn.close()


def cargar_catalogo_ejemplo():
    """Carga un catálogo de ejemplo con productos típicos de oficina."""
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    if count > 0:
        conn.close()
        return False  # Ya hay productos

    productos = [
        # Papelería
        ("Hojas blancas carta (resma 500)", "Papelería", "resma", 50),
        ("Hojas blancas oficio (resma 500)", "Papelería", "resma", 30),
        ("Folder tamaño carta", "Papelería", "paquete", 40),
        ("Folder tamaño oficio", "Papelería", "paquete", 30),
        ("Sobre manila carta", "Papelería", "paquete", 25),
        ("Sobre manila oficio", "Papelería", "paquete", 20),
        ("Libreta profesional rayada", "Papelería", "pieza", 60),
        ("Libreta profesional cuadro", "Papelería", "pieza", 40),
        ("Post-it notas adhesivas (paquete)", "Papelería", "paquete", 50),
        ("Separadores de colores", "Papelería", "paquete", 30),
        ("Clips estándar (caja)", "Papelería", "caja", 40),
        ("Clips mariposa (caja)", "Papelería", "caja", 25),
        ("Grapas estándar (caja)", "Papelería", "caja", 35),
        ("Ligas de hule (bolsa)", "Papelería", "bolsa", 20),

        # Escritura
        ("Pluma azul punto mediano", "Escritura", "pieza", 100),
        ("Pluma negra punto mediano", "Escritura", "pieza", 100),
        ("Pluma roja punto mediano", "Escritura", "pieza", 50),
        ("Lápiz #2 c/goma", "Escritura", "pieza", 80),
        ("Marcatextos amarillo", "Escritura", "pieza", 40),
        ("Marcatextos verde", "Escritura", "pieza", 30),
        ("Marcatextos rosa", "Escritura", "pieza", 30),
        ("Marcador permanente negro", "Escritura", "pieza", 30),
        ("Marcador para pizarrón negro", "Escritura", "pieza", 20),
        ("Marcador para pizarrón azul", "Escritura", "pieza", 20),
        ("Corrector líquido", "Escritura", "pieza", 25),
        ("Borrador blanco", "Escritura", "pieza", 40),

        # Impresión
        ("Tóner negro HP universal", "Impresión", "pieza", 10),
        ("Tóner color HP universal", "Impresión", "pieza", 6),
        ("Cartucho tinta negro", "Impresión", "pieza", 8),
        ("Cartucho tinta color", "Impresión", "pieza", 6),
        ("Papel fotográfico carta", "Impresión", "paquete", 10),

        # Organización
        ("Archivero de cartón", "Organización", "pieza", 20),
        ("Charola organizadora escritorio", "Organización", "pieza", 15),
        ("Engrapadora estándar", "Organización", "pieza", 10),
        ("Perforadora 2 orificios", "Organización", "pieza", 10),
        ("Tijeras de oficina", "Organización", "pieza", 15),
        ("Cinta adhesiva transparente", "Organización", "pieza", 30),
        ("Cinta canela para empaque", "Organización", "rollo", 15),
        ("Calculadora de escritorio", "Organización", "pieza", 8),

        # Tecnología
        ("Mouse USB", "Tecnología", "pieza", 10),
        ("Teclado USB", "Tecnología", "pieza", 8),
        ("Cable USB-C", "Tecnología", "pieza", 15),
        ("Cable HDMI 2m", "Tecnología", "pieza", 8),
        ("Memoria USB 32GB", "Tecnología", "pieza", 10),
        ("Pilas AA (paquete 4)", "Tecnología", "paquete", 20),
        ("Pilas AAA (paquete 4)", "Tecnología", "paquete", 15),
        ("Audífonos con micrófono", "Tecnología", "pieza", 10),

        # Limpieza y Higiene
        ("Gel antibacterial 500ml", "Limpieza y Higiene", "pieza", 30),
        ("Toallas húmedas desinfectantes", "Limpieza y Higiene", "paquete", 25),
        ("Papel higiénico (paquete 4)", "Limpieza y Higiene", "paquete", 40),
        ("Servilletas (paquete)", "Limpieza y Higiene", "paquete", 30),
        ("Jabón líquido para manos 500ml", "Limpieza y Higiene", "pieza", 20),
        ("Aromatizante en aerosol", "Limpieza y Higiene", "pieza", 15),
        ("Bolsas de basura grandes", "Limpieza y Higiene", "rollo", 20),

        # Cafetería
        ("Café soluble 200g", "Cafetería", "bote", 15),
        ("Azúcar (kilo)", "Cafetería", "kilo", 10),
        ("Sustituto de crema", "Cafetería", "bote", 10),
        ("Vasos desechables 8oz (paquete 50)", "Cafetería", "paquete", 20),
        ("Cucharas desechables (paquete 50)", "Cafetería", "paquete", 15),
        ("Agua purificada garrafón 20L", "Cafetería", "pieza", 20),
        ("Galletas surtido (paquete)", "Cafetería", "paquete", 10),
        ("Té surtido (caja 25 sobres)", "Cafetería", "caja", 10),
    ]

    for nombre, categoria, unidad, stock in productos:
        conn.execute(
            "INSERT INTO productos (nombre, categoria, unidad, stock_almacen) VALUES (?, ?, ?, ?)",
            (nombre, categoria, unidad, stock),
        )

    log_actividad(conn, "Sistema", None, "Catálogo cargado", f"{len(productos)} productos de ejemplo")
    conn.commit()
    conn.close()
    return True


# --- Ciclos automáticos ---

def asegurar_ciclo_activo():
    """Crea automáticamente un nuevo ciclo de 20 días si no hay uno abierto."""
    conn = get_conn()
    activo = conn.execute(
        "SELECT * FROM ciclos WHERE estado='abierto' ORDER BY fecha_inicio DESC LIMIT 1"
    ).fetchone()

    if activo:
        # Verificar si ya venció
        cierre = datetime.strptime(activo["fecha_cierre"], "%Y-%m-%d")
        if datetime.now() > cierre:
            conn.execute("UPDATE ciclos SET estado='cerrado' WHERE id=?", (activo["id"],))
            conn.commit()
            activo = None

    if not activo:
        # Obtener el número del siguiente ciclo
        ultimo = conn.execute("SELECT MAX(numero) as max_num FROM ciclos").fetchone()
        num = (ultimo["max_num"] or 0) + 1

        hoy = datetime.now()
        inicio = hoy.strftime("%Y-%m-%d")
        cierre = (hoy + timedelta(days=CICLO_DIAS)).strftime("%Y-%m-%d")
        mes = hoy.strftime("%B %Y").capitalize()
        nombre = f"Ciclo #{num} — {mes}"

        conn.execute(
            "INSERT INTO ciclos (nombre, numero, fecha_inicio, fecha_cierre) VALUES (?, ?, ?, ?)",
            (nombre, num, inicio, cierre),
        )
        log_actividad(conn, "Sistema", None, "Ciclo creado", nombre)
        conn.commit()

    conn.close()


# --- Log ---

def log_actividad(conn_or_none, usuario, area, accion, detalle=""):
    if conn_or_none is None:
        conn = get_conn()
        conn.execute(
            "INSERT INTO log_actividad (usuario, area, accion, detalle) VALUES (?, ?, ?, ?)",
            (usuario, area, accion, detalle),
        )
        conn.commit()
        conn.close()
    else:
        conn_or_none.execute(
            "INSERT INTO log_actividad (usuario, area, accion, detalle) VALUES (?, ?, ?, ?)",
            (usuario, area, accion, detalle),
        )


def get_log_actividad(limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM log_actividad ORDER BY fecha DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Productos ---

def get_productos(solo_activos=True):
    conn = get_conn()
    if solo_activos:
        rows = conn.execute("SELECT * FROM productos WHERE activo=1 ORDER BY categoria, nombre").fetchall()
    else:
        rows = conn.execute("SELECT * FROM productos ORDER BY categoria, nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categorias():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT categoria FROM productos WHERE activo=1 ORDER BY categoria").fetchall()
    conn.close()
    return [r["categoria"] for r in rows]


def agregar_producto(nombre, categoria, unidad, stock):
    conn = get_conn()
    conn.execute(
        "INSERT INTO productos (nombre, categoria, unidad, stock_almacen) VALUES (?, ?, ?, ?)",
        (nombre, categoria, unidad, stock),
    )
    log_actividad(conn, "Admin", None, "Producto agregado", nombre)
    conn.commit()
    conn.close()


def agregar_productos_masivo(productos_list):
    """Carga masiva de productos: lista de (nombre, categoria, unidad, stock)."""
    conn = get_conn()
    count = 0
    for nombre, categoria, unidad, stock in productos_list:
        conn.execute(
            "INSERT INTO productos (nombre, categoria, unidad, stock_almacen) VALUES (?, ?, ?, ?)",
            (nombre, categoria, unidad, stock),
        )
        count += 1
    log_actividad(conn, "Admin", None, "Carga masiva", f"{count} productos")
    conn.commit()
    conn.close()
    return count


def actualizar_producto(prod_id, nombre, categoria, unidad, stock, activo):
    conn = get_conn()
    conn.execute(
        "UPDATE productos SET nombre=?, categoria=?, unidad=?, stock_almacen=?, activo=? WHERE id=?",
        (nombre, categoria, unidad, stock, activo, prod_id),
    )
    conn.commit()
    conn.close()


def actualizar_stock(prod_id, nuevo_stock):
    conn = get_conn()
    conn.execute("UPDATE productos SET stock_almacen=? WHERE id=?", (nuevo_stock, prod_id))
    conn.commit()
    conn.close()


# --- Áreas ---

def get_areas():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM areas ORDER BY nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def actualizar_lider(area_id, lider):
    conn = get_conn()
    conn.execute("UPDATE areas SET lider=? WHERE id=?", (lider, area_id))
    conn.commit()
    conn.close()


# --- Ciclos ---

def get_ciclo_activo():
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM ciclos WHERE estado='abierto' ORDER BY fecha_inicio DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_ciclos():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM ciclos ORDER BY fecha_inicio DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def crear_ciclo(nombre, numero, fecha_inicio, fecha_cierre):
    conn = get_conn()
    conn.execute(
        "INSERT INTO ciclos (nombre, numero, fecha_inicio, fecha_cierre) VALUES (?, ?, ?, ?)",
        (nombre, numero, fecha_inicio, fecha_cierre),
    )
    log_actividad(conn, "Admin", None, "Ciclo creado", nombre)
    conn.commit()
    conn.close()


def cerrar_ciclo(ciclo_id):
    conn = get_conn()
    conn.execute("UPDATE ciclos SET estado='cerrado' WHERE id=?", (ciclo_id,))
    log_actividad(conn, "Admin", None, "Ciclo cerrado", f"ID {ciclo_id}")
    conn.commit()
    conn.close()


# --- Pedidos ---

def crear_pedido(area_id, ciclo_id, items, notas="", prioridad="normal"):
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    area = conn.execute("SELECT nombre FROM areas WHERE id=?", (area_id,)).fetchone()
    area_nombre = area["nombre"] if area else "?"

    cur = conn.execute(
        "INSERT INTO pedidos (area_id, ciclo_id, fecha_pedido, notas, prioridad) VALUES (?, ?, ?, ?, ?)",
        (area_id, ciclo_id, now, notas, prioridad),
    )
    pedido_id = cur.lastrowid

    detalles = []
    for producto_id, cantidad in items:
        conn.execute(
            "INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad) VALUES (?, ?, ?)",
            (pedido_id, producto_id, cantidad),
        )
        prod = conn.execute("SELECT nombre FROM productos WHERE id=?", (producto_id,)).fetchone()
        detalles.append(f"{prod['nombre']} x{cantidad}")

    log_actividad(conn, area_nombre, area_nombre, "Pedido creado",
                  f"#{pedido_id}: {', '.join(detalles[:3])}{'...' if len(detalles) > 3 else ''}")
    conn.commit()
    conn.close()
    return pedido_id


def get_pedidos_area(area_id, ciclo_id=None):
    conn = get_conn()
    if ciclo_id:
        rows = conn.execute(
            """SELECT p.*, c.nombre as ciclo_nombre
               FROM pedidos p JOIN ciclos c ON p.ciclo_id=c.id
               WHERE p.area_id=? AND p.ciclo_id=?
               ORDER BY p.fecha_pedido DESC""",
            (area_id, ciclo_id),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT p.*, c.nombre as ciclo_nombre
               FROM pedidos p JOIN ciclos c ON p.ciclo_id=c.id
               WHERE p.area_id=?
               ORDER BY p.fecha_pedido DESC""",
            (area_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_detalle_pedido(pedido_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT dp.*, p.nombre as producto_nombre, p.unidad, p.categoria
           FROM detalle_pedido dp
           JOIN productos p ON dp.producto_id=p.id
           WHERE dp.pedido_id=?""",
        (pedido_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_todos_pedidos(ciclo_id=None, estado=None):
    conn = get_conn()
    conditions = []
    params = []
    if ciclo_id:
        conditions.append("p.ciclo_id=?")
        params.append(ciclo_id)
    if estado:
        conditions.append("p.estado=?")
        params.append(estado)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = conn.execute(
        f"""SELECT p.*, a.nombre as area_nombre, a.emoji as area_emoji, c.nombre as ciclo_nombre
            FROM pedidos p
            JOIN areas a ON p.area_id=a.id
            JOIN ciclos c ON p.ciclo_id=c.id
            {where}
            ORDER BY
                CASE p.prioridad WHEN 'urgente' THEN 0 ELSE 1 END,
                p.fecha_pedido DESC""",
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def contar_pedidos_pendientes():
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as c FROM pedidos WHERE estado='pendiente'").fetchone()
    conn.close()
    return row["c"]


def actualizar_estado_pedido(pedido_id, estado):
    conn = get_conn()
    conn.execute("UPDATE pedidos SET estado=? WHERE id=?", (estado, pedido_id))
    pedido = conn.execute(
        "SELECT p.*, a.nombre as area FROM pedidos p JOIN areas a ON p.area_id=a.id WHERE p.id=?",
        (pedido_id,)
    ).fetchone()
    log_actividad(conn, "Admin", pedido["area"], f"Pedido {estado}", f"#{pedido_id}")
    conn.commit()
    conn.close()


def entregar_pedido(pedido_id):
    conn = get_conn()
    conn.execute("UPDATE pedidos SET estado='entregado' WHERE id=?", (pedido_id,))
    detalles = conn.execute(
        "SELECT producto_id, cantidad FROM detalle_pedido WHERE pedido_id=?",
        (pedido_id,),
    ).fetchall()
    pedido = conn.execute(
        "SELECT p.area_id, a.nombre as area FROM pedidos p JOIN areas a ON p.area_id=a.id WHERE p.id=?",
        (pedido_id,)
    ).fetchone()
    area_id = pedido["area_id"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for d in detalles:
        # Actualizar inventario del área
        conn.execute(
            """INSERT INTO inventario_area (area_id, producto_id, cantidad, ultima_actualizacion)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(area_id, producto_id)
               DO UPDATE SET cantidad=cantidad+?, ultima_actualizacion=?""",
            (area_id, d["producto_id"], d["cantidad"], now, d["cantidad"], now),
        )
        # Descontar del stock del almacén
        conn.execute(
            "UPDATE productos SET stock_almacen = MAX(0, stock_almacen - ?) WHERE id=?",
            (d["cantidad"], d["producto_id"]),
        )
        conn.execute(
            "UPDATE detalle_pedido SET cantidad_entregada=? WHERE pedido_id=? AND producto_id=?",
            (d["cantidad"], pedido_id, d["producto_id"]),
        )

    log_actividad(conn, "Admin", pedido["area"], "Pedido entregado", f"#{pedido_id}")
    conn.commit()
    conn.close()


# --- Inventario por área ---

def get_inventario_area(area_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT ia.*, p.nombre as producto_nombre, p.unidad, p.categoria
           FROM inventario_area ia
           JOIN productos p ON ia.producto_id=p.id
           WHERE ia.area_id=?
           ORDER BY p.categoria, p.nombre""",
        (area_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Analytics ---

def get_resumen_por_area(ciclo_id=None):
    conn = get_conn()
    if ciclo_id:
        rows = conn.execute(
            """SELECT a.nombre as area, a.emoji,
                   COUNT(DISTINCT p.id) as total_pedidos,
                   COALESCE(SUM(dp.cantidad), 0) as total_items,
                   SUM(CASE WHEN p.estado='entregado' THEN 1 ELSE 0 END) as entregados,
                   SUM(CASE WHEN p.estado='pendiente' THEN 1 ELSE 0 END) as pendientes
            FROM areas a
            LEFT JOIN pedidos p ON a.id=p.area_id AND p.ciclo_id=?
            LEFT JOIN detalle_pedido dp ON p.id=dp.pedido_id
            GROUP BY a.id, a.nombre
            ORDER BY total_items DESC""",
            (ciclo_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT a.nombre as area, a.emoji,
                   COUNT(DISTINCT p.id) as total_pedidos,
                   COALESCE(SUM(dp.cantidad), 0) as total_items,
                   SUM(CASE WHEN p.estado='entregado' THEN 1 ELSE 0 END) as entregados,
                   SUM(CASE WHEN p.estado='pendiente' THEN 1 ELSE 0 END) as pendientes
            FROM areas a
            LEFT JOIN pedidos p ON a.id=p.area_id
            LEFT JOIN detalle_pedido dp ON p.id=dp.pedido_id
            GROUP BY a.id, a.nombre
            ORDER BY total_items DESC""",
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_productos_mas_pedidos(ciclo_id=None, limit=10):
    conn = get_conn()
    if ciclo_id:
        rows = conn.execute(
            """SELECT pr.nombre, pr.categoria, pr.unidad, pr.stock_almacen,
                      SUM(dp.cantidad) as total
               FROM detalle_pedido dp
               JOIN productos pr ON dp.producto_id=pr.id
               JOIN pedidos p ON dp.pedido_id=p.id
               WHERE p.ciclo_id=?
               GROUP BY pr.id ORDER BY total DESC LIMIT ?""",
            (ciclo_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT pr.nombre, pr.categoria, pr.unidad, pr.stock_almacen,
                      SUM(dp.cantidad) as total
               FROM detalle_pedido dp
               JOIN productos pr ON dp.producto_id=pr.id
               JOIN pedidos p ON dp.pedido_id=p.id
               GROUP BY pr.id ORDER BY total DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stock_bajo(umbral=5):
    """Productos con stock bajo el umbral o bajo su mínimo de reorden."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT * FROM productos
           WHERE activo=1 AND (stock_almacen <= ? OR stock_almacen <= minimo_reorden)
           ORDER BY stock_almacen ASC""",
        (umbral,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_consumo_por_area_periodo(ciclo_id=None):
    """Consumo desglosado por área y categoría."""
    conn = get_conn()
    if ciclo_id:
        rows = conn.execute(
            """SELECT a.nombre as area, pr.categoria,
                      SUM(dp.cantidad) as total
               FROM detalle_pedido dp
               JOIN pedidos p ON dp.pedido_id=p.id
               JOIN areas a ON p.area_id=a.id
               JOIN productos pr ON dp.producto_id=pr.id
               WHERE p.ciclo_id=?
               GROUP BY a.nombre, pr.categoria
               ORDER BY a.nombre, total DESC""",
            (ciclo_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT a.nombre as area, pr.categoria,
                      SUM(dp.cantidad) as total
               FROM detalle_pedido dp
               JOIN pedidos p ON dp.pedido_id=p.id
               JOIN areas a ON p.area_id=a.id
               JOIN productos pr ON dp.producto_id=pr.id
               GROUP BY a.nombre, pr.categoria
               ORDER BY a.nombre, total DESC""",
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
