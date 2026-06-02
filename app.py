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
    page_title="PROESA - Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Init ---
init_db()
cargar_catalogo_ejemplo()
asegurar_ciclo_activo()

# --- CSS PROESA ---
st.markdown("""
<style>
    /* General */
    .block-container { padding: 1rem 2rem; max-width: 100%; }
    header[data-testid="stHeader"] { background: #1a5276; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a5276 0%, #154360 100%);
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 8px 12px;
        margin: 2px 0;
        transition: background 0.2s;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.2);
    }
    section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2); }

    /* KPI cards */
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #d4e6f1;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(26,82,118,0.08);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem; font-weight: 700; color: #1a5276;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem; color: #5d6d7e;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #eaf2f8; border-radius: 10px; padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #1a5276 !important; color: white !important;
    }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background: #1a5276; border: none; font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background: #154360;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: #f8fbfd; border-radius: 8px; font-weight: 500;
    }

    /* Tables */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* Logo header */
    .proesa-header {
        text-align: center; padding: 10px 0 5px 0;
    }
    .proesa-header img { width: 60px; margin-bottom: 4px; }
    .proesa-title {
        font-size: 1.1rem; font-weight: 700; color: white;
        letter-spacing: 2px; margin: 0;
    }
    .proesa-sub {
        font-size: 0.65rem; color: rgba(255,255,255,0.7);
        letter-spacing: 3px; margin: 0;
    }

    /* Page title */
    .page-title {
        color: #1a5276; font-size: 1.6rem; font-weight: 700;
        border-bottom: 3px solid #2e86c1; padding-bottom: 8px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
areas = get_areas()
area_nombres = [a["nombre"] for a in areas]
pendientes = contar_pedidos_pendientes()

with st.sidebar:
    # Logo
    st.markdown("""
    <div class="proesa-header">
        <p class="proesa-title">PROESA</p>
        <p class="proesa-sub">SOLUCIONES EN SALUD</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("##### Acceso")
    rol = st.radio(
        "Rol",
        ["Líder de Área", "Almacén (Admin)"],
        label_visibility="collapsed",
    )
    is_admin = "Admin" in rol

    if not is_admin:
        st.divider()
        st.markdown("##### Tu Área")
        area_sel = st.selectbox("Área", area_nombres, label_visibility="collapsed")
        area = next(a for a in areas if a["nombre"] == area_sel)
        area_id = area["id"]

    st.divider()
    ciclo = get_ciclo_activo()
    if ciclo:
        dias = (datetime.strptime(ciclo["fecha_cierre"], "%Y-%m-%d") - datetime.now()).days
        st.markdown(f"**Ciclo activo**")
        st.caption(f"{ciclo['nombre']}")
        st.progress(max(0, min(1.0, 1 - (dias / CICLO_DIAS))))
        st.caption(f"{max(0, dias)} días restantes")

    if pendientes and is_admin:
        st.divider()
        st.error(f"📬 {pendientes} pedido(s) pendiente(s)")


# =====================================================
# VISTA LÍDER DE ÁREA
# =====================================================
if not is_admin:
    emoji = area.get("emoji", "🏢")
    st.markdown(f'<div class="page-title">{emoji} {area_sel}</div>', unsafe_allow_html=True)

    # KPIs
    pedidos_area = get_pedidos_area(area_id)
    inv = get_inventario_area(area_id)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Pedidos", len(pedidos_area))
    with c2:
        st.metric("Pendientes", len([p for p in pedidos_area if p["estado"] == "pendiente"]))
    with c3:
        st.metric("Entregados", len([p for p in pedidos_area if p["estado"] == "entregado"]))
    with c4:
        st.metric("Items en Área", sum(i["cantidad"] for i in inv) if inv else 0)

    tab1, tab2, tab3 = st.tabs(["Nuevo Pedido", "Mis Pedidos", "Mi Inventario"])

    # --- NUEVO PEDIDO ---
    with tab1:
        if not ciclo:
            st.warning("No hay un ciclo de pedidos abierto.")
        else:
            productos = get_productos()
            if not productos:
                st.warning("El catálogo está vacío. Espera a que el administrador cargue los productos.")
            else:
                col_buscar, col_prio = st.columns([3, 1])
                with col_buscar:
                    buscar = st.text_input("Buscar producto", placeholder="Ej: pluma, tóner, café...")
                with col_prio:
                    prioridad = st.selectbox("Prioridad", ["Normal", "Urgente"])

                categorias = sorted(set(p["categoria"] for p in productos))
                items_pedido = []

                for cat in categorias:
                    prods_cat = [p for p in productos if p["categoria"] == cat]
                    if buscar:
                        prods_cat = [p for p in prods_cat if buscar.lower() in p["nombre"].lower()]
                    if not prods_cat:
                        continue

                    with st.expander(f"{cat} ({len(prods_cat)} productos)", expanded=bool(buscar)):
                        for p in prods_cat:
                            col1, col2, col3 = st.columns([4, 2, 1])
                            with col1:
                                st.markdown(f"**{p['nombre']}**")
                            with col2:
                                st.caption(f"{p['unidad']} | Stock: {p['stock_almacen']}")
                            with col3:
                                cant = st.number_input(
                                    "Cant", min_value=0, max_value=999, value=0,
                                    key=f"prod_{p['id']}", label_visibility="collapsed",
                                )
                                if cant > 0:
                                    items_pedido.append((p["id"], cant))

                notas = st.text_area("Notas (opcional)", placeholder="Ej: Necesario para evento del viernes")

                col_info, col_btn = st.columns([2, 1])
                with col_info:
                    if items_pedido:
                        st.success(f"**{len(items_pedido)} producto(s)** seleccionados")
                with col_btn:
                    if items_pedido:
                        if st.button("Enviar Pedido", type="primary", use_container_width=True):
                            prio = "urgente" if prioridad == "Urgente" else "normal"
                            pedido_id = crear_pedido(area_id, ciclo["id"], items_pedido, notas, prio)
                            st.balloons()
                            st.success(f"Pedido #{pedido_id} enviado")
                            st.rerun()

    # --- MIS PEDIDOS ---
    with tab2:
        if not pedidos_area:
            st.info("No tienes pedidos registrados aún.")
        else:
            filtro_estado = st.selectbox(
                "Filtrar", ["Todos", "Pendientes", "Aprobados", "Entregados", "Rechazados"],
                key="filtro_mis",
            )
            pedidos_f = pedidos_area
            if filtro_estado != "Todos":
                mapa = {"Pendientes": "pendiente", "Aprobados": "aprobado",
                        "Entregados": "entregado", "Rechazados": "rechazado"}
                pedidos_f = [p for p in pedidos_area if p["estado"] == mapa[filtro_estado]]

            for ped in pedidos_f:
                estado = ped["estado"]
                emoji_st = {"pendiente": "🟡", "aprobado": "🔵", "entregado": "🟢", "rechazado": "🔴"}.get(estado, "⚪")
                urg = " | URGENTE" if ped.get("prioridad") == "urgente" else ""

                with st.expander(f"{emoji_st} Pedido #{ped['id']} — {estado.upper()}{urg} | {ped['fecha_pedido'][:10]}"):
                    if ped["notas"]:
                        st.info(f"{ped['notas']}")
                    detalles = get_detalle_pedido(ped["id"])
                    df_det = pd.DataFrame(detalles)[["producto_nombre", "cantidad", "unidad", "cantidad_entregada"]]
                    df_det.columns = ["Producto", "Pedido", "Unidad", "Entregado"]
                    st.dataframe(df_det, use_container_width=True, hide_index=True)

    # --- MI INVENTARIO ---
    with tab3:
        if not inv:
            st.info("Tu área no tiene inventario registrado. Aparecerá cuando te entreguen pedidos.")
        else:
            df = pd.DataFrame(inv)[["producto_nombre", "cantidad", "unidad", "categoria", "ultima_actualizacion"]]
            df.columns = ["Producto", "Cantidad", "Unidad", "Categoría", "Última Entrega"]
            st.dataframe(df, use_container_width=True, hide_index=True)


# =====================================================
# VISTA ADMIN
# =====================================================
else:
    st.markdown('<div class="page-title">Panel de Almacén</div>', unsafe_allow_html=True)

    # Alertas
    pendientes_list = get_todos_pedidos(estado="pendiente")
    stock_bajo = get_stock_bajo()
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        if pendientes_list:
            urgentes = [p for p in pendientes_list if p.get("prioridad") == "urgente"]
            if urgentes:
                st.error(f"🚨 {len(urgentes)} pedido(s) URGENTE(S)")
    with col_a2:
        if stock_bajo:
            st.warning(f"📉 {len(stock_bajo)} producto(s) con stock bajo")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Dashboard", "Pedidos", "Catálogo", "Ciclos", "Áreas"]
    )

    # --- DASHBOARD ---
    with tab1:
        ciclos_todos = get_ciclos()
        filtro_ciclo = None
        if ciclos_todos:
            ciclo_f = st.selectbox("Filtrar por ciclo", ["Todos"] + [c["nombre"] for c in ciclos_todos])
            if ciclo_f != "Todos":
                filtro_ciclo = next(c["id"] for c in ciclos_todos if c["nombre"] == ciclo_f)

        resumen = get_resumen_por_area(filtro_ciclo)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Pedidos", sum(r["total_pedidos"] or 0 for r in resumen))
        with c2:
            st.metric("Total Items", int(sum(r["total_items"] or 0 for r in resumen)))
        with c3:
            st.metric("Entregados", int(sum(r["entregados"] or 0 for r in resumen)))
        with c4:
            st.metric("Pendientes", int(sum(r["pendientes"] or 0 for r in resumen)))

        col_chart, col_top = st.columns(2)

        with col_chart:
            st.markdown("#### Consumo por Área")
            if any(r["total_pedidos"] for r in resumen):
                df_r = pd.DataFrame(resumen)
                df_r = df_r[df_r["total_pedidos"] > 0].sort_values("total_items", ascending=False)
                if not df_r.empty:
                    chart = df_r.set_index("area")[["total_items"]].rename(columns={"total_items": "Items"})
                    st.bar_chart(chart)
            else:
                st.info("No hay pedidos aún.")

        with col_top:
            st.markdown("#### Productos más pedidos")
            top = get_productos_mas_pedidos(filtro_ciclo)
            if top:
                df_top = pd.DataFrame(top)
                df_top.columns = ["Producto", "Categoría", "Unidad", "Stock", "Total"]
                st.dataframe(df_top, use_container_width=True, hide_index=True)
            else:
                st.info("Sin datos.")

        if stock_bajo:
            st.markdown("#### Stock bajo")
            df_sb = pd.DataFrame(stock_bajo)[["nombre", "stock_almacen", "unidad", "categoria"]]
            df_sb.columns = ["Producto", "Stock", "Unidad", "Categoría"]
            st.dataframe(df_sb, use_container_width=True, hide_index=True)

    # --- PEDIDOS ---
    with tab2:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            ciclos_todos = get_ciclos()
            filtro = None
            if ciclos_todos:
                sel = st.selectbox("Ciclo", ["Todos"] + [c["nombre"] for c in ciclos_todos], key="adm_ciclo")
                if sel != "Todos":
                    filtro = next(c["id"] for c in ciclos_todos if c["nombre"] == sel)
        with col_f2:
            estado_f = st.selectbox("Estado", ["Todos", "Pendientes", "Aprobados", "Entregados", "Rechazados"], key="adm_est")

        mapa = {"Pendientes": "pendiente", "Aprobados": "aprobado",
                "Entregados": "entregado", "Rechazados": "rechazado"}
        estado_val = mapa.get(estado_f)

        pedidos = get_todos_pedidos(filtro, estado_val)
        if not pedidos:
            st.info("No hay pedidos con estos filtros.")
        else:
            st.caption(f"{len(pedidos)} pedido(s)")
            for ped in pedidos:
                estado = ped["estado"]
                emoji_st = {"pendiente": "🟡", "aprobado": "🔵", "entregado": "🟢", "rechazado": "🔴"}.get(estado, "⚪")
                urg = " 🔴" if ped.get("prioridad") == "urgente" else ""
                area_emoji = ped.get("area_emoji", "🏢")

                with st.expander(
                    f"{emoji_st}{urg} #{ped['id']} | {area_emoji} {ped['area_nombre']} | {estado.upper()} | {ped['fecha_pedido'][:10]}"
                ):
                    if ped.get("prioridad") == "urgente":
                        st.error("PEDIDO URGENTE")
                    if ped["notas"]:
                        st.info(f"{ped['notas']}")

                    detalles = get_detalle_pedido(ped["id"])
                    df_d = pd.DataFrame(detalles)[["producto_nombre", "cantidad", "unidad"]]
                    df_d.columns = ["Producto", "Cantidad", "Unidad"]
                    st.dataframe(df_d, use_container_width=True, hide_index=True)

                    if estado == "pendiente":
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button("Aprobar", key=f"apr_{ped['id']}", use_container_width=True):
                                actualizar_estado_pedido(ped["id"], "aprobado")
                                st.rerun()
                        with c2:
                            if st.button("Entregar", key=f"ent_{ped['id']}", use_container_width=True, type="primary"):
                                entregar_pedido(ped["id"])
                                st.rerun()
                        with c3:
                            if st.button("Rechazar", key=f"rej_{ped['id']}", use_container_width=True):
                                actualizar_estado_pedido(ped["id"], "rechazado")
                                st.rerun()
                    elif estado == "aprobado":
                        if st.button("Marcar Entregado", key=f"entd_{ped['id']}", use_container_width=True, type="primary"):
                            entregar_pedido(ped["id"])
                            st.rerun()

    # --- CATÁLOGO ---
    with tab3:
        productos = get_productos(solo_activos=False)
        activos = len([p for p in productos if p["activo"]])

        c1, c2 = st.columns(2)
        with c1:
            st.metric("Productos activos", activos)
        with c2:
            st.metric("Categorías", len(set(p["categoria"] for p in productos)) if productos else 0)

        col_masivo, col_individual = st.columns(2)

        with col_masivo:
            with st.expander("Cargar desde Excel/CSV"):
                st.caption("Columnas: nombre, categoria, unidad, stock")
                archivo = st.file_uploader("Archivo", type=["xlsx", "csv"], key="carga")
                if archivo:
                    try:
                        df_c = pd.read_csv(archivo) if archivo.name.endswith(".csv") else pd.read_excel(archivo)
                        if "nombre" not in df_c.columns:
                            st.error("Necesita columna 'nombre'")
                        else:
                            for col in ["categoria", "unidad", "stock"]:
                                if col not in df_c.columns:
                                    df_c[col] = "General" if col == "categoria" else ("pieza" if col == "unidad" else 0)
                            st.dataframe(df_c.head(5), use_container_width=True, hide_index=True)
                            st.caption(f"{len(df_c)} productos")
                            if st.button("Cargar", type="primary", use_container_width=True):
                                items = [(r["nombre"], r["categoria"], r["unidad"], int(r["stock"]))
                                         for _, r in df_c.iterrows() if pd.notna(r["nombre"])]
                                agregar_productos_masivo(items)
                                st.success(f"{len(items)} productos cargados")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col_individual:
            with st.expander("Agregar producto"):
                with st.form("nuevo_prod"):
                    nombre = st.text_input("Nombre")
                    categoria = st.text_input("Categoría", value="General")
                    unidad = st.selectbox("Unidad", ["pieza", "paquete", "caja", "resma", "rollo", "bote", "bolsa", "litro", "kilo"])
                    stock = st.number_input("Stock", min_value=0, value=0)
                    if st.form_submit_button("Agregar", use_container_width=True):
                        if nombre.strip():
                            agregar_producto(nombre.strip(), categoria.strip(), unidad, stock)
                            st.success(f"'{nombre}' agregado")
                            st.rerun()

        # Lista
        if productos:
            buscar_p = st.text_input("Buscar en catálogo", key="buscar_cat")
            for cat in sorted(set(p["categoria"] for p in productos)):
                pc = [p for p in productos if p["categoria"] == cat]
                if buscar_p:
                    pc = [p for p in pc if buscar_p.lower() in p["nombre"].lower()]
                if not pc:
                    continue
                with st.expander(f"{cat} ({len(pc)})"):
                    df_cat = pd.DataFrame(pc)[["nombre", "stock_almacen", "unidad", "activo"]]
                    df_cat["activo"] = df_cat["activo"].map({1: "Si", 0: "No"})
                    df_cat.columns = ["Producto", "Stock", "Unidad", "Activo"]
                    st.dataframe(df_cat, use_container_width=True, hide_index=True)

    # --- CICLOS ---
    with tab4:
        ciclo_activo = get_ciclo_activo()
        if ciclo_activo:
            dias = (datetime.strptime(ciclo_activo["fecha_cierre"], "%Y-%m-%d") - datetime.now()).days
            st.success(f"**Ciclo activo:** {ciclo_activo['nombre']} — {max(0, dias)} días restantes")
            if st.button("Cerrar ciclo actual", use_container_width=False):
                cerrar_ciclo(ciclo_activo["id"])
                asegurar_ciclo_activo()
                st.rerun()

        with st.expander("Crear ciclo manual"):
            with st.form("nuevo_ciclo"):
                hoy = datetime.now()
                num = len(get_ciclos()) + 1
                nombre_ciclo = st.text_input("Nombre", value=f"Ciclo #{num} — {hoy.strftime('%B %Y')}")
                c1, c2 = st.columns(2)
                with c1:
                    f_inicio = st.date_input("Inicio", value=hoy)
                with c2:
                    f_cierre = st.date_input("Cierre", value=hoy + timedelta(days=CICLO_DIAS))
                if st.form_submit_button("Crear", type="primary"):
                    crear_ciclo(nombre_ciclo, num, f_inicio.strftime("%Y-%m-%d"), f_cierre.strftime("%Y-%m-%d"))
                    st.rerun()

        st.markdown("#### Historial")
        for c in get_ciclos():
            e = "🟢" if c["estado"] == "abierto" else "⚫"
            st.markdown(f"{e} **{c['nombre']}** | {c['fecha_inicio']} → {c['fecha_cierre']}")

    # --- ÁREAS ---
    with tab5:
        for a in areas:
            ea = a.get("emoji", "🏢")
            with st.expander(f"{ea} {a['nombre']}"):
                lider = st.text_input("Líder", value=a["lider"] or "", key=f"l_{a['id']}", placeholder="Nombre del líder")
                if st.button("Guardar", key=f"sl_{a['id']}"):
                    actualizar_lider(a["id"], lider)
                    st.rerun()
                inv = get_inventario_area(a["id"])
                if inv:
                    df_i = pd.DataFrame(inv)[["producto_nombre", "cantidad", "unidad"]]
                    df_i.columns = ["Producto", "Cantidad", "Unidad"]
                    st.dataframe(df_i, use_container_width=True, hide_index=True)

        st.divider()
        if st.button("Respaldar Base de Datos"):
            path = backup_db()
            if path:
                st.success(f"Respaldo: {path}")

# Footer
st.divider()
st.caption("PROESA Soluciones en Salud — Sistema de Inventario v2.0")
