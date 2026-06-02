import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import (
    init_db, get_areas, get_productos, agregar_producto, actualizar_producto,
    get_ciclo_activo, get_ciclos, crear_ciclo, cerrar_ciclo,
    crear_pedido, get_pedidos_area, get_detalle_pedido, get_todos_pedidos,
    actualizar_estado_pedido, entregar_pedido,
    get_inventario_area, get_resumen_por_area, get_productos_mas_pedidos,
    actualizar_lider,
)

st.set_page_config(
    page_title="Inventario Almacén",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

init_db()

# --- Estilos ---
st.markdown("""
<style>
    .block-container { max-width: 500px; padding: 1rem; }
    .stMetric { background: #f8f9fa; border-radius: 10px; padding: 12px; text-align: center; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; color: #666; }
    .status-pendiente { color: #f39c12; font-weight: 600; }
    .status-aprobado { color: #3498db; font-weight: 600; }
    .status-entregado { color: #27ae60; font-weight: 600; }
    .status-rechazado { color: #e74c3c; font-weight: 600; }
    h1 { font-size: 1.5rem !important; }
    .area-card {
        background: white; border: 1px solid #e0e0e0; border-radius: 12px;
        padding: 16px; margin: 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("## 📦 Inventario Almacén")

# --- Selección de rol ---
areas = get_areas()
area_nombres = [a["nombre"] for a in areas]

rol = st.radio(
    "Selecciona tu rol",
    ["👤 Líder de Área", "🔧 Administrador (Almacén)"],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# =====================================================
# VISTA LÍDER
# =====================================================
if rol == "👤 Líder de Área":
    area_sel = st.selectbox("Tu área", area_nombres)
    area = next(a for a in areas if a["nombre"] == area_sel)
    area_id = area["id"]

    tab1, tab2, tab3 = st.tabs(["🛒 Pedir", "📋 Mis Pedidos", "📊 Mi Inventario"])

    # --- TAB PEDIR ---
    with tab1:
        ciclo = get_ciclo_activo()
        if not ciclo:
            st.warning("No hay un ciclo de pedidos abierto. Espera a que el administrador abra uno.")
        else:
            dias_restantes = (datetime.strptime(ciclo["fecha_cierre"], "%Y-%m-%d") - datetime.now()).days
            st.info(f"**Ciclo:** {ciclo['nombre']} — Cierra en **{max(0, dias_restantes)} días**")

            productos = get_productos()
            if not productos:
                st.warning("El catálogo está vacío. El administrador debe cargar los productos disponibles.")
            else:
                categorias = sorted(set(p["categoria"] for p in productos))

                st.markdown("### Selecciona productos")
                items_pedido = []

                for cat in categorias:
                    prods_cat = [p for p in productos if p["categoria"] == cat]
                    with st.expander(f"📁 {cat} ({len(prods_cat)} productos)", expanded=len(categorias) == 1):
                        for p in prods_cat:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{p['nombre']}**")
                                st.caption(f"{p['unidad']} | Stock: {p['stock_almacen']}")
                            with col2:
                                cant = st.number_input(
                                    "Cant",
                                    min_value=0,
                                    max_value=max(p["stock_almacen"], 100),
                                    value=0,
                                    key=f"prod_{p['id']}",
                                    label_visibility="collapsed",
                                )
                                if cant > 0:
                                    items_pedido.append((p["id"], cant))

                notas = st.text_area("Notas (opcional)", placeholder="Ej: Urgente para evento del viernes")

                if items_pedido:
                    st.success(f"**{len(items_pedido)} productos** seleccionados")
                    if st.button("📤 Enviar Pedido", type="primary", use_container_width=True):
                        pedido_id = crear_pedido(area_id, ciclo["id"], items_pedido, notas)
                        st.balloons()
                        st.success(f"Pedido #{pedido_id} enviado correctamente")
                        st.rerun()

    # --- TAB MIS PEDIDOS ---
    with tab2:
        pedidos = get_pedidos_area(area_id)
        if not pedidos:
            st.info("No tienes pedidos registrados aún.")
        else:
            for ped in pedidos:
                estado = ped["estado"]
                emoji = {"pendiente": "🟡", "aprobado": "🔵", "entregado": "🟢", "rechazado": "🔴"}.get(estado, "⚪")
                with st.expander(f"{emoji} Pedido #{ped['id']} — {estado.upper()} | {ped['fecha_pedido'][:10]}"):
                    st.caption(f"Ciclo: {ped['ciclo_nombre']}")
                    if ped["notas"]:
                        st.markdown(f"*{ped['notas']}*")
                    detalles = get_detalle_pedido(ped["id"])
                    for d in detalles:
                        entregado = f" ✅ {d['cantidad_entregada']}" if d["cantidad_entregada"] else ""
                        st.markdown(f"- {d['producto_nombre']}: **{d['cantidad']}** {d['unidad']}{entregado}")

    # --- TAB MI INVENTARIO ---
    with tab3:
        inv = get_inventario_area(area_id)
        if not inv:
            st.info("Tu área no tiene inventario registrado aún.")
        else:
            df = pd.DataFrame(inv)[["producto_nombre", "cantidad", "unidad", "categoria", "ultima_actualizacion"]]
            df.columns = ["Producto", "Cantidad", "Unidad", "Categoría", "Última Actualización"]
            st.dataframe(df, use_container_width=True, hide_index=True)


# =====================================================
# VISTA ADMIN
# =====================================================
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Dashboard", "📋 Pedidos", "📦 Catálogo", "🔄 Ciclos", "⚙️ Áreas"]
    )

    # --- TAB DASHBOARD ---
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

        col1, col2 = st.columns(2)
        total_pedidos = sum(r["total_pedidos"] or 0 for r in resumen)
        total_items = sum(r["total_items"] or 0 for r in resumen)
        with col1:
            st.metric("Total Pedidos", total_pedidos)
        with col2:
            st.metric("Total Items", total_items)

        col3, col4 = st.columns(2)
        total_entregados = sum(r["entregados"] or 0 for r in resumen)
        total_pendientes = sum(r["pendientes"] or 0 for r in resumen)
        with col3:
            st.metric("Entregados", total_entregados)
        with col4:
            st.metric("Pendientes", total_pendientes)

        st.markdown("### Pedidos por Área")
        if resumen:
            df_resumen = pd.DataFrame(resumen)
            df_resumen = df_resumen.fillna(0)
            df_resumen.columns = ["Área", "Pedidos", "Items", "Entregados", "Pendientes"]
            df_resumen = df_resumen[df_resumen["Pedidos"] > 0].sort_values("Items", ascending=False)
            if not df_resumen.empty:
                st.dataframe(df_resumen, use_container_width=True, hide_index=True)

                st.bar_chart(df_resumen.set_index("Área")["Items"])
            else:
                st.info("No hay pedidos aún.")

        st.markdown("### Productos más pedidos")
        top = get_productos_mas_pedidos(filtro_ciclo)
        if top:
            df_top = pd.DataFrame(top)
            df_top.columns = ["Producto", "Categoría", "Unidad", "Total Pedido"]
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos aún.")

    # --- TAB PEDIDOS ---
    with tab2:
        ciclos_todos = get_ciclos()
        filtro = None
        if ciclos_todos:
            sel = st.selectbox(
                "Ciclo", ["Todos"] + [c["nombre"] for c in ciclos_todos], key="filtro_pedidos"
            )
            if sel != "Todos":
                filtro = next(c["id"] for c in ciclos_todos if c["nombre"] == sel)

        pedidos = get_todos_pedidos(filtro)
        if not pedidos:
            st.info("No hay pedidos.")
        else:
            for ped in pedidos:
                estado = ped["estado"]
                emoji = {"pendiente": "🟡", "aprobado": "🔵", "entregado": "🟢", "rechazado": "🔴"}.get(estado, "⚪")

                with st.expander(
                    f"{emoji} #{ped['id']} | {ped['area_nombre']} | {estado.upper()} | {ped['fecha_pedido'][:10]}"
                ):
                    st.caption(f"Ciclo: {ped['ciclo_nombre']}")
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
                            if st.button("❌ Rechazar", key=f"rej_{ped['id']}", use_container_width=True):
                                actualizar_estado_pedido(ped["id"], "rechazado")
                                st.rerun()
                        with c3:
                            if st.button("📦 Entregar", key=f"ent_{ped['id']}", use_container_width=True):
                                entregar_pedido(ped["id"])
                                st.rerun()
                    elif estado == "aprobado":
                        if st.button("📦 Marcar Entregado", key=f"entd_{ped['id']}", use_container_width=True):
                            entregar_pedido(ped["id"])
                            st.rerun()

    # --- TAB CATÁLOGO ---
    with tab3:
        st.markdown("### Catálogo de Productos")

        productos = get_productos(solo_activos=False)

        with st.expander("➕ Agregar Producto", expanded=not productos):
            with st.form("nuevo_prod"):
                nombre = st.text_input("Nombre del producto")
                col1, col2 = st.columns(2)
                with col1:
                    categoria = st.text_input("Categoría", value="General")
                with col2:
                    unidad = st.selectbox("Unidad", ["pieza", "paquete", "caja", "resma", "rollo", "bote", "litro", "kilo"])
                stock = st.number_input("Stock en almacén", min_value=0, value=0)

                if st.form_submit_button("Agregar", use_container_width=True):
                    if nombre.strip():
                        agregar_producto(nombre.strip(), categoria.strip(), unidad, stock)
                        st.success(f"Producto '{nombre}' agregado")
                        st.rerun()
                    else:
                        st.error("El nombre es obligatorio")

        if productos:
            for p in productos:
                estado_txt = "✅ Activo" if p["activo"] else "❌ Inactivo"
                with st.expander(f"{p['nombre']} — {p['categoria']} | {estado_txt}"):
                    with st.form(f"edit_{p['id']}"):
                        n = st.text_input("Nombre", value=p["nombre"], key=f"n_{p['id']}")
                        c1, c2 = st.columns(2)
                        with c1:
                            cat = st.text_input("Categoría", value=p["categoria"], key=f"cat_{p['id']}")
                        with c2:
                            unidades = ["pieza", "paquete", "caja", "resma", "rollo", "bote", "litro", "kilo"]
                            idx = unidades.index(p["unidad"]) if p["unidad"] in unidades else 0
                            uni = st.selectbox("Unidad", unidades, index=idx, key=f"uni_{p['id']}")
                        s = st.number_input("Stock", min_value=0, value=p["stock_almacen"], key=f"s_{p['id']}")
                        act = st.checkbox("Activo", value=bool(p["activo"]), key=f"act_{p['id']}")

                        if st.form_submit_button("Guardar", use_container_width=True):
                            actualizar_producto(p["id"], n, cat, uni, s, int(act))
                            st.success("Producto actualizado")
                            st.rerun()
        else:
            st.info("No hay productos en el catálogo. Agrega productos arriba o espera el catálogo de Jorge Alvarez.")

    # --- TAB CICLOS ---
    with tab4:
        st.markdown("### Ciclos de Pedido")
        ciclo_activo = get_ciclo_activo()

        if ciclo_activo:
            dias = (datetime.strptime(ciclo_activo["fecha_cierre"], "%Y-%m-%d") - datetime.now()).days
            st.success(f"**Ciclo activo:** {ciclo_activo['nombre']} ({max(0, dias)} días restantes)")
            if st.button("🔒 Cerrar ciclo actual", use_container_width=True):
                cerrar_ciclo(ciclo_activo["id"])
                st.success("Ciclo cerrado")
                st.rerun()
        else:
            st.warning("No hay ciclo activo")

        with st.expander("➕ Crear nuevo ciclo"):
            with st.form("nuevo_ciclo"):
                hoy = datetime.now()
                nombre_ciclo = st.text_input(
                    "Nombre del ciclo",
                    value=f"Ciclo {hoy.strftime('%B %Y')}",
                )
                c1, c2 = st.columns(2)
                with c1:
                    f_inicio = st.date_input("Fecha inicio", value=hoy)
                with c2:
                    f_cierre = st.date_input("Fecha cierre", value=hoy + timedelta(days=20))

                if st.form_submit_button("Crear Ciclo", type="primary", use_container_width=True):
                    crear_ciclo(
                        nombre_ciclo,
                        f_inicio.strftime("%Y-%m-%d"),
                        f_cierre.strftime("%Y-%m-%d"),
                    )
                    st.success(f"Ciclo '{nombre_ciclo}' creado")
                    st.rerun()

        st.markdown("### Historial de ciclos")
        for c in get_ciclos():
            emoji = "🟢" if c["estado"] == "abierto" else "⚫"
            st.markdown(
                f"{emoji} **{c['nombre']}** | {c['fecha_inicio']} → {c['fecha_cierre']} | {c['estado'].upper()}"
            )

    # --- TAB ÁREAS ---
    with tab5:
        st.markdown("### Áreas y Líderes")
        for a in areas:
            with st.expander(f"🏢 {a['nombre']}"):
                lider = st.text_input(
                    "Líder del área",
                    value=a["lider"] or "",
                    key=f"lider_{a['id']}",
                    placeholder="Nombre del líder",
                )
                if st.button("Guardar", key=f"save_lider_{a['id']}", use_container_width=True):
                    actualizar_lider(a["id"], lider)
                    st.success(f"Líder actualizado para {a['nombre']}")
                    st.rerun()

                inv = get_inventario_area(a["id"])
                if inv:
                    st.markdown("**Inventario del área:**")
                    for item in inv:
                        st.markdown(f"- {item['producto_nombre']}: {item['cantidad']} {item['unidad']}")

# --- Footer ---
st.divider()
st.caption("Sistema de Inventario y Requisiciones — Almacén v1.0")
