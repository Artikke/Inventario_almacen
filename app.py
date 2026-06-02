import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import (
    init_db, cargar_catalogo_ejemplo, asegurar_ciclo_activo, backup_db,
    get_areas, get_productos, get_categorias, agregar_producto,
    actualizar_producto, actualizar_stock, agregar_productos_masivo,
    get_ciclo_activo, get_ciclos, crear_ciclo, cerrar_ciclo,
    crear_pedido, get_pedidos_area, get_detalle_pedido, get_todos_pedidos,
    actualizar_estado_pedido, entregar_pedido, borrar_pedido, contar_pedidos_pendientes,
    get_inventario_area, get_resumen_por_area, get_productos_mas_pedidos,
    get_stock_bajo, get_consumo_por_area_periodo,
    actualizar_lider, get_log_actividad, log_actividad,
    CICLO_DIAS,
)

# ==============================================================
# CONFIG
# ==============================================================
st.set_page_config(
    page_title="PROESA - Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
cargar_catalogo_ejemplo()
asegurar_ciclo_activo()

# ==============================================================
# CSS — Design system corporativo PROESA
# ==============================================================
PROESA_CSS = """
<style>
:root {
    --proesa-blue: #1a5276;
    --proesa-dark-blue: #0e3650;
    --proesa-mid-blue: #2471a3;
    --proesa-light-blue: #d6eaf8;
    --proesa-ice: #eaf2f8;
    --proesa-green: #1abc9c;
    --proesa-green-bg: #e8f8f5;
    --proesa-yellow: #f39c12;
    --proesa-yellow-bg: #fef9e7;
    --proesa-red: #e74c3c;
    --proesa-red-bg: #fdedec;
    --proesa-bg: #f4f7fa;
    --proesa-white: #ffffff;
    --proesa-border: #d4e6f1;
    --proesa-text: #1a1a2e;
    --proesa-muted: #7f8c8d;
    --radius: 14px;
    --shadow-sm: 0 1px 3px rgba(26,82,118,0.06);
    --shadow-md: 0 4px 12px rgba(26,82,118,0.08);
    --shadow-lg: 0 8px 24px rgba(26,82,118,0.10);
}

/* ── Layout ── */
.block-container { padding: 1.2rem 2.5rem 2rem; max-width: 100%; }
header[data-testid="stHeader"] { background: var(--proesa-blue); }
[data-testid="stAppViewBlockContainer"] { background: var(--proesa-bg); }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--proesa-blue) 0%, var(--proesa-dark-blue) 100%);
    border-right: none;
}
section[data-testid="stSidebar"] * { color: #ffffff !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12); margin: 12px 0; }
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18);
    border-radius: 10px;
}
section[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px; padding: 10px 14px; margin: 3px 0;
    font-weight: 500; transition: all 0.2s ease;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.18); border-color: rgba(255,255,255,0.25);
}
section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"] {
    background: rgba(255,255,255,0.22) !important;
    border-color: var(--proesa-green) !important;
}
section[data-testid="stSidebar"] .stProgress > div > div {
    background: rgba(255,255,255,0.15); border-radius: 8px;
}
section[data-testid="stSidebar"] .stProgress > div > div > div {
    background: var(--proesa-green); border-radius: 8px;
}

/* ── Sidebar logo ── */
.sidebar-logo {
    text-align: center; padding: 20px 0 8px;
}
.sidebar-logo-mark {
    font-size: 2rem; font-weight: 800; letter-spacing: 4px;
    color: #ffffff; margin: 0; line-height: 1.1;
}
.sidebar-logo-sub {
    font-size: 0.6rem; letter-spacing: 4px; text-transform: uppercase;
    color: rgba(255,255,255,0.55); margin: 2px 0 0;
}
.sidebar-section-label {
    font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase;
    color: rgba(255,255,255,0.45); margin: 0 0 6px; font-weight: 600;
}
.sidebar-ciclo {
    background: rgba(255,255,255,0.08); border-radius: 12px;
    padding: 14px; margin-top: 4px;
}
.sidebar-ciclo-title { font-size: 0.75rem; color: rgba(255,255,255,0.6); margin: 0; }
.sidebar-ciclo-name { font-size: 0.9rem; font-weight: 600; color: #fff; margin: 2px 0 8px; }
.sidebar-ciclo-days {
    font-size: 0.7rem; color: rgba(255,255,255,0.5); margin: 4px 0 0; text-align: right;
}
.sidebar-badge {
    background: var(--proesa-red); color: white; font-size: 0.72rem; font-weight: 700;
    padding: 6px 12px; border-radius: 10px; text-align: center; margin-top: 4px;
}

/* ── Page header ── */
.page-header {
    display: flex; align-items: center; gap: 14px;
    margin-top: 20px; margin-bottom: 24px; padding-bottom: 16px;
    border-bottom: 2px solid var(--proesa-border);
}
.page-header-icon { font-size: 1.8rem; }
.page-header-text h2 {
    margin: 0; font-size: 1.5rem; font-weight: 700;
    color: var(--proesa-blue); line-height: 1.2;
}
.page-header-text p {
    margin: 2px 0 0; font-size: 0.82rem; color: var(--proesa-muted);
}

/* ── KPI Cards ── */
div[data-testid="stMetric"] {
    background: var(--proesa-white);
    border: 1px solid var(--proesa-border);
    border-radius: var(--radius); padding: 18px 16px;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s, transform 0.2s;
}
div[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-md); transform: translateY(-1px);
}
div[data-testid="stMetricValue"] {
    font-size: 2rem; font-weight: 800; color: var(--proesa-blue);
}
div[data-testid="stMetricLabel"] {
    font-size: 0.78rem; color: var(--proesa-muted);
    text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--proesa-white); border-radius: 12px;
    padding: 4px; border: 1px solid var(--proesa-border);
    box-shadow: var(--shadow-sm); gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px; font-weight: 500; font-size: 0.88rem;
    padding: 8px 18px; color: var(--proesa-muted);
}
.stTabs [aria-selected="true"] {
    background: var(--proesa-blue) !important; color: #ffffff !important;
    font-weight: 600; box-shadow: var(--shadow-sm);
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px; font-weight: 600; font-size: 0.85rem;
    padding: 8px 20px; transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: var(--proesa-blue); border: none; color: white;
}
.stButton > button[kind="primary"]:hover {
    background: var(--proesa-dark-blue); box-shadow: var(--shadow-md);
}
.stButton > button[kind="secondary"] {
    border: 1px solid var(--proesa-border); color: var(--proesa-blue);
}

/* ── Expanders / Cards ── */
.streamlit-expanderHeader {
    background: var(--proesa-white); border-radius: var(--radius) !important;
    font-weight: 500; font-size: 0.9rem;
    border: 1px solid var(--proesa-border);
}
details[open] .streamlit-expanderHeader {
    border-bottom: 1px solid var(--proesa-border);
    border-radius: var(--radius) var(--radius) 0 0 !important;
}
.streamlit-expanderContent {
    border: 1px solid var(--proesa-border); border-top: none;
    border-radius: 0 0 var(--radius) var(--radius);
    background: var(--proesa-white);
}

/* ── Inputs ── */
.stTextInput > div > div, .stSelectbox > div > div, .stTextArea > div > div {
    border-radius: 10px; border: 1px solid var(--proesa-border);
}
.stTextInput > div > div:focus-within, .stSelectbox > div > div:focus-within {
    border-color: var(--proesa-mid-blue);
    box-shadow: 0 0 0 2px rgba(36,113,163,0.15);
}

/* ── DataFrames ── */
.stDataFrame { border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-sm); }

/* ── Custom badges ── */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.3px;
}
.badge-green { background: var(--proesa-green-bg); color: #148f77; }
.badge-yellow { background: var(--proesa-yellow-bg); color: #b7950b; }
.badge-red { background: var(--proesa-red-bg); color: #c0392b; }
.badge-blue { background: var(--proesa-light-blue); color: var(--proesa-blue); }

/* ── Product row ── */
.prod-row {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 14px; margin: 2px 0;
    border-bottom: 1px solid #f0f3f5;
    transition: background 0.15s;
}
.prod-row:hover { background: var(--proesa-ice); }
.prod-row:last-child { border-bottom: none; }
.prod-name { flex: 3; font-weight: 500; font-size: 0.9rem; color: var(--proesa-text); }
.prod-unit { flex: 1; font-size: 0.8rem; color: var(--proesa-muted); text-align: center; }
.prod-stock { flex: 1; text-align: center; }

/* ── Order card ── */
.order-card {
    background: var(--proesa-white); border: 1px solid var(--proesa-border);
    border-radius: var(--radius); padding: 16px 20px; margin: 8px 0;
    box-shadow: var(--shadow-sm); transition: box-shadow 0.2s;
}
.order-card:hover { box-shadow: var(--shadow-md); }
.order-card-urgent { border-left: 4px solid var(--proesa-red); }
.order-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 8px;
}
.order-folio { font-weight: 700; color: var(--proesa-blue); font-size: 0.95rem; }
.order-date { font-size: 0.78rem; color: var(--proesa-muted); }
.order-area { font-size: 0.85rem; color: var(--proesa-text); font-weight: 500; }

/* ── Summary panel ── */
.summary-panel {
    background: var(--proesa-white); border: 2px solid var(--proesa-blue);
    border-radius: var(--radius); padding: 18px 20px;
    box-shadow: var(--shadow-md); position: sticky; top: 20px;
}
.summary-title {
    font-size: 0.95rem; font-weight: 700; color: var(--proesa-blue);
    margin: 0 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--proesa-border);
}
.summary-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 4px 0; font-size: 0.85rem;
}
.summary-item-name { color: var(--proesa-text); }
.summary-item-qty { font-weight: 700; color: var(--proesa-blue); }
.summary-total {
    display: flex; justify-content: space-between; margin-top: 10px;
    padding-top: 10px; border-top: 1px solid var(--proesa-border);
    font-weight: 700; font-size: 0.95rem; color: var(--proesa-blue);
}

/* ── Section heading ── */
.section-heading {
    font-size: 1.05rem; font-weight: 700; color: var(--proesa-blue);
    margin: 24px 0 12px; padding-bottom: 6px;
    border-bottom: 2px solid var(--proesa-light-blue);
}

/* ── Alert bar ── */
.alert-bar {
    display: flex; gap: 12px; margin-bottom: 20px;
}
.alert-chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; border-radius: 10px; font-size: 0.82rem; font-weight: 600;
}
.alert-chip-red { background: var(--proesa-red-bg); color: var(--proesa-red); }
.alert-chip-yellow { background: var(--proesa-yellow-bg); color: #b7950b; }

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 40px 20px; color: var(--proesa-muted);
}
.empty-state-icon { font-size: 2.5rem; margin-bottom: 8px; }
.empty-state-text { font-size: 0.95rem; }

/* ── Footer ── */
.app-footer {
    text-align: center; padding: 20px 0 8px;
    font-size: 0.72rem; color: var(--proesa-muted);
    border-top: 1px solid var(--proesa-border); margin-top: 40px;
}
</style>
"""
st.markdown(PROESA_CSS, unsafe_allow_html=True)


# ==============================================================
# HELPER COMPONENTS
# ==============================================================

def render_page_header(icon, title, subtitle=""):
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-icon">{icon}</div>
        <div class="page-header-text">
            <h2>{title}</h2>
            {sub_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stock_badge(stock):
    if stock == 0:
        return '<span class="badge badge-red">Sin stock</span>'
    elif stock <= 5:
        return f'<span class="badge badge-yellow">Stock: {stock}</span>'
    else:
        return f'<span class="badge badge-green">Stock: {stock}</span>'


def render_status_badge(estado):
    m = {
        "pendiente": ("Pendiente", "badge-yellow"),
        "aprobado": ("Aprobado", "badge-blue"),
        "entregado": ("Entregado", "badge-green"),
        "rechazado": ("Rechazado", "badge-red"),
    }
    text, cls = m.get(estado, (estado, "badge-blue"))
    return f'<span class="badge {cls}">{text}</span>'


def render_empty_state(icon, text):
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-text">{text}</div>
    </div>
    """, unsafe_allow_html=True)


def render_section_heading(text):
    st.markdown(f'<div class="section-heading">{text}</div>', unsafe_allow_html=True)


# ==============================================================
# SIDEBAR
# ==============================================================
areas = get_areas()
area_nombres = [a["nombre"] for a in areas]
pendientes = contar_pedidos_pendientes()

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <p class="sidebar-logo-mark">PROESA</p>
        <p class="sidebar-logo-sub">Soluciones en Salud</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown('<p class="sidebar-section-label">Acceso</p>', unsafe_allow_html=True)
    rol = st.radio("Rol", ["Lider de Area", "Almacen (Admin)"], label_visibility="collapsed")
    is_admin = "Admin" in rol

    if not is_admin:
        # Si cambia a líder, resetear auth admin
        if st.session_state.get("admin_auth", False):
            st.session_state["admin_auth"] = False
        st.divider()
        st.markdown('<p class="sidebar-section-label">Selecciona tu area</p>', unsafe_allow_html=True)
        area_sel = st.selectbox("Area", area_nombres, label_visibility="collapsed")
        area = next(a for a in areas if a["nombre"] == area_sel)
        area_id = area["id"]

    if is_admin and st.session_state.get("admin_auth", False):
        st.divider()
        if st.button("Cerrar acceso admin", use_container_width=True):
            st.session_state["admin_auth"] = False
            st.rerun()

    st.divider()
    ciclo = get_ciclo_activo()
    if ciclo:
        fecha_inicio = datetime.strptime(ciclo["fecha_inicio"], "%Y-%m-%d")
        fecha_cierre = datetime.strptime(ciclo["fecha_cierre"], "%Y-%m-%d")
        dias = max(0, (fecha_cierre - datetime.now()).days)
        total_dias = max(1, (fecha_cierre - fecha_inicio).days)
        progreso = max(0, min(1.0, 1 - (dias / total_dias)))
        st.markdown(f"""
        <div class="sidebar-ciclo">
            <p class="sidebar-ciclo-title">CICLO ACTIVO</p>
            <p class="sidebar-ciclo-name">{ciclo['nombre']}</p>
        </div>
        """, unsafe_allow_html=True)
        st.progress(progreso)

    if pendientes and is_admin:
        st.divider()
        st.markdown(f'<div class="sidebar-badge">{pendientes} pedido(s) pendiente(s)</div>',
                    unsafe_allow_html=True)

    st.markdown("""
    <div class="app-footer">
        PROESA Soluciones en Salud<br>
        Sistema de Inventario v3.0
    </div>
    """, unsafe_allow_html=True)


# ==============================================================
# VISTA LIDER DE AREA
# ==============================================================
if not is_admin:
    emoji_area = area.get("emoji", "")
    lider_nombre = area.get("lider", "") or "Sin asignar"
    render_page_header(emoji_area, area_sel, f"Lider: {lider_nombre}")

    # ── KPIs ──
    pedidos_area = get_pedidos_area(area_id)
    inv = get_inventario_area(area_id)
    n_pend = len([p for p in pedidos_area if p["estado"] == "pendiente"])
    n_ent = len([p for p in pedidos_area if p["estado"] == "entregado"])
    n_items = sum(i["cantidad"] for i in inv) if inv else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Pedidos", len(pedidos_area))
    with k2:
        st.metric("Pendientes", n_pend)
    with k3:
        st.metric("Entregados", n_ent)
    with k4:
        st.metric("Items en Area", n_items)

    tab_pedido, tab_mis, tab_inv = st.tabs(["Nuevo Pedido", "Mis Pedidos", "Mi Inventario"])

    # ── NUEVO PEDIDO ──
    with tab_pedido:
        if not ciclo:
            render_empty_state("", "No hay un ciclo de pedidos abierto. Contacta al administrador.")
        else:
            productos = get_productos()
            if not productos:
                render_empty_state("", "El catalogo esta vacio. Espera a que el administrador cargue los productos.")
            else:
                # Mensaje de confirmacion
                if st.session_state.pop("pedido_enviado", None):
                    st.success("Gracias, tu pedido ha sido enviado. El equipo de almacen lo revisara pronto.")

                # Search + priority row
                col_search, col_prio = st.columns([4, 1])
                with col_search:
                    buscar = st.text_input(
                        "Buscar producto",
                        placeholder="Escribe para filtrar: boligrafo, folder, pilas...",
                        label_visibility="collapsed",
                    )
                with col_prio:
                    prioridad = st.selectbox("Prioridad", ["Normal", "Urgente"], label_visibility="collapsed")

                # Two-column layout: products left, summary right
                col_productos, col_resumen = st.columns([3, 1])

                items_pedido = []
                productos_sel_info = []

                with col_productos:
                    categorias = sorted(set(p["categoria"] for p in productos))
                    for cat in categorias:
                        prods_cat = [p for p in productos if p["categoria"] == cat]
                        if buscar:
                            prods_cat = [p for p in prods_cat if buscar.lower() in p["nombre"].lower()]
                        if not prods_cat:
                            continue

                        with st.expander(f"{cat}  ({len(prods_cat)})", expanded=bool(buscar)):
                            # Table header
                            hdr1, hdr2, hdr3 = st.columns([4, 1.5, 1])
                            with hdr1:
                                st.caption("**PRODUCTO**")
                            with hdr2:
                                st.caption("**UNIDAD**")
                            with hdr3:
                                st.caption("**CANT.**")

                            for p in prods_cat:
                                r1, r2, r3 = st.columns([4, 1.5, 1])
                                with r1:
                                    st.markdown(f"**{p['nombre']}**")
                                with r2:
                                    st.caption(p["unidad"])
                                with r3:
                                    cant = st.number_input(
                                        "c", min_value=0, max_value=999, value=0,
                                        key=f"prod_{p['id']}", label_visibility="collapsed",
                                    )
                                    if cant > 0:
                                        items_pedido.append((p["id"], cant))
                                        productos_sel_info.append((p["nombre"], cant, p["unidad"]))

                # ── Summary panel ──
                with col_resumen:
                    prio_label = "Urgente" if prioridad == "Urgente" else "Normal"
                    st.markdown(f"**Resumen del Pedido** — {prio_label}")
                    st.divider()

                    if productos_sel_info:
                        for nombre, cant, unidad in productos_sel_info:
                            st.markdown(f"- **{nombre}** — {cant} {unidad}")
                        st.divider()
                        st.markdown(f"**Total: {len(productos_sel_info)} producto(s)**")

                        notas = st.text_area("Notas (opcional)", placeholder="Ej: Necesario para evento del viernes",
                                             key="notas_pedido")

                        if st.button("Enviar Pedido", type="primary", use_container_width=True):
                            prio = "urgente" if prioridad == "Urgente" else "normal"
                            pedido_id = crear_pedido(area_id, ciclo["id"], items_pedido, notas, prio)
                            st.session_state["pedido_enviado"] = pedido_id
                            # Limpiar cantidades eliminando keys para que se recreen en 0
                            keys_to_del = [f"prod_{p['id']}" for p in productos if f"prod_{p['id']}" in st.session_state]
                            if "notas_pedido" in st.session_state:
                                keys_to_del.append("notas_pedido")
                            for k in keys_to_del:
                                del st.session_state[k]
                            st.rerun()
                    else:
                        st.caption("Selecciona productos del catalogo para armar tu pedido.")

    # ── MIS PEDIDOS ──
    with tab_mis:
        if not pedidos_area:
            render_empty_state("", "No tienes pedidos registrados aun.")
        else:
            # Filters
            fc1, fc2 = st.columns([1, 3])
            with fc1:
                filtro_estado = st.selectbox(
                    "Estado", ["Todos", "Pendientes", "Aprobados", "Entregados", "Rechazados"],
                    key="filtro_mis",
                )

            mapa = {"Pendientes": "pendiente", "Aprobados": "aprobado",
                    "Entregados": "entregado", "Rechazados": "rechazado"}
            pedidos_f = pedidos_area
            if filtro_estado != "Todos":
                pedidos_f = [p for p in pedidos_area if p["estado"] == mapa[filtro_estado]]

            st.caption(f"{len(pedidos_f)} pedido(s)")

            for ped in pedidos_f:
                estado = ped["estado"]
                urg_class = " order-card-urgent" if ped.get("prioridad") == "urgente" else ""
                urg_badge = ' <span class="badge badge-red">Urgente</span>' if ped.get("prioridad") == "urgente" else ""

                st.markdown(f"""
                <div class="order-card{urg_class}">
                    <div class="order-header">
                        <span class="order-folio">Pedido #{ped['id']}{urg_badge}</span>
                        <span class="order-date">{ped['fecha_pedido'][:10]}</span>
                    </div>
                    <div style="margin-bottom:4px;">{render_status_badge(estado)}</div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"Ver detalle #{ped['id']}"):
                    if ped["notas"]:
                        st.info(ped["notas"])
                    detalles = get_detalle_pedido(ped["id"])
                    df_det = pd.DataFrame(detalles)[["producto_nombre", "cantidad", "unidad", "cantidad_entregada"]]
                    df_det.columns = ["Producto", "Solicitado", "Unidad", "Entregado"]
                    st.dataframe(df_det, use_container_width=True, hide_index=True)

    # ── MI INVENTARIO ──
    with tab_inv:
        if not inv:
            render_empty_state("", "Tu area no tiene inventario registrado. Aparecera cuando te entreguen pedidos.")
        else:
            buscar_inv = st.text_input("Buscar en inventario", placeholder="Filtrar productos...",
                                        key="buscar_inv", label_visibility="collapsed")
            df_inv = pd.DataFrame(inv)[["producto_nombre", "cantidad", "unidad", "categoria", "ultima_actualizacion"]]
            df_inv.columns = ["Producto", "Cantidad", "Unidad", "Categoria", "Ultima Entrega"]
            if buscar_inv:
                df_inv = df_inv[df_inv["Producto"].str.lower().str.contains(buscar_inv.lower())]
            st.dataframe(df_inv, use_container_width=True, hide_index=True, height=400)


# ==============================================================
# VISTA ADMIN (ALMACEN)
# ==============================================================
else:
    ADMIN_PIN = st.secrets.get("ADMIN_PIN", "1234")

    if not st.session_state.get("admin_auth", False):
        render_page_header("", "Acceso Almacen", "Ingresa el PIN para continuar")

        col_pin, _ = st.columns([1, 2])
        with col_pin:
            pin = st.text_input("PIN de almacen", type="password", placeholder="Ingresa el PIN")
            if st.button("Entrar", type="primary", use_container_width=True):
                if pin == ADMIN_PIN:
                    st.session_state["admin_auth"] = True
                    st.rerun()
                else:
                    st.error("PIN incorrecto. Intenta de nuevo.")
        st.stop()

    render_page_header("", "Panel de Almacen", "Administracion de inventario y pedidos")

    # ── Alert bar ──
    pendientes_list = get_todos_pedidos(estado="pendiente")
    stock_bajo = get_stock_bajo()
    urgentes = [p for p in pendientes_list if p.get("prioridad") == "urgente"]

    alerts_html = '<div class="alert-bar">'
    if urgentes:
        alerts_html += f'<div class="alert-chip alert-chip-red">{len(urgentes)} pedido(s) URGENTE(S)</div>'
    if len(pendientes_list) - len(urgentes) > 0:
        alerts_html += f'<div class="alert-chip alert-chip-yellow">{len(pendientes_list) - len(urgentes)} pedido(s) pendiente(s)</div>'
    if stock_bajo:
        alerts_html += f'<div class="alert-chip alert-chip-yellow">{len(stock_bajo)} producto(s) con stock bajo</div>'
    alerts_html += '</div>'
    if pendientes_list or stock_bajo:
        st.markdown(alerts_html, unsafe_allow_html=True)

    tab_dash, tab_ped, tab_cat, tab_cicl, tab_areas = st.tabs(
        ["Dashboard", "Pedidos", "Catalogo", "Ciclos", "Areas"]
    )

    # ── DASHBOARD ──
    with tab_dash:
        ciclos_todos = get_ciclos()
        filtro_ciclo = None
        if ciclos_todos:
            ciclo_f = st.selectbox("Filtrar por ciclo", ["Todos"] + [c["nombre"] for c in ciclos_todos])
            if ciclo_f != "Todos":
                filtro_ciclo = next(c["id"] for c in ciclos_todos if c["nombre"] == ciclo_f)

        resumen = get_resumen_por_area(filtro_ciclo)

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total Pedidos", sum(r["total_pedidos"] or 0 for r in resumen))
        with k2:
            st.metric("Total Items", int(sum(r["total_items"] or 0 for r in resumen)))
        with k3:
            st.metric("Entregados", int(sum(r["entregados"] or 0 for r in resumen)))
        with k4:
            st.metric("Pendientes", int(sum(r["pendientes"] or 0 for r in resumen)))

        col_chart, col_top = st.columns(2)

        with col_chart:
            render_section_heading("Consumo por Area")
            if any(r["total_pedidos"] for r in resumen):
                df_r = pd.DataFrame(resumen)
                df_r = df_r[df_r["total_pedidos"] > 0].sort_values("total_items", ascending=False)
                if not df_r.empty:
                    chart = df_r.set_index("area")[["total_items"]].rename(columns={"total_items": "Items"})
                    st.bar_chart(chart, color="#1a5276")
            else:
                render_empty_state("", "No hay pedidos en este periodo.")

        with col_top:
            render_section_heading("Productos mas pedidos")
            top = get_productos_mas_pedidos(filtro_ciclo)
            if top:
                df_top = pd.DataFrame(top)
                df_top.columns = ["Producto", "Categoria", "Unidad", "Stock", "Total"]
                st.dataframe(df_top, use_container_width=True, hide_index=True)
            else:
                render_empty_state("", "Sin datos.")

        if stock_bajo:
            render_section_heading("Alerta de Stock Bajo")
            df_sb = pd.DataFrame(stock_bajo)[["nombre", "stock_almacen", "unidad", "categoria"]]
            df_sb.columns = ["Producto", "Stock", "Unidad", "Categoria"]
            st.dataframe(df_sb, use_container_width=True, hide_index=True)

    # ── PEDIDOS ──
    with tab_ped:
        f1, f2, f3 = st.columns([2, 2, 6])
        with f1:
            ciclos_todos = get_ciclos()
            filtro = None
            if ciclos_todos:
                sel = st.selectbox("Ciclo", ["Todos"] + [c["nombre"] for c in ciclos_todos], key="adm_ciclo")
                if sel != "Todos":
                    filtro = next(c["id"] for c in ciclos_todos if c["nombre"] == sel)
        with f2:
            estado_f = st.selectbox("Estado", ["Todos", "Pendientes", "Aprobados", "Entregados", "Rechazados"], key="adm_est")

        mapa = {"Pendientes": "pendiente", "Aprobados": "aprobado",
                "Entregados": "entregado", "Rechazados": "rechazado"}
        estado_val = mapa.get(estado_f)

        pedidos = get_todos_pedidos(filtro, estado_val)
        if not pedidos:
            render_empty_state("", "No hay pedidos con estos filtros.")
        else:
            st.caption(f"{len(pedidos)} pedido(s)")
            for ped in pedidos:
                estado = ped["estado"]
                urg_class = " order-card-urgent" if ped.get("prioridad") == "urgente" else ""
                urg_badge = ' <span class="badge badge-red">Urgente</span>' if ped.get("prioridad") == "urgente" else ""
                area_emoji = ped.get("area_emoji", "")

                st.markdown(f"""
                <div class="order-card{urg_class}">
                    <div class="order-header">
                        <span class="order-folio">#{ped['id']} {area_emoji} {ped['area_nombre']}{urg_badge}</span>
                        <span class="order-date">{ped['fecha_pedido'][:10]}</span>
                    </div>
                    <div>{render_status_badge(estado)}</div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"Gestionar #{ped['id']} - {ped['area_nombre']}"):
                    if ped["notas"]:
                        st.info(ped["notas"])

                    detalles = get_detalle_pedido(ped["id"])
                    df_d = pd.DataFrame(detalles)[["producto_nombre", "cantidad", "unidad"]]
                    df_d.columns = ["Producto", "Cantidad", "Unidad"]
                    st.dataframe(df_d, use_container_width=True, hide_index=True)

                    if estado == "pendiente":
                        c1, c2, c3, c4 = st.columns(4)
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
                        with c4:
                            if st.button("Eliminar", key=f"del_{ped['id']}", use_container_width=True):
                                borrar_pedido(ped["id"])
                                st.rerun()
                    elif estado == "aprobado":
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Marcar Entregado", key=f"entd_{ped['id']}", use_container_width=True, type="primary"):
                                entregar_pedido(ped["id"])
                                st.rerun()
                        with c2:
                            if st.button("Eliminar", key=f"dela_{ped['id']}", use_container_width=True):
                                borrar_pedido(ped["id"])
                                st.rerun()
                    else:
                        if st.button("Eliminar", key=f"dele_{ped['id']}"):
                            borrar_pedido(ped["id"])
                            st.rerun()

    # ── CATALOGO ──
    with tab_cat:
        productos = get_productos(solo_activos=False)
        activos = len([p for p in productos if p["activo"]])

        k1, k2 = st.columns(2)
        with k1:
            st.metric("Productos Activos", activos)
        with k2:
            st.metric("Categorias", len(set(p["categoria"] for p in productos)) if productos else 0)

        col_m, col_i = st.columns(2)
        with col_m:
            with st.expander("Cargar desde Excel/CSV"):
                st.caption("Columnas requeridas: **nombre** | Opcionales: categoria, unidad, stock")
                archivo = st.file_uploader("Seleccionar archivo", type=["xlsx", "csv"], key="carga",
                                           label_visibility="collapsed")
                if archivo:
                    try:
                        df_c = pd.read_csv(archivo) if archivo.name.endswith(".csv") else pd.read_excel(archivo)
                        if "nombre" not in df_c.columns:
                            st.error("El archivo debe tener una columna 'nombre'")
                        else:
                            for col in ["categoria", "unidad", "stock"]:
                                if col not in df_c.columns:
                                    df_c[col] = "General" if col == "categoria" else ("pieza" if col == "unidad" else 0)
                            st.dataframe(df_c.head(5), use_container_width=True, hide_index=True)
                            st.caption(f"{len(df_c)} productos encontrados")
                            if st.button("Cargar productos", type="primary", use_container_width=True):
                                items = [(r["nombre"], r["categoria"], r["unidad"], int(r["stock"]))
                                         for _, r in df_c.iterrows() if pd.notna(r["nombre"])]
                                agregar_productos_masivo(items)
                                st.success(f"{len(items)} productos cargados")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col_i:
            with st.expander("Agregar producto individual"):
                with st.form("nuevo_prod"):
                    nombre = st.text_input("Nombre del producto")
                    c1, c2 = st.columns(2)
                    with c1:
                        categoria = st.text_input("Categoria", value="General")
                    with c2:
                        unidad = st.selectbox("Unidad", ["pieza", "paquete", "caja", "resma", "rollo", "bote", "bolsa", "litro", "kilo"])
                    stock = st.number_input("Stock inicial", min_value=0, value=0)
                    if st.form_submit_button("Agregar Producto", use_container_width=True):
                        if nombre.strip():
                            agregar_producto(nombre.strip(), categoria.strip(), unidad, stock)
                            st.success(f"'{nombre}' agregado al catalogo")
                            st.rerun()
                        else:
                            st.error("El nombre es obligatorio")

        if productos:
            buscar_p = st.text_input("Buscar en catalogo", placeholder="Filtrar por nombre...",
                                      key="buscar_cat", label_visibility="collapsed")
            for cat in sorted(set(p["categoria"] for p in productos)):
                pc = [p for p in productos if p["categoria"] == cat]
                if buscar_p:
                    pc = [p for p in pc if buscar_p.lower() in p["nombre"].lower()]
                if not pc:
                    continue
                with st.expander(f"{cat}  ({len(pc)} productos)"):
                    df_cat = pd.DataFrame(pc)[["nombre", "stock_almacen", "unidad", "activo"]]
                    df_cat["activo"] = df_cat["activo"].map({1: "Activo", 0: "Inactivo"})
                    df_cat.columns = ["Producto", "Stock", "Unidad", "Estado"]
                    st.dataframe(df_cat, use_container_width=True, hide_index=True)

    # ── CICLOS ──
    with tab_cicl:
        ciclo_activo = get_ciclo_activo()
        if ciclo_activo:
            f_ini = datetime.strptime(ciclo_activo["fecha_inicio"], "%Y-%m-%d")
            f_fin = datetime.strptime(ciclo_activo["fecha_cierre"], "%Y-%m-%d")
            dias = max(0, (f_fin - datetime.now()).days)
            total_dias = max(1, (f_fin - f_ini).days)
            progreso = max(0, min(1.0, 1 - (dias / total_dias)))
            st.success(f"**Ciclo activo:** {ciclo_activo['nombre']}")
            st.progress(progreso)
            if st.button("Cerrar ciclo actual"):
                cerrar_ciclo(ciclo_activo["id"])
                asegurar_ciclo_activo()
                st.rerun()

        with st.expander("Crear ciclo manual"):
            with st.form("nuevo_ciclo"):
                import calendar as cal_mod
                hoy = datetime.now()
                num = len(get_ciclos()) + 1
                meses_es = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
                            7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}
                nombre_ciclo = st.text_input("Nombre", value=f"{meses_es[hoy.month]} {hoy.year}")
                c1, c2 = st.columns(2)
                with c1:
                    f_inicio = st.date_input("Inicio", value=hoy.replace(day=1))
                with c2:
                    ultimo_dia = cal_mod.monthrange(hoy.year, hoy.month)[1]
                    f_cierre = st.date_input("Cierre", value=hoy.replace(day=ultimo_dia))
                if st.form_submit_button("Crear Ciclo", type="primary"):
                    crear_ciclo(nombre_ciclo, num, f_inicio.strftime("%Y-%m-%d"), f_cierre.strftime("%Y-%m-%d"))
                    st.rerun()

        render_section_heading("Historial de Ciclos")
        for c in get_ciclos():
            badge = render_status_badge("entregado") if c["estado"] == "abierto" else '<span class="badge badge-yellow">Cerrado</span>'
            st.markdown(f"""
            <div class="order-card" style="padding:12px 16px;">
                <div class="order-header">
                    <span class="order-folio">{c['nombre']}</span>
                    <span>{badge}</span>
                </div>
                <span class="order-date">{c['fecha_inicio']}  &rarr;  {c['fecha_cierre']}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── AREAS ──
    with tab_areas:
        render_section_heading("Areas y Lideres")
        for a in areas:
            ea = a.get("emoji", "")
            with st.expander(f"{ea}  {a['nombre']}"):
                lider = st.text_input("Lider del area", value=a["lider"] or "", key=f"l_{a['id']}",
                                       placeholder="Nombre del lider responsable")
                if st.button("Guardar", key=f"sl_{a['id']}"):
                    actualizar_lider(a["id"], lider)
                    st.success("Lider actualizado")
                    st.rerun()
                inv_a = get_inventario_area(a["id"])
                if inv_a:
                    render_section_heading("Inventario asignado")
                    df_i = pd.DataFrame(inv_a)[["producto_nombre", "cantidad", "unidad"]]
                    df_i.columns = ["Producto", "Cantidad", "Unidad"]
                    st.dataframe(df_i, use_container_width=True, hide_index=True)

        st.divider()
        col_bk, _ = st.columns([1, 3])
        with col_bk:
            if st.button("Respaldar Base de Datos"):
                path = backup_db()
                if path:
                    st.success(f"Respaldo creado")
