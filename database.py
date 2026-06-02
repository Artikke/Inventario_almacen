import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "inventario.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        lider TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL DEFAULT 'General',
        unidad TEXT NOT NULL DEFAULT 'pieza',
        stock_almacen INTEGER NOT NULL DEFAULT 0,
        activo INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS ciclos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
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
    """)

    areas = [
        ("Talento Humano", ""),
        ("Mesa de Atención al Cliente", ""),
        ("Contabilidad", ""),
        ("Finanzas", ""),
        ("Crédito y Cobranza", ""),
        ("Abastecimiento y Compras", ""),
        ("Tecnología de Información (TI)", ""),
        ("Business Intelligence (BI)", ""),
    ]
    for nombre, lider in areas:
        conn.execute(
            "INSERT OR IGNORE INTO areas (nombre, lider) VALUES (?, ?)",
            (nombre, lider),
        )

    conn.commit()
    conn.close()


# --- Productos ---

def get_productos(solo_activos=True):
    conn = get_conn()
    if solo_activos:
        rows = conn.execute("SELECT * FROM productos WHERE activo=1 ORDER BY categoria, nombre").fetchall()
    else:
        rows = conn.execute("SELECT * FROM productos ORDER BY categoria, nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def agregar_producto(nombre, categoria, unidad, stock):
    conn = get_conn()
    conn.execute(
        "INSERT INTO productos (nombre, categoria, unidad, stock_almacen) VALUES (?, ?, ?, ?)",
        (nombre, categoria, unidad, stock),
    )
    conn.commit()
    conn.close()


def actualizar_producto(prod_id, nombre, categoria, unidad, stock, activo):
    conn = get_conn()
    conn.execute(
        "UPDATE productos SET nombre=?, categoria=?, unidad=?, stock_almacen=?, activo=? WHERE id=?",
        (nombre, categoria, unidad, stock, activo, prod_id),
    )
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


def crear_ciclo(nombre, fecha_inicio, fecha_cierre):
    conn = get_conn()
    conn.execute(
        "INSERT INTO ciclos (nombre, fecha_inicio, fecha_cierre) VALUES (?, ?, ?)",
        (nombre, fecha_inicio, fecha_cierre),
    )
    conn.commit()
    conn.close()


def cerrar_ciclo(ciclo_id):
    conn = get_conn()
    conn.execute("UPDATE ciclos SET estado='cerrado' WHERE id=?", (ciclo_id,))
    conn.commit()
    conn.close()


# --- Pedidos ---

def crear_pedido(area_id, ciclo_id, items, notas=""):
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO pedidos (area_id, ciclo_id, fecha_pedido, notas) VALUES (?, ?, ?, ?)",
        (area_id, ciclo_id, now, notas),
    )
    pedido_id = cur.lastrowid
    for producto_id, cantidad in items:
        conn.execute(
            "INSERT INTO detalle_pedido (pedido_id, producto_id, cantidad) VALUES (?, ?, ?)",
            (pedido_id, producto_id, cantidad),
        )
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


def get_todos_pedidos(ciclo_id=None):
    conn = get_conn()
    if ciclo_id:
        rows = conn.execute(
            """SELECT p.*, a.nombre as area_nombre, c.nombre as ciclo_nombre
               FROM pedidos p
               JOIN areas a ON p.area_id=a.id
               JOIN ciclos c ON p.ciclo_id=c.id
               WHERE p.ciclo_id=?
               ORDER BY p.fecha_pedido DESC""",
            (ciclo_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT p.*, a.nombre as area_nombre, c.nombre as ciclo_nombre
               FROM pedidos p
               JOIN areas a ON p.area_id=a.id
               JOIN ciclos c ON p.ciclo_id=c.id
               ORDER BY p.fecha_pedido DESC""",
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def actualizar_estado_pedido(pedido_id, estado):
    conn = get_conn()
    conn.execute("UPDATE pedidos SET estado=? WHERE id=?", (estado, pedido_id))
    conn.commit()
    conn.close()


def entregar_pedido(pedido_id):
    conn = get_conn()
    conn.execute("UPDATE pedidos SET estado='entregado' WHERE id=?", (pedido_id,))
    detalles = conn.execute(
        "SELECT producto_id, cantidad FROM detalle_pedido WHERE pedido_id=?",
        (pedido_id,),
    ).fetchall()
    pedido = conn.execute("SELECT area_id FROM pedidos WHERE id=?", (pedido_id,)).fetchone()
    area_id = pedido["area_id"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for d in detalles:
        conn.execute(
            """INSERT INTO inventario_area (area_id, producto_id, cantidad, ultima_actualizacion)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(area_id, producto_id)
               DO UPDATE SET cantidad=cantidad+?, ultima_actualizacion=?""",
            (area_id, d["producto_id"], d["cantidad"], now, d["cantidad"], now),
        )
        conn.execute(
            "UPDATE detalle_pedido SET cantidad_entregada=? WHERE pedido_id=? AND producto_id=?",
            (d["cantidad"], pedido_id, d["producto_id"]),
        )
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
    query = """
        SELECT a.nombre as area,
               COUNT(DISTINCT p.id) as total_pedidos,
               SUM(dp.cantidad) as total_items,
               SUM(CASE WHEN p.estado='entregado' THEN 1 ELSE 0 END) as entregados,
               SUM(CASE WHEN p.estado='pendiente' THEN 1 ELSE 0 END) as pendientes
        FROM areas a
        LEFT JOIN pedidos p ON a.id=p.area_id {}
        LEFT JOIN detalle_pedido dp ON p.id=dp.pedido_id
        GROUP BY a.id, a.nombre
        ORDER BY total_items DESC
    """.format("AND p.ciclo_id=?" if ciclo_id else "")

    if ciclo_id:
        rows = conn.execute(query, (ciclo_id,)).fetchall()
    else:
        rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_productos_mas_pedidos(ciclo_id=None, limit=10):
    conn = get_conn()
    query = """
        SELECT pr.nombre, pr.categoria, pr.unidad, SUM(dp.cantidad) as total
        FROM detalle_pedido dp
        JOIN productos pr ON dp.producto_id=pr.id
        JOIN pedidos p ON dp.pedido_id=p.id
        {}
        GROUP BY pr.id
        ORDER BY total DESC
        LIMIT ?
    """.format("WHERE p.ciclo_id=?" if ciclo_id else "")

    if ciclo_id:
        rows = conn.execute(query, (ciclo_id, limit)).fetchall()
    else:
        rows = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
