import sqlite3
import os
import shutil
import calendar
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")

CICLO_DIAS = 30  # Referencia visual (ciclos son mensuales)


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
    """Carga el catálogo oficial de Papelería PROESA."""
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    if count > 0:
        conn.close()
        return False  # Ya hay productos

    productos = [
        # Papelería
        ("Block de vales naranja", "Papelería", "pieza", 0),
        ("Block de vales azules", "Papelería", "pieza", 0),
        ("Folder tamaño carta beige", "Papelería", "pieza", 0),
        ("Folder tamaño oficio azul", "Papelería", "pieza", 0),
        ("Mica pliego", "Papelería", "pieza", 0),
        ("Protector de hojas tamaño carta", "Papelería", "paquete", 0),
        ("Sobre para efectivo", "Papelería", "pieza", 0),

        # Escritura
        ("Bolígrafo tinta azul", "Escritura", "pieza", 0),
        ("Bolígrafo tinta negra", "Escritura", "pieza", 0),
        ("Bolígrafo tinta roja", "Escritura", "pieza", 0),
        ("Bolígrafo tinta verde", "Escritura", "pieza", 0),
        ("Goma", "Escritura", "pieza", 0),
        ("Lápiz", "Escritura", "pieza", 0),
        ("Marca textos amarillo", "Escritura", "pieza", 0),
        ("Marca textos azul", "Escritura", "pieza", 0),
        ("Marca textos naranja", "Escritura", "pieza", 0),
        ("Marca textos rosa", "Escritura", "pieza", 0),
        ("Marca textos verde", "Escritura", "pieza", 0),
        ("Plumón punto fino azul", "Escritura", "pieza", 0),
        ("Plumón punto fino negro", "Escritura", "pieza", 0),
        ("Plumón punto fino rojo", "Escritura", "pieza", 0),
        ("Plumones lavables para pizarrón", "Escritura", "paquete", 0),
        ("Sacapuntas", "Escritura", "pieza", 0),

        # Sujetadores
        ("Clip #2", "Sujetadores", "caja", 0),
        ("Clip tipo mariposa", "Sujetadores", "caja", 0),
        ("Grapas", "Sujetadores", "caja", 0),

        # Adhesivos
        ("Diurex", "Adhesivos", "pieza", 0),
        ("Lápiz adhesivo", "Adhesivos", "pieza", 0),
        ("Pegamento Kola loka", "Adhesivos", "pieza", 0),

        # Herramientas
        ("Cutter", "Herramientas", "pieza", 0),
        ("Engrapadora", "Herramientas", "pieza", 0),
        ("Quita grapas", "Herramientas", "pieza", 0),
        ("Tijeras", "Herramientas", "pieza", 0),

        # Pilas
        ("Pilas AA", "Pilas", "paquete", 0),
        ("Pilas AAA", "Pilas", "paquete", 0),
        ("Pilas Cuadrada", "Pilas", "pieza", 0),
        ("Pilas D", "Pilas", "pieza", 0),

        # Protección
        ("Manga plástica cubre polvo", "Protección", "pieza", 0),

        # Varios
        ("Papel aluminio rollo", "Varios", "rollo", 0),
        ("Porta gafete cordón retráctil", "Varios", "pieza", 0),
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
    """Crea automáticamente un nuevo ciclo mensual si no hay uno abierto."""
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
        # Ciclo mensual: del 1 al último día del mes actual
        inicio = hoy.replace(day=1).strftime("%Y-%m-%d")
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
        cierre = hoy.replace(day=ultimo_dia).strftime("%Y-%m-%d")

        meses_es = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
        }
        mes = f"{meses_es[hoy.month]} {hoy.year}"
        nombre = f"{mes}"

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
