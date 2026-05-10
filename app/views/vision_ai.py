"""
Página de Visión AI - Control de Stock Visual Profesional
3 Tabs: Galería de Referencia | Conteo de Estante | Discrepancias
"""
import streamlit as st
from app.utils.api import api_get
import requests
from app.config import API_URL


def render():
    st.markdown("""
    <style>
    .vision-header {
        background: linear-gradient(90deg, #10b981, #0ea5e9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .badge-ref { background: rgba(16,185,129,0.15); color: #10b981; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; border: 1px solid rgba(16,185,129,0.3); }
    .badge-noref { background: rgba(239,68,68,0.15); color: #ef4444; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; border: 1px solid rgba(239,68,68,0.3); }
    .discrep-card {
        padding: 12px;
        margin-bottom: 8px;
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        border-left: 4px solid #10b981;
    }
    .discrep-card.faltante { border-left-color: #ef4444; }
    .discrep-card.sobrante { border-left-color: #f59e0b; }
    </style>
    <div class="vision-header">📸 Visión AI — Control de Stock Visual</div>
    <p style="color:#94a3b8; margin-top:0;">ResNet50 + YOLOv8: detecta productos en fotos del almacén y compara con el inventario teórico.</p>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🏷️ Galería de Referencia", "📸 Conteo de Estante", "⚠️ Discrepancias"])

    with tab1:
        _render_galeria()

    with tab2:
        _render_conteo()

    with tab3:
        _render_discrepancias()


def _render_galeria():
    st.markdown("#### Galería de Imágenes de Referencia")

    refs = api_get("/api/v1/vision/referencias", use_cache=False) or []
    if not refs:
        st.info("No hay imágenes de referencia registradas.")
        return

    # Métricas
    con_img = len([r for r in refs if r["num_imagenes"] > 0])
    sin_img = len([r for r in refs if r["num_imagenes"] == 0])
    total_img = sum(r["num_imagenes"] for r in refs)

    cols = st.columns(3)
    cols[0].metric("Productos", len(refs))
    cols[1].metric("Con referencia", con_img)
    cols[2].metric("Total fotos", total_img)

    # Re-entrenar
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Re-entrenar Modelo Visual", type="primary"):
            with st.spinner("Re-calculando embeddings..."):
                try:
                    r = requests.post(f"{API_URL}/api/v1/vision/entrenar", timeout=60)
                    if r.status_code == 200:
                        st.success("Modelo re-entrenado correctamente")
                        st.rerun()
                    else:
                        st.error(f"Error: {r.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")

    # Grid de productos
    # Mostrar en columnas de 4
    for i in range(0, len(refs), 4):
        row_items = refs[i:i+4]
        cols = st.columns(4)
        for col, item in zip(cols, row_items):
            with col:
                badge = f'<span class="badge-ref">{item["num_imagenes"]} foto(s)</span>' if item["num_imagenes"] > 0 else '<span class="badge-noref">Sin foto</span>'
                st.markdown(f"""
                <div style="text-align:center; margin-bottom:8px;">
                    <strong style="font-size:0.9rem;">{item['nombre']}</strong><br/>
                    <span style="color:#64748b; font-size:0.75rem;">{item['sku']}</span><br/>
                    {badge}
                </div>
                """, unsafe_allow_html=True)

                # Mostrar todas las imagenes con boton eliminar
                if item["imagenes"]:
                    st.markdown("<div style='font-size:0.75rem; color:#64748b; margin-bottom:4px;'>Imagenes de referencia:</div>", unsafe_allow_html=True)
                    for img in item["imagenes"]:
                        col_img, col_del = st.columns([4, 1])
                        with col_img:
                            try:
                                st.image(img["ruta"], use_container_width=True)
                            except Exception:
                                st.caption(f"(img id={img['id']})")
                        with col_del:
                            st.markdown("<br/>", unsafe_allow_html=True)
                            if st.button("❌", key=f"del_{img['id']}", help="Eliminar esta foto"):
                                with st.spinner("Eliminando..."):
                                    try:
                                        r = requests.delete(
                                            f"{API_URL}/api/v1/vision/referencias/{img['id']}",
                                            timeout=10
                                        )
                                        if r.status_code == 200:
                                            st.success("Eliminada")
                                            st.rerun()
                                        else:
                                            st.error(f"Error: {r.text}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                else:
                    st.markdown("""
                    <div style="height:80px; background:rgba(255,255,255,0.03); border-radius:8px; display:flex; align-items:center; justify-content:center; color:#64748b; font-size:0.8rem; margin-bottom:8px;">
                        Sin imagen
                    </div>
                    """, unsafe_allow_html=True)

                # Subir nueva foto
                with st.expander("➕ Agregar foto"):
                    nueva_foto = st.file_uploader(
                        f"Foto para {item['nombre']}",
                        type=['jpg', 'jpeg', 'png'],
                        key=f"upload_{item['producto_id']}"
                    )
                    if nueva_foto is not None:
                        if st.button("Subir", key=f"btn_upload_{item['producto_id']}"):
                            with st.spinner("Subiendo..."):
                                try:
                                    files = {"archivo": (nueva_foto.name, nueva_foto.getvalue(), nueva_foto.type)}
                                    data = {"producto_id": item["producto_id"]}
                                    r = requests.post(
                                        f"{API_URL}/api/v1/vision/referencias",
                                        files=files,
                                        data=data,
                                        timeout=30
                                    )
                                    if r.status_code == 200:
                                        st.success("Foto agregada")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {r.text}")
                                except Exception as e:
                                    st.error(f"Error: {e}")


def _render_conteo():
    st.markdown("#### Conteo Visual de Estante / Almacén")

    st.markdown("""
    <div style="padding:12px; background:rgba(14,165,233,0.08); border-radius:8px; border:1px solid rgba(14,165,233,0.2); margin-bottom:1rem;">
        <strong>Como funciona:</strong> Sube una foto del estante. YOLO detecta objetos y ResNet50 los compara con la galería de referencia para identificar productos reales.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        imagen = st.file_uploader("📁 Sube foto del estante", type=['jpg', 'jpeg', 'png'])
    with col2:
        conf_yolo = st.slider("Confianza YOLO", 0.05, 0.5, 0.15, 0.05)
        umbral_sim = st.slider("Umbral similitud", 0.40, 0.90, 0.65, 0.05)

    if imagen is not None:
        st.image(imagen, caption="Vista previa", use_container_width=True)

        if st.button("🔍 Analizar con IA", type="primary", use_container_width=True):
            with st.spinner("Detectando y clasificando objetos..."):
                try:
                    files = {"archivo": (imagen.name, imagen.getvalue(), imagen.type)}
                    r = requests.post(
                        f"{API_URL}/api/v1/vision/conteo?confianza_min_yolo={conf_yolo}&umbral_similitud={umbral_sim}",
                        files=files,
                        timeout=60
                    )

                    if r.status_code == 200:
                        resultado = r.json()
                        conteo_ia = resultado["conteo_ia"]
                        discrepancias = resultado["discrepancias"]

                        # Resultados del conteo
                        st.markdown("**Resultados del análisis**")
                        cols = st.columns(4)
                        cols[0].metric("Regiones YOLO", conteo_ia["total_regiones"])
                        cols[1].metric("Productos ID", len(conteo_ia["conteo"]))
                        cols[2].metric("No clasificados", conteo_ia["no_clasificados"])
                        cols[3].metric("Discrepancias", len([d for d in discrepancias if d["estado"] != "OK"]))

                        # Tabla de productos detectados
                        st.markdown("**Productos detectados**")
                        productos = list(conteo_ia.get("productos_enriquecidos", {}).values())
                        if productos:
                            for p in productos:
                                st.markdown(f"""
                                <div style="display:flex; justify-content:space-between; padding:8px; background:rgba(255,255,255,0.03); border-radius:8px; margin-bottom:4px;">
                                    <strong>{p['nombre']}</strong>
                                    <span style="color:#0ea5e9; font-weight:700;">{p['cantidad_detectada']} uds</span>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.warning("No se detectaron productos conocidos en la imagen.")

                        # Guardar en session state para la pestaña de discrepancias
                        st.session_state["ultimas_discrepancias"] = discrepancias

                        # Mostrar discrepancias resumen
                        desc_con_problemas = [d for d in discrepancias if d["estado"] != "OK"]
                        if desc_con_problemas:
                            st.markdown("**⚠️ Discrepancias detectadas**")
                            for d in desc_con_problemas[:10]:
                                color = "#ef4444" if d["estado"] == "FALTANTE" else "#f59e0b"
                                icon = "🔴" if d["estado"] == "FALTANTE" else "🟠"
                                st.markdown(f"""
                                <div class="discrep-card {'faltante' if d['estado']=='FALTANTE' else 'sobrante'}">
                                    <div style="display:flex; justify-content:space-between;">
                                        <strong>{icon} {d['nombre']}</strong>
                                        <span style="color:{color}; font-weight:700;">{d['estado']}</span>
                                    </div>
                                    <div style="font-size:0.8rem; color:#94a3b8; margin-top:4px;">
                                        Stock BD: <strong>{d['stock_bd']}</strong> · Detectado IA: <strong>{d['detectado_ia']}</strong> · Diferencia: <strong>{d['diferencia']:+d}</strong>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.success("✅ Todo coincide con el inventario teórico.")

                    else:
                        st.error(f"Error del servidor: {r.status_code} — {r.text[:300]}")
                except Exception as e:
                    st.error(f"Error al analizar: {e}")


def _render_discrepancias():
    st.markdown("#### Discrepancias Stock BD vs IA")

    discrepancias = st.session_state.get("ultimas_discrepancias", [])
    if not discrepancias:
        st.info("Aún no has realizado ningún conteo visual. Ve a la pestaña 'Conteo de Estante' y sube una foto.")
        return

    # Filtros
    estados = st.multiselect("Filtrar estado:", ["OK", "FALTANTE", "SOBRANTE"], default=["FALTANTE", "SOBRANTE"])
    discrepancias = [d for d in discrepancias if d["estado"] in estados]

    # Métricas
    faltantes = len([d for d in discrepancias if d["estado"] == "FALTANTE"])
    sobrantes = len([d for d in discrepancias if d["estado"] == "SOBRANTE"])
    ok = len([d for d in discrepancias if d["estado"] == "OK"])

    cols = st.columns(3)
    cols[0].metric("Faltantes", faltantes, delta_color="inverse")
    cols[1].metric("Sobrantes", sobrantes)
    cols[2].metric("OK", ok)

    st.markdown("---")

    if not discrepancias:
        st.success("No hay discrepancias con los filtros seleccionados.")
        return

    # Tabla
    for d in discrepancias:
        if d["estado"] == "OK":
            color = "#10b981"
            clase = ""
            icon = "🟢"
        elif d["estado"] == "FALTANTE":
            color = "#ef4444"
            clase = "faltante"
            icon = "🔴"
        else:
            color = "#f59e0b"
            clase = "sobrante"
            icon = "🟠"

        st.markdown(f"""
        <div class="discrep-card {clase}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:1.1rem;">{icon}</span>
                    <strong style="font-size:0.95rem;">{d['nombre']}</strong>
                    <span style="color:#64748b; font-size:0.75rem; margin-left:6px;">({d['categoria']})</span>
                </div>
                <span style="color:{color}; font-weight:700; font-size:0.9rem;">{d['estado']}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:0.85rem; color:#94a3b8;">
                <span>Stock BD: <strong style="color:#e2e8f0;">{d['stock_bd']}</strong></span>
                <span>Detectado IA: <strong style="color:#e2e8f0;">{d['detectado_ia']}</strong></span>
                <span>Diferencia: <strong style="color:{color};">{d['diferencia']:+d}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
