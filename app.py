import os
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_file,
)
from database import (
    init_db, cargar_catalogo, asegurar_ciclo_activo,
    verificar_login, get_usuario, get_usuarios, crear_usuario,
    actualizar_usuario, eliminar_usuario,
    get_areas, get_productos, get_categorias,
    agregar_producto, actualizar_producto, eliminar_producto,
    get_ciclo_activo,
    crear_pedido, get_pedidos_usuario, get_pedidos_area_estado,
    get_pedidos_por_estado, get_todos_pedidos,
    get_detalle_pedido, actualizar_estado_pedido, borrar_pedido,
    contar_pendientes_area, contar_pendientes_admin,
    generar_excel_orden,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "proesa-inventario-dev-key-2026")

# ── Init ────────────────────────────────────────────────────────
init_db()
cargar_catalogo()
asegurar_ciclo_activo()


# ── Auth helpers ────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            user = get_usuario(session["user_id"])
            if not user or user["rol"] not in roles:
                flash("No tienes permiso para acceder a esta pagina.", "error")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated
    return decorator


@app.context_processor
def inject_user():
    """Make current user available in all templates."""
    user = None
    if "user_id" in session:
        user = get_usuario(session["user_id"])
    return dict(current_user=user)


# ── Login / Logout ──────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = verificar_login(username, password)
        if user:
            session["user_id"] = user["id"]
            flash(f"Bienvenido, {user['nombre']}", "success")
            return redirect(url_for("index"))
        flash("Usuario o contrasena incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Index (redirect by role) ───────────────────────────────────

@app.route("/")
@login_required
def index():
    user = get_usuario(session["user_id"])
    if user["rol"] == "admin":
        return redirect(url_for("admin_pedidos"))
    elif user["rol"] == "lider":
        return redirect(url_for("aprobar"))
    else:
        return redirect(url_for("nuevo_pedido"))


# ── Empleado: Nuevo Pedido ─────────────────────────────────────

@app.route("/nuevo-pedido", methods=["GET", "POST"])
@login_required
def nuevo_pedido():
    user = get_usuario(session["user_id"])
    if not user["area_id"]:
        flash("No tienes un area asignada. Contacta al administrador.", "error")
        return redirect(url_for("index"))

    ciclo = get_ciclo_activo()
    if not ciclo:
        flash("No hay un ciclo de pedidos abierto.", "error")
        return render_template("nuevo_pedido.html", productos_por_cat={}, ciclo=None)

    if request.method == "POST":
        items = []
        for key, val in request.form.items():
            if key.startswith("cant_") and val:
                try:
                    prod_id = int(key.replace("cant_", ""))
                    cant = int(val)
                    if cant > 0:
                        items.append((prod_id, cant))
                except ValueError:
                    pass
        notas = request.form.get("notas", "").strip()

        if not items:
            flash("Selecciona al menos un producto.", "error")
        else:
            pedido_id = crear_pedido(user["id"], user["area_id"], ciclo["id"], items, notas)
            flash(f"Pedido #{pedido_id} enviado. Tu lider lo revisara pronto.", "success")
            return redirect(url_for("mis_pedidos"))

    productos = get_productos()
    # Group by category
    productos_por_cat = {}
    for p in productos:
        cat = p["categoria"]
        if cat not in productos_por_cat:
            productos_por_cat[cat] = []
        productos_por_cat[cat].append(p)

    return render_template("nuevo_pedido.html", productos_por_cat=productos_por_cat, ciclo=ciclo)


# ── Empleado/Lider: Mis Pedidos ────────────────────────────────

@app.route("/mis-pedidos")
@login_required
def mis_pedidos():
    user = get_usuario(session["user_id"])
    pedidos = get_pedidos_usuario(user["id"])
    # Attach details
    for p in pedidos:
        p["detalles"] = get_detalle_pedido(p["id"])
    return render_template("mis_pedidos.html", pedidos=pedidos)


# ── Lider: Aprobar Pedidos ─────────────────────────────────────

@app.route("/aprobar")
@role_required("lider", "admin")
def aprobar():
    user = get_usuario(session["user_id"])
    if user["rol"] == "lider":
        if not user["area_id"]:
            flash("No tienes area asignada.", "error")
            return redirect(url_for("index"))
        pedidos = get_pedidos_area_estado(user["area_id"], "pendiente")
        titulo = "Pedidos pendientes de tu area"
    else:
        # Admin can also see this view
        pedidos = get_pedidos_por_estado("pendiente")
        titulo = "Todos los pedidos pendientes (lider)"

    for p in pedidos:
        p["detalles"] = get_detalle_pedido(p["id"])

    n_pendientes = len(pedidos)
    return render_template("aprobar.html", pedidos=pedidos, titulo=titulo,
                           n_pendientes=n_pendientes, nivel="lider")


@app.route("/aprobar/<int:pedido_id>", methods=["POST"])
@role_required("lider", "admin")
def aprobar_accion(pedido_id):
    accion = request.form.get("accion")
    if accion == "aprobar":
        actualizar_estado_pedido(pedido_id, "aprobado_lider")
        flash(f"Pedido #{pedido_id} aprobado.", "success")
    elif accion == "rechazar":
        actualizar_estado_pedido(pedido_id, "rechazado")
        flash(f"Pedido #{pedido_id} rechazado.", "warning")

    user = get_usuario(session["user_id"])
    if user["rol"] == "admin":
        return redirect(url_for("admin_pedidos"))
    return redirect(url_for("aprobar"))


# ── Admin: Pedidos ──────────────────────────────────────────────

@app.route("/admin/pedidos")
@role_required("admin")
def admin_pedidos():
    filtro = request.args.get("filtro", "aprobado_lider")
    if filtro == "todos":
        pedidos = get_todos_pedidos()
    else:
        pedidos = get_pedidos_por_estado(filtro)

    for p in pedidos:
        p["detalles"] = get_detalle_pedido(p["id"])

    n_admin = contar_pendientes_admin()
    return render_template("admin_pedidos.html", pedidos=pedidos, filtro=filtro, n_admin=n_admin)


@app.route("/admin/pedidos/<int:pedido_id>", methods=["POST"])
@role_required("admin")
def admin_pedido_accion(pedido_id):
    accion = request.form.get("accion")
    if accion == "aprobar":
        actualizar_estado_pedido(pedido_id, "aprobado")
        flash(f"Pedido #{pedido_id} aprobado.", "success")
    elif accion == "rechazar":
        actualizar_estado_pedido(pedido_id, "rechazado")
        flash(f"Pedido #{pedido_id} rechazado.", "warning")
    elif accion == "entregar":
        actualizar_estado_pedido(pedido_id, "entregado")
        flash(f"Pedido #{pedido_id} marcado como entregado.", "success")
    elif accion == "eliminar":
        borrar_pedido(pedido_id)
        flash(f"Pedido #{pedido_id} eliminado.", "warning")
    return redirect(url_for("admin_pedidos"))


# ── Admin: Exportar Excel ──────────────────────────────────────

@app.route("/admin/exportar", methods=["GET", "POST"])
@role_required("admin")
def admin_exportar():
    pedidos_aprobados = get_pedidos_por_estado("aprobado")
    for p in pedidos_aprobados:
        p["detalles"] = get_detalle_pedido(p["id"])

    if request.method == "POST":
        ids = request.form.getlist("pedido_ids")
        no_inv = request.form.get("no_inventario", "GA-GE-OF-00001").strip()
        if not ids:
            flash("Selecciona al menos un pedido para exportar.", "error")
            return redirect(url_for("admin_exportar"))

        pedido_ids = [int(i) for i in ids]
        buf = generar_excel_orden(pedido_ids, no_inv)
        return send_file(
            buf,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"Orden_Compra_{no_inv}.xlsx",
        )

    return render_template("exportar.html", pedidos=pedidos_aprobados)


# ── Admin: Catalogo ─────────────────────────────────────────────

@app.route("/admin/catalogo")
@role_required("admin")
def admin_catalogo():
    productos = get_productos(solo_activos=False)
    productos_por_cat = {}
    for p in productos:
        cat = p["categoria"]
        if cat not in productos_por_cat:
            productos_por_cat[cat] = []
        productos_por_cat[cat].append(p)
    return render_template("catalogo.html", productos_por_cat=productos_por_cat)


@app.route("/admin/catalogo/agregar", methods=["POST"])
@role_required("admin")
def admin_catalogo_agregar():
    nombre = request.form.get("nombre", "").strip()
    categoria = request.form.get("categoria", "General").strip()
    unidad = request.form.get("unidad", "PIEZA").strip()
    if nombre:
        agregar_producto(nombre, categoria, unidad)
        flash(f"'{nombre}' agregado al catalogo.", "success")
    else:
        flash("El nombre es obligatorio.", "error")
    return redirect(url_for("admin_catalogo"))


@app.route("/admin/catalogo/eliminar/<int:prod_id>", methods=["POST"])
@role_required("admin")
def admin_catalogo_eliminar(prod_id):
    eliminar_producto(prod_id)
    flash("Producto desactivado.", "warning")
    return redirect(url_for("admin_catalogo"))


# ── Admin: Usuarios ─────────────────────────────────────────────

@app.route("/admin/usuarios")
@role_required("admin")
def admin_usuarios():
    usuarios = get_usuarios()
    areas = get_areas()
    return render_template("usuarios.html", usuarios=usuarios, areas=areas)


@app.route("/admin/usuarios/crear", methods=["POST"])
@role_required("admin")
def admin_usuario_crear():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    nombre = request.form.get("nombre", "").strip()
    rol = request.form.get("rol", "empleado")
    area_id = request.form.get("area_id")
    area_id = int(area_id) if area_id else None

    if not username or not password or not nombre:
        flash("Todos los campos son obligatorios.", "error")
    elif crear_usuario(username, password, nombre, rol, area_id):
        flash(f"Usuario '{username}' creado.", "success")
    else:
        flash(f"El usuario '{username}' ya existe.", "error")
    return redirect(url_for("admin_usuarios"))


@app.route("/admin/usuarios/editar/<int:user_id>", methods=["POST"])
@role_required("admin")
def admin_usuario_editar(user_id):
    nombre = request.form.get("nombre", "").strip()
    rol = request.form.get("rol", "empleado")
    area_id = request.form.get("area_id")
    area_id = int(area_id) if area_id else None
    activo = 1 if request.form.get("activo") else 0
    password = request.form.get("password", "").strip() or None

    actualizar_usuario(user_id, nombre, rol, area_id, activo, password)
    flash("Usuario actualizado.", "success")
    return redirect(url_for("admin_usuarios"))


@app.route("/admin/usuarios/eliminar/<int:user_id>", methods=["POST"])
@role_required("admin")
def admin_usuario_eliminar(user_id):
    eliminar_usuario(user_id)
    flash("Usuario desactivado.", "warning")
    return redirect(url_for("admin_usuarios"))


# ── Run ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8502))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug,
            extra_files=None, exclude_patterns=["*.pyc", "*.db", "*.xlsx"])
