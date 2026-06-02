import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import (
    init_db, cargar_catalogo_ejemplo, asegurar_ciclo_activo, backup_db,
    get_areas, get_productos, get_categorias, agregar_producto,
    actualizar_producto, actualizar_stock, agregar_productos_masivo,
    get_ciclo_activo, get_ciclos, crear_ciclo, cerrar_ciclo,
    crear_pedido, get_pedidos_area, get_detalle_pedido, get_todos_pedidos,
    actualizar_estado_pedido, entregar_pedido, contar_pedidos_pendientes,
    get_inventario_area, get_resumen_por_area, get_productos_mas_pedidos,
    get_stock_bajo, get_consumo_por_area_periodo,
    actualizar_lider, get_log_actividad, log_actividad,
    CICLO_DIAS,
)

st.set_page_config(
    page_title="Inventario Almacén",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Init ---
init_db()
cargar_catalogo_ejemplo()
asegurar_ciclo_activo()

# --- Estilos mobile-first ---
st.markdown("""
<style>
    .block-container { max-width: 520px; padding: 0.8rem 1rem; }
    h1, h2, h3 { margin-top: 0.5rem !important; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
    div[data-testid="stMetricLabel"] { font-size: 0.8rem; color: #666; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { padding: 6px 12px; font-size: 0.85rem; }

    .pedido-urgente { border-left: 4px solid #e74c3c !important; }
    .badge {
        display: inline-block; padding: 2px 8px; border-radius: 12px;
        font-size: 0.75rem; font-weight: 600; color: white;
    }
    .badge-pendiente { background: #f39c12; }
    .badge-aprobado { background: #3498db; }
    .badge-entregado { background: #27ae60; }
    .badge-rechazado { background: #e74c3c; }

    .area-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 16px; border-radius: 12px; margin-bottom: 16px;
        text-align: center;
    }
    .admin-header {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white; padding: 16px; border-radius: 12px; margin-bottom: 16px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("## 📦 Sistema de Inventario")
st.caption("Requisiciones de Almacén")

# --- Selección de rol ---
areas = get_areas()
area_nombres = [a["nombre"] for a in areas]

pendientes = contar_pedidos_pendientes()
admin_label = f"🔧 Almacén ({pendientes} pendientes)" if pendientes else "🔧 Almacén"

rol = st.radio(
    "Selecciona tu rol",
    ["👤 Líder de Área", admin_label],
    horizontal=True,
    label_visibility="collapsed",
)
is_admin = "Almacén" in rol

st.divider()

# =====================================================
# VISTA LÍDER DE ÁREA
# =====================================================
if not is_admin:
    area_sel = st.selectbox("Tu área", area_nombres)
    area = next(a for a in areas if a["nombre"] == area_sel)
    area_id = area["id"]
    emoji = area.get("emoji", "🏢")

    st.markdown(
        f'<div class="area-header">{emoji} <b>{area_sel}</b><br>'
        f'<small>Líder: {area["lider"] or "Sin asignar"}</small></div>',
        unsafe_allow_html=True,
    )

    # KPIs del área
    pedidos_area = get_pedidos_area(area_id)
    inv = get_inventario_area(area_id)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Pedidos", len(pedidos_area))
    with c2:
        pend = len([p for p in pedidos_area if p["estado"] == "pendiente"])
        st.metric("Pendientes", pend)
    with c3:
        st.metric("Productos", len(inv))

    tab1, tab2, tab3 = st.tabs(["🛒 Nuevo Pedido", "📋 Mis Pedidos", "📊 Mi Inventario"])

    # --- NUEVO PEDIDO ---
    with tab1:
        ciclo = get_ciclo_activo()
        if not ciclo:
            st.warning("No hay un ciclo de pedidos abierto.")
        else:
            dias_restantes = (datetime.strptime(ciclo["fecha_cierre"], "%Y-%m-%d") - datetime.now()).days
            if dias_restantes <= 3:
                st.warning(f"⚠️ **{ciclo['nombre']}** — Cierra en **{max(0, dias_restantes)} días**. ¡Apúrate!")
            else:
                st.info(f"**{ciclo['nombre']}** — Cierra en **{dias_restantes} días**")

            productos = get_productos()
            if not productos:
                st.warning("El catálogo está vacío. Espera a que el administrador cargue los productos.")
            else:
                # Búsqueda rápida
                buscar = st.text_input("🔍 Buscar producto", placeholder="Ej: pluma, tóner, café...")

                categorias = sorted(set(p["categoria"] for p in productos))
                items_pedido = []

                for cat in categorias:
                    prods_cat = [p for p in productos if p["categoria"] == cat]
                    if buscar:
                        prods_cat = [p for p in prods_cat if buscar.lower() in p["nombre"].lower()]
                    if not prods_cat:
                        continue

                    with st.expander(f"📁 {cat} ({len(prods_cat)})", expanded=bool(buscar)):
                        for p in prods_cat:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                stock_txt = f"Stock: {p['stock_almacen']}"
                                if p["stock_almacen"] <= 5:
                                    stock_txt = f"⚠️ Poco stock: {p['stock_almacen']}"
                                st.markdown(f"**{p['nombre']}**")
                                st.caption(f"{p['unidad']} | {stock_txt}")
                            with col2:
                                cant = st.number_input(
                                    "Cant",
                                    min_value=0,
                                    max_value=999,
                                    value=0,
                                    key=f"prod_{p['id']}",
                                    label_visibility="collapsed",
                                )
                                if cant > 0:
                                    items_pedido.append((p["id"], cant))

                st.divider()

                prioridad = st.radio(
                    "Prioridad", ["Normal", "Urgente 🔴"], horizontal=True
                )
                notas = st.text_area("Notas (opcional)", placeholder="Ej: Para evento del viernes")

                if items_pedido:
                    st.success(f"**{len(items_pedido)} producto(s)** seleccionados")
                    if st.button("📤 Enviar Pedido", type="primary", use_container_width=True):
                        prio = "urgente" if "Urgente" in prioridad else "normal"
                        pedido_id = crear_pedido(area_id, ciclo["id"], items_pedido, notas, prio)
                        st.balloons()
                        st.success(f"✅ Pedido #{pedido_id} enviado correctamente")
                        st.rerun()
                else:
                    st.caption("Selecciona al menos un producto para hacer tu pedido.")

    # --- MIS PEDIDOS ---
    with tab2:
        if not pedidos_area:
            st.info("No tienes pedidos registrados aún.")
        else:
            # Filtro por estado
            filtro_estado = st.selectbox(
                "Filtrar", ["Todos", "Pendientes", "Aprobados", "Entregados", "Rechazados"],
                key="filtro_mis_pedidos",
            )
            pedidos_filtrados = pedidos_area
            if filtro_estado != "Todos":
                estado_map = {"Pendientes": "pendiente", "Aprobados": "aprobado",
                              "Entregados": "entregado", "Rechazados": "rechazado"}
                pedidos_filtrados = [p for p in pedidos_area if p["estado"] == estado_map[filtro_estado]]

            for ped in pedidos_filtrados:
                estado = ped["estado"]
                emoji_st = {"pendiente": "🟡", "aprobado": "🔵", "entregado": "🟢", "rechazado": "🔴"}.get(estado, "⚪")
                urgente = " 🔴 URGENTE" if ped.get("prioridad") == "urgente" else ""

                with st.expander(f"{emoji_st} Pedido #{ped['id']} — {estado.upper()}{urgente} | {ped['fecha_pedido'][:10]}"):
                    st.caption(f"Ciclo: {ped['ciclo_nombre']}")
                    if ped["notas"]:
                        st.markdown(f"📝 *{ped['notas']}*")
                    detalles = get_detalle_pedido(ped["id"])
                    for d in detalles:
                        check = "✅" if d["cantidad_entregada"] else "⬜"
                        st.markdown(f"{check} {d['producto_nombre']}: **{d['cantidad']}** {d['unidad']}")

    # --- MI INVENTARIO ---
    with tab3:
        if not inv:
            st.info("Tu área no tiene inventario registrado aún. Aparecerá cuando te entreguen pedidos.")
        else:
            total = sum(i["cantidad"] for i in inv)
            st.metric("Total items en tu área", total)
            df = pd.DataFrame(inv)[["producto_nombre", "cantidad", "unidad", "categoria", "ultima_actualizacion"]]
            df.columns = ["Producto", "Cant.", "Unidad", "Categoría", "Última Entrega"]
            st.dataframe(df, use_container_width=True, hide_index=True)


# =====================================================
# VISTA ADMIN (ALMACÉN)
# =====================================================
else:
    st.markdown(
        '<div class="admin-header">🔧 <b>Panel de Almacén</b><br>'
        '<small>Administración de inventario y pedidos</small></div>',
        unsafe_allow_html=True,
    )

    # Alertas
    pendientes_list = get_todos_pedidos(estado="pendiente")
    stock_bajo = get_stock_bajo()

    if pendientes_list:
        urgentes = [p for p in pendientes_list if p.get("prioridad") == "urgente"]
        if urgentes:
            st.error(f"🚨 **{len(urgentes)} pedido(s) URGENTE(S)** por atender")
        if len(pendientes_list) - len(urgentes) > 0:
            st.warning(f"📬 **{len(pendientes_list) - len(urgentes)}** pedido(s) pendiente(s)")
    if stock_bajo:
        st.warning(f"📉 **{len(stock_bajo)}** producto(s) con stock bajo")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📊 Dashboard", "📋 Pedidos", "📦 Catálogo", "🔄 Ciclos", "⚙️ Áreas", "📜 Log"]
    )

    # --- DASHBOARD ---
    with tab1:
        ciclo = get_ciclo_activo()
        ciclos_todos = get_ciclos()

        filtro_ciclo = None
        if ciclos_todos:
            ciclo_filtro = st.selectbox(
                "Filtrar por ciclo",
                ["Todos"] + [c["nombre"] for c in ciclos_todos],
            )
            if ciclo_filtro != "Todos":
                filtro_ciclo = next(c["id"] for c in ciclos_todos if c["nombre"] == ciclo_filtro)

        if ciclo:
            dias = (datetime.strptime(ciclo["fecha_cierre"], "%Y-%m-%d") - datetime.now()).days
            st.info(f"**Ciclo activo:** {ciclo['nombre']} — {max(0, dias)} días restantes")

        resumen = get_resumen_por_area(filtro_ciclo)

        # KPIs
        c1, c2 = st.columns(2)
        total_pedidos = sum(r["total_pedidos"] or 0 for r in resumen)
        total_items = sum(r["total_items"] or 0 for r in resumen)
        with c1:
            st.metric("Total Pedidos", total_pedidos)
        with c2:
            st.metric("Total Items", int(total_items))

        c3, c4 = st.columns(2)
        total_ent = sum(r["entregados"] or 0 for r in resumen)
        total_pend = sum(r["pendientes"] or 0 for r in resumen)
        with c3:
            st.metric("Entregados", int(total_ent))
        with c4:
            st.metric("Pendientes", int(total_pend))

        # Tabla por área
        st.markdown("### 📈 Consumo por Área")
        if any(r["total_pedidos"] for r in resumen):
            df_r = pd.DataFrame(resumen)
            df_r["area"] = df_r["emoji"] + " " + df_r["area"]
            df_r = df_r[df_r["total_pedidos"] > 0].sort_values("total_items", ascending=False)
            df_show = df_r[["area", "total_pedidos", "total_items", "entregados", "pendientes"]].copy()
            df_show.columns = ["Área", "Pedidos", "Items", "Entregados", "Pendientes"]
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            # Gráfica
            chart_data = df_r.set_index("area")[["total_items"]].rename(columns={"total_items": "Items pedidos"})
            st.bar_chart(chart_data)
        else:
            st.info("No hay pedidos aún en este período.")

        # Top productos
        st.markdown("### 🏆 Productos más pedidos")
        top = get_productos_mas_pedidos(filtro_ciclo)
        if top:
            df_top = pd.DataFrame(top)
            df_top.columns = ["Producto", "Categoría", "Unidad", "Stock", "Total Pedido"]
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos aún.")

        # Stock bajo
        if stock_bajo:
            st.markdown("### ⚠️ Stock bajo")
            for p in stock_bajo:
                st.markdown(f"- **{p['nombre']}** — Stock: **{p['stock_almacen']}** {p['unidad']}")

    # --- PEDIDOS ---
    with tab2:
        ciclos_todos = get_ciclos()
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro = None
            if ciclos_todos:
                sel = st.selectbox("Ciclo", ["Todos"] + [c["nombre"] for c in ciclos_todos], key="admin_ciclo")
                if sel != "Todos":
                    filtro = next(c["id"] for c in ciclos_todos if c["nombre"] == sel)
        with col_f2:
            estado_f = st.selectbox("Estado", ["Todos", "Pendientes", "Aprobados", "Entregados", "Rechazados"], key="admin_estado")

        estado_map = {"Pendientes": "pendiente", "Aprobados": "aprobado",
                      "Entregados": "entregado", "Rechazados": "rechazado"}
        estado_val = estado_map.get(estado_f, None)

        pedidos = get_todos_pedidos(filtro, estado_val)
        if not pedidos:
            st.info("No hay pedidos con estos filtros.")
        else:
            st.caption(f"{len(pedidos)} pedido(s)")
            for ped in pedidos:
                estado = ped["estado"]
                emoji_st = {"pendiente": "🟡", "aprobado": "🔵", "entregado": "🟢", "rechazado": "🔴"}.get(estado, "⚪")
                urgente = " 🔴" if ped.get("prioridad") == "urgente" else ""
                area_emoji = ped.get("area_emoji", "🏢")

                with st.expander(
                    f"{emoji_st}{urgente} #{ped['id']} | {area_emoji} {ped['area_nombre']} | {estado.upper()} | {ped['fecha_pedido'][:10]}"
                ):
                    st.caption(f"Ciclo: {ped['ciclo_nombre']}")
                    if ped.get("prioridad") == "urgente":
                        st.error("🔴 PEDIDO URGENTE")
                    if ped["notas"]:
                        st.markdown(f"📝 *{ped['notas']}*")

                    detalles = get_detalle_pedido(ped["id"])
                    for d in detalles:
                        st.markdown(f"- {d['producto_nombre']}: **{d['cantidad']}** {d['unidad']}")

                    if estado == "pendiente":
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button("✅ Aprobar", key=f"apr_{ped['id']}", use_container_width=True):
                                actualizar_estado_pedido(ped["id"], "aprobado")
                                st.rerun()
                        with c2:
                            if st.button("📦 Entregar", key=f"ent_{ped['id']}", use_container_width=True):
                                entregar_pedido(ped["id"])
                                st.success("Entregado y stock actualizado")
                                st.rerun()
                        with c3:
                            if st.button("❌ Rechazar", key=f"rej_{ped['id']}", use_container_width=True):
                                actualizar_estado_pedido(ped["id"], "rechazado")
                                st.rerun()
                    elif estado == "aprobado":
                        if st.button("📦 Marcar Entregado", key=f"entd_{ped['id']}", use_container_width=True):
                            entregar_pedido(ped["id"])
                            st.success("Entregado y stock actualizado")
                            st.rerun()

    # --- CATÁLOGO ---
    with tab3:
        st.markdown("### 📦 Catálogo de Productos")
        productos = get_productos(solo_activos=False)

        # Stats
        activos = len([p for p in productos if p["activo"]])
        cats = len(set(p["categoria"] for p in productos))
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Productos activos", activos)
        with c2:
            st.metric("Categorías", cats)

        # Carga masiva
        with st.expander("📤 Cargar catálogo desde Excel/CSV"):
            st.markdown("""
            Sube un archivo Excel o CSV con estas columnas:
            - **nombre** — Nombre del producto
            - **categoria** — Categoría (ej: Papelería, Limpieza)
            - **unidad** — pieza, paquete, caja, etc.
            - **stock** — Cantidad en almacén
            """)
            archivo = st.file_uploader("Selecciona archivo", type=["xlsx", "csv"], key="carga_masiva")
            if archivo:
                try:
                    if archivo.name.endswith(".csv"):
                        df_carga = pd.read_csv(archivo)
                    else:
                        df_carga = pd.read_excel(archivo)

                    cols_requeridas = ["nombre"]
                    if not all(c in df_carga.columns for c in cols_requeridas):
                        st.error("El archivo debe tener al menos la columna 'nombre'")
                    else:
                        if "categoria" not in df_carga.columns:
                            df_carga["categoria"] = "General"
                        if "unidad" not in df_carga.columns:
                            df_carga["unidad"] = "pieza"
                        if "stock" not in df_carga.columns:
                            df_carga["stock"] = 0

                        st.dataframe(df_carga.head(10), use_container_width=True, hide_index=True)
                        st.caption(f"{len(df_carga)} productos encontrados")

                        if st.button("✅ Cargar productos", type="primary", use_container_width=True):
                            items = [
                                (row["nombre"], row["categoria"], row["unidad"], int(row["stock"]))
                                for _, row in df_carga.iterrows()
                                if pd.notna(row["nombre"]) and str(row["nombre"]).strip()
                            ]
                            count = agregar_productos_masivo(items)
                            st.success(f"✅ {count} productos cargados")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error al leer archivo: {e}")

        # Agregar individual
        with st.expander("➕ Agregar producto"):
            with st.form("nuevo_prod"):
                nombre = st.text_input("Nombre del producto")
                col1, col2 = st.columns(2)
                with col1:
                    cats_existentes = get_categorias()
                    if cats_existentes:
                        cat_sel = st.selectbox("Categoría existente", ["(Nueva)"] + cats_existentes)
                    else:
                        cat_sel = "(Nueva)"
                with col2:
                    if cat_sel == "(Nueva)":
                        categoria = st.text_input("Nombre categoría", value="General")
                    else:
                        categoria = cat_sel
                        st.text_input("Categoría", value=cat_sel, disabled=True)

                c1, c2 = st.columns(2)
                with c1:
                    unidad = st.selectbox("Unidad", ["pieza", "paquete", "caja", "resma", "rollo",
                                                      "bote", "bolsa", "litro", "kilo"])
                with c2:
                    stock = st.number_input("Stock", min_value=0, value=0)

                if st.form_submit_button("Agregar", use_container_width=True):
                    if nombre.strip():
                        agregar_producto(nombre.strip(), categoria.strip(), unidad, stock)
                        st.success(f"Producto '{nombre}' agregado")
                        st.rerun()
                    else:
                        st.error("El nombre es obligatorio")

        # Lista de productos
        if productos:
            buscar_prod = st.text_input("🔍 Buscar en catálogo", key="buscar_cat")
            cats_list = sorted(set(p["categoria"] for p in productos))
            for cat in cats_list:
                prods_cat = [p for p in productos if p["categoria"] == cat]
                if buscar_prod:
                    prods_cat = [p for p in prods_cat if buscar_prod.lower() in p["nombre"].lower()]
                if not prods_cat:
                    continue

                with st.expander(f"📁 {cat} ({len(prods_cat)})"):
                    for p in prods_cat:
                        estado_txt = "✅" if p["activo"] else "❌"
                        stock_warn = " ⚠️" if p["stock_almacen"] <= 5 and p["activo"] else ""
                        st.markdown(f"{estado_txt} **{p['nombre']}** — {p['stock_almacen']} {p['unidad']}{stock_warn}")

                        with st.popover(f"✏️ Editar", use_container_width=True):
                            n = st.text_input("Nombre", value=p["nombre"], key=f"n_{p['id']}")
                            cc1, cc2 = st.columns(2)
                            with cc1:
                                ct = st.text_input("Categoría", value=p["categoria"], key=f"cat_{p['id']}")
                            with cc2:
                                unidades = ["pieza", "paquete", "caja", "resma", "rollo", "bote", "bolsa", "litro", "kilo"]
                                idx = unidades.index(p["unidad"]) if p["unidad"] in unidades else 0
                                un = st.selectbox("Unidad", unidades, index=idx, key=f"uni_{p['id']}")
                            s = st.number_input("Stock", min_value=0, value=p["stock_almacen"], key=f"s_{p['id']}")
                            act = st.checkbox("Activo", value=bool(p["activo"]), key=f"act_{p['id']}")
                            if st.button("Guardar", key=f"save_{p['id']}", use_container_width=True):
                                actualizar_producto(p["id"], n, ct, un, s, int(act))
                                st.rerun()
        else:
            st.info("No hay productos. Carga el catálogo de Jorge Alvarez arriba.")

    # --- CICLOS ---
    with tab4:
        st.markdown("### 🔄 Ciclos de Pedido")
        st.caption(f"Duración estándar: {CICLO_DIAS} días")

        ciclo_activo = get_ciclo_activo()

        if ciclo_activo:
            dias = (datetime.strptime(ciclo_activo["fecha_cierre"], "%Y-%m-%d") - datetime.now()).days
            progreso = max(0, min(1.0, 1 - (dias / CICLO_DIAS)))
            st.success(f"**Ciclo activo:** {ciclo_activo['nombre']}")
            st.progress(progreso, text=f"{max(0, dias)} días restantes de {CICLO_DIAS}")

            if st.button("🔒 Cerrar ciclo actual", use_container_width=True):
                cerrar_ciclo(ciclo_activo["id"])
                st.success("Ciclo cerrado. Se creará uno nuevo automáticamente.")
                asegurar_ciclo_activo()
                st.rerun()

        with st.expander("➕ Crear ciclo manual"):
            with st.form("nuevo_ciclo"):
                hoy = datetime.now()
                ultimo_num = len(get_ciclos())
                nombre_ciclo = st.text_input("Nombre", value=f"Ciclo #{ultimo_num + 1} — {hoy.strftime('%B %Y')}")
                c1, c2 = st.columns(2)
                with c1:
                    f_inicio = st.date_input("Inicio", value=hoy)
                with c2:
                    f_cierre = st.date_input("Cierre", value=hoy + timedelta(days=CICLO_DIAS))

                if st.form_submit_button("Crear", type="primary", use_container_width=True):
                    crear_ciclo(nombre_ciclo, ultimo_num + 1,
                                f_inicio.strftime("%Y-%m-%d"), f_cierre.strftime("%Y-%m-%d"))
                    st.success(f"Ciclo '{nombre_ciclo}' creado")
                    st.rerun()

        st.markdown("### Historial")
        for c in get_ciclos():
            emoji_c = "🟢" if c["estado"] == "abierto" else "⚫"
            st.markdown(
                f"{emoji_c} **{c['nombre']}** | {c['fecha_inicio']} → {c['fecha_cierre']} | {c['estado'].upper()}"
            )

    # --- ÁREAS ---
    with tab5:
        st.markdown("### 🏢 Áreas y Líderes")
        for a in areas:
            emoji_a = a.get("emoji", "🏢")
            with st.expander(f"{emoji_a} {a['nombre']}"):
                lider = st.text_input(
                    "Líder", value=a["lider"] or "", key=f"lider_{a['id']}",
                    placeholder="Nombre del líder",
                )
                if st.button("Guardar", key=f"save_l_{a['id']}", use_container_width=True):
                    actualizar_lider(a["id"], lider)
                    st.success(f"Líder actualizado")
                    st.rerun()

                inv = get_inventario_area(a["id"])
                if inv:
                    st.markdown("**Inventario:**")
                    for item in inv:
                        st.markdown(f"- {item['producto_nombre']}: {item['cantidad']} {item['unidad']}")
                else:
                    st.caption("Sin inventario registrado")

    # --- LOG ---
    with tab6:
        st.markdown("### 📜 Actividad Reciente")
        logs = get_log_actividad(30)
        if logs:
            for lg in logs:
                area_txt = f" [{lg['area']}]" if lg.get("area") else ""
                st.markdown(f"**{lg['fecha'][:16]}**{area_txt} — {lg['accion']}")
                if lg.get("detalle"):
                    st.caption(lg["detalle"])
        else:
            st.info("No hay actividad registrada.")

        st.divider()
        if st.button("💾 Respaldar Base de Datos", use_container_width=True):
            path = backup_db()
            if path:
                st.success(f"Respaldo creado: {path}")

# --- Footer ---
st.divider()
st.caption("Sistema de Inventario y Requisiciones — Almacén v2.0")
