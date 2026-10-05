"""
Ventas - TPV Profesional + Dashboard + Historial
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import base64
import io
import time
from typing import Optional

from app.db import DatabaseAccess

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
from app.utils.helpers import to_excel, format_currency


def _obj_to_dict(obj):
    if hasattr(obj, '__dict__'):
        result = {}
        for k, v in obj.__dict__.items():
            if k.startswith('_'):
                continue
            if hasattr(v, 'isoformat'):  # datetime objects
                result[k] = v.isoformat()
            elif isinstance(v, list):
                result[k] = [_obj_to_dict(item) if hasattr(item, '__dict__') else item for item in v]
            else:
                result[k] = v
        return result
    return obj


def _format_fecha(fecha):
    """Formatea fecha para display."""
    if hasattr(fecha, 'strftime'):
        return fecha.strftime('%Y-%m-%d %H:%M')
    fecha_str = str(fecha)
    return fecha_str[:16].replace('T', ' ') if fecha_str else ''


def _get_ventas_data():
    """Obtiene datos para ventas usando db directamente."""
    db = DatabaseAccess()
    try:
        productos = db.get_productos()
        inventarios = db.get_inventario()
        tickets = db.get_tickets(limite=LIMITE_TICKETS_DASHBOARD)
        
        productos = [_obj_to_dict(p) for p in productos]
        inventarios = [_obj_to_dict(i) for i in inventarios]
        tickets = [_obj_to_dict(t) for t in tickets]
        
        return productos, inventarios, tickets
    finally:
        db.close()


from app.utils.state import (
    init_tpv_state, get_tpv_carrito, set_tpv_carrito, limpiar_carrito,
    agregar_linea_carrito, actualizar_cantidad_linea, calcular_total_carrito, get_cajeros
)


# ============================================================================
# CONSTANTES
# ============================================================================

CAJEROS = get_cajeros()
METODOS_PAGO = ["efectivo", "tarjeta", "transferencia"]
PRODUCTOS_POR_PAGINA = 12


DIRECTORIO_IMAGENES = 'docs/img_productos'
EXTENSIONES_IMAGEN = ['.jpg', '.jpeg', '.png']
THUMBNAIL_TAMANIO = (100, 100)


def _candidatos_imagen_directo(imagen_url):
    """Devuelve la lista de rutas candidatas si la imagen_url existe en disco."""
    return [imagen_url] if imagen_url and os.path.exists(imagen_url) else []


def _candidatos_imagen_documentos(nombre_producto):
    """Busca en docs/img_productos/ ficheros cuyo nombre coincide con el producto."""
    if not os.path.exists(DIRECTORIO_IMAGENES):
        return []

    candidatos = []
    for fname in os.listdir(DIRECTORIO_IMAGENES):
        lower = fname.lower()
        if not any(lower.endswith(ext) for ext in EXTENSIONES_IMAGEN):
            continue
        sin_extension = lower.rsplit('.', 1)[0]
        if nombre_producto in lower or sin_extension in nombre_producto:
            candidatos.append(os.path.join(DIRECTORIO_IMAGENES, fname))
    return candidatos


def _candidatos_imagen(producto):
    """Devuelve todas las rutas candidatas de imagen para el producto."""
    nombre = producto.get('nombre', '').lower().replace(' ', '_')
    return _candidatos_imagen_directo(producto.get('imagen_url')) + _candidatos_imagen_documentos(nombre)


def _imagen_como_data_uri(path):
    """Redimensiona la imagen y la devuelve como data URI, o None si falla."""
    if not PIL_AVAILABLE:
        return path

    with Image.open(path) as img:
        img.thumbnail(THUMBNAIL_TAMANIO, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        fmt = 'PNG' if path.lower().endswith('.png') else 'JPEG'
        img.save(buffer, format=fmt)
        return f"data:image/{fmt.lower()};base64," + base64.b64encode(buffer.getvalue()).decode()


def _buscar_imagen_producto(producto: dict) -> Optional[str]:
    """Intenta encontrar una imagen para el producto (redimensionada a thumbnail)."""
    for path in _candidatos_imagen(producto):
        try:
            return _imagen_como_data_uri(path)
        except Exception:
            continue
    return None


def _get_stock(producto_id: int, inventarios: list) -> int:
    for inv in inventarios:
        if inv.get('producto_id') == producto_id:
            return inv.get('cantidad', 0)
    return 0


# ============================================================================
# RENDER PRINCIPAL
# ============================================================================

def render():
    st.markdown("<h2 style='margin-bottom: 20px;'>💰 Gestión de Ventas</h2>", unsafe_allow_html=True)

    tab_dashboard, tab_historial, tab_tpv = st.tabs([
        "📊 Dashboard",
        "📋 Historial de Tickets",
        "💰 TPV"
    ])

    with tab_tpv:
        render_tpv()

    with tab_dashboard:
        render_dashboard()

    with tab_historial:
        render_historial()


# ============================================================================
# TAB TPV
# ============================================================================

def render_tpv():
    init_tpv_state()

    # Si se acaba de cobrar y hay ticket para mostrar
    if st.session_state.get('tpv_mostrar_ticket') and st.session_state.get('tpv_ticket_reciente'):
        render_ticket_post_cobro()
        return

    # Si estamos en modal de cobro, mostrar SOLO el modal centrado
    if st.session_state.get('tpv_mostrar_cobro'):
        render_cobro_modal()
        return

    col_izq, col_der = st.columns([35, 65])

    with col_izq:
        render_panel_ticket()

    with col_der:
        render_panel_productos()


DIV_CLOSE = "</div>"

COLS_LINEA_CARRITO = [1, 4, 2, 2, 1, 1, 1]
DESCUENTOS_RAPIDOS = (5, 10, 20)


def _linea_seleccionada(idx):
    """Indica si la línea indicada es la seleccionada en el TPV."""
    return st.session_state.get('tpv_linea_seleccionada') == idx


def _estilos_linea_seleccionada(seleccionada):
    """Devuelve (color_fondo, color_borde) de la línea del carrito."""
    if seleccionada:
        return "rgba(59, 130, 246,0.1)", "#3b82f6"
    return "transparent", "rgba(255,255,255,0.05)"


def _seleccionar_linea(idx):
    """Marca la línea como seleccionada y limpia el teclado."""
    st.session_state['tpv_linea_seleccionada'] = idx
    st.session_state['tpv_teclado_buffer'] = ''
    st.rerun()


def _render_celda_seleccion(idx, col):
    """Renderiza el botón que selecciona la línea."""
    with col:
        marcador = '●' if _linea_seleccionada(idx) else '○'
        if st.button(marcador, key=f"sel_linea_{idx}", help="Seleccionar línea"):
            _seleccionar_linea(idx)


def _render_celda_datos(linea, cols):
    """Renderiza descripción, precio unitario y subtotal de la línea."""
    with cols[1]:
        st.markdown(f"<div style='font-size: 0.9rem; color: #f8fafc;'>{linea['cantidad']} x {linea['nombre']}</div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f"<div style='font-size: 0.85rem; color: #94a3b8; text-align: right;'>€{linea['precio_unitario']:.2f}</div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"<div style='font-size: 0.9rem; color: #10b981; text-align: right; font-weight: 600;'>€{linea['subtotal']:.2f}</div>", unsafe_allow_html=True)


def _ajustar_linea(idx, delta):
    """Aplica un delta de cantidad a la línea y recarga."""
    actualizar_cantidad_linea(idx, delta)
    st.rerun()


def _render_controles_cantidad(linea, idx, cols):
    """Renderiza los botones de +/- y eliminar de la línea."""
    with cols[4]:
        if st.button("➖", key=f"btn_menos_{idx}"):
            _ajustar_linea(idx, linea['cantidad'] - 1)
    with cols[5]:
        if st.button("➕", key=f"btn_mas_{idx}"):
            _ajustar_linea(idx, linea['cantidad'] + 1)
    with cols[6]:
        if st.button("🗑️", key=f"btn_del_{idx}"):
            _ajustar_linea(idx, 0)


def _render_linea_carrito(linea, idx):
    """Renderiza una línea completa del carrito."""
    cols = st.columns(COLS_LINEA_CARRITO)

    _render_celda_seleccion(idx, cols[0])
    _render_celda_datos(linea, cols)
    _render_controles_cantidad(linea, idx, cols)

    bg_color, border_color = _estilos_linea_seleccionada(_linea_seleccionada(idx))
    st.markdown(f"<div style='background: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; margin: 2px -5px; padding: 4px 8px;'></div>", unsafe_allow_html=True)


def _render_lineas_carrito(carrito):
    """Renderiza el bloque con scroll del carrito, o el mensaje de ticket vacío."""
    st.markdown("<div class='tpv-panel-scroll'>", unsafe_allow_html=True)

    if not carrito:
        st.markdown("<p style='color: #64748b; text-align: center; padding: 30px 0;'>🛒 Ticket vacío<br>Haz clic en un producto para agregarlo</p>", unsafe_allow_html=True)
    else:
        for idx, linea in enumerate(carrito):
            _render_linea_carrito(linea, idx)

    st.markdown(DIV_CLOSE, unsafe_allow_html=True)


def _render_totales():
    """Muestra el total del carrito y el desglose de descuento."""
    total = calcular_total_carrito()
    descuento_pct = st.session_state.get('tpv_descuento', 0)

    if descuento_pct > 0:
        total_con_desc = round(total * (1 - descuento_pct / 100), 2)
        st.markdown(f"<p style='text-align: center; color: #f59e0b; font-size: 0.85rem;'>Descuento: {descuento_pct}% | Original: €{total:.2f}</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: #3b82f6; margin: 5px 0;'>Total: €{total_con_desc:.2f}</h2>", unsafe_allow_html=True)
        return

    st.markdown(f"<h2 style='text-align: center; color: #3b82f6; margin: 10px 0;'>Total: €{total:.2f}</h2>", unsafe_allow_html=True)


def _alternar_descuento(pct):
    """Activa el descuento o lo desactiva si ya estaba activo."""
    st.session_state['tpv_descuento'] = 0 if st.session_state.get('tpv_descuento') == pct else pct
    st.rerun()


def _render_descuentos_rapidos():
    """Muestra los botones de descuento rápido."""
    for col, pct in zip(st.columns(len(DESCUENTOS_RAPIDOS)), DESCUENTOS_RAPIDOS):
        with col:
            if st.button(f"DTO {pct}%", key=f"dto_{pct}", width="stretch"):
                _alternar_descuento(pct)


def _css_boton_accion(pos, color_inicio, color_fin, color_texto, peso, sombra=None):
    """Genera el CSS del gradiente de un botón de acción del TPV."""
    regla_sombra = f"\n    box-shadow: 0 4px 12px {sombra} !important;" if sombra else ""
    return f"""
<style>
div[data-testid="stHorizontalBlock"] div:nth-child({pos}) button[data-testid="baseButton-primary"],
div[data-testid="stHorizontalBlock"] div:nth-child({pos}) button[data-testid="baseButton-secondary"] {{
    background: linear-gradient(135deg, {color_inicio}, {color_fin}) !important;
    color: {color_texto} !important; border: none !important;
    border-radius: 10px !important; font-weight: {peso} !important;{regla_sombra}
}}
</style>
"""


def _abrir_cobro(metodo):
    """Selecciona el método de pago y abre el modal de cobro."""
    st.session_state['tpv_metodo_pago'] = metodo
    st.session_state['tpv_mostrar_cobro'] = True
    st.rerun()


def _abrir_cobro_efectivo():
    _abrir_cobro('efectivo')


def _abrir_cobro_tarjeta():
    _abrir_cobro('tarjeta')


def _limpiar_ticket():
    """Limpia el carrito y el descuento aplicado."""
    st.session_state['tpv_descuento'] = 0
    limpiar_carrito()
    st.rerun()


# (etiqueta, clave, tipo, css, requiere_carrito_para_habilitarse, accion)
ACCIONES_TPV = (
    (
        "💶 Efectivo", "btn_efectivo_grad", "primary", True, _abrir_cobro_efectivo,
        _css_boton_accion(1, "#10b981", "#059669", "white", 700, "rgba(16,185,129,0.3)"),
    ),
    (
        "💳 Tarjeta", "btn_tarjeta_grad", "primary", True, _abrir_cobro_tarjeta,
        _css_boton_accion(2, "#3b82f6", "#1d4ed8", "#0f172a", 700, "rgba(59,130,246,0.3)"),
    ),
    (
        "🧹 Limpiar", "btn_limpiar_grad", "secondary", False, _limpiar_ticket,
        _css_boton_accion(3, "#64748b", "#475569", "white", 600),
    ),
)


def _render_botones_accion(carrito):
    """Renderiza los botones de cobro y limpieza del TPV."""
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    for col, (etiqueta, clave, tipo, requiere_carrito, accion, css) in zip(st.columns(len(ACCIONES_TPV)), ACCIONES_TPV):
        with col:
            st.markdown(css, unsafe_allow_html=True)
            if st.button(etiqueta, width="stretch", type=tipo, disabled=requiere_carrito and not carrito, key=clave):
                accion()


def render_panel_ticket():
    """Panel izquierdo: Ticket actual con scroll, barcode, descuento y alertas."""
    st.markdown("<div style='background: rgba(30,41,59,0.6); border-radius: 10px; padding: 15px; border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    cajero = st.selectbox("🧑‍💼 Cajero", CAJEROS, key="tpv_cajero_select")
    st.session_state['tpv_cajero'] = cajero
    st.markdown(f"<p style='color: #64748b; font-size: 0.8rem;'>📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>", unsafe_allow_html=True)

    barcode = st.text_input("🔍 Código de barras / Nombre", placeholder="Escanea o escribe...", key="tpv_barcode", label_visibility="collapsed")
    if barcode:
        _procesar_barcode(barcode)

    st.markdown("---")

    carrito = get_tpv_carrito()

    _render_lineas_carrito(carrito)

    st.markdown("---")

    if carrito:
        render_teclado_numerico()

    st.markdown("---")

    _render_totales()

    if carrito:
        _render_descuentos_rapidos()

    _render_botones_accion(carrito)

    if carrito:
        _render_alerta_stock_bajo(carrito)

    st.markdown(DIV_CLOSE, unsafe_allow_html=True)


def _procesar_barcode(texto: str):
    """Busca producto por código de barras o nombre y lo agrega al carrito."""
    texto = texto.strip().lower()
    if not texto:
        return
    productos, _, _ = _get_ventas_data()
    for prod in productos:
        sku = (prod.get('sku') or '').lower()
        cod = (prod.get('codigo_barras') or '').lower()
        nombre = (prod.get('nombre') or '').lower()
        if texto == sku or texto == cod or texto in nombre:
            agregar_linea_carrito(prod)
            st.session_state['tpv_barcode'] = ''
            st.rerun()
            return
    st.warning(f"❌ Producto no encontrado: '{texto}'")


def _render_alerta_stock_bajo(carrito: list):
    """Muestra alerta si algún producto del carrito queda con stock < 5."""
    _, inventarios, _ = _get_ventas_data()
    inv_dict = {i['producto_id']: i['cantidad'] for i in inventarios}
    alertas = []
    for linea in carrito:
        stock_restante = inv_dict.get(linea['producto_id'], 0)
        if stock_restante < 5:
            alertas.append(f"⚠️ {linea['nombre']}: quedan {stock_restante} unidades")
    if alertas:
        st.markdown(f"<div class='alerta-stock-bajo'>{'<br>'.join(alertas)}</div>", unsafe_allow_html=True)


TECLADO_NUMERICO = (
    ['7', '8', '9'],
    ['4', '5', '6'],
    ['1', '2', '3'],
    ['0', '.', 'CLR'],
)
TECLA_LIMPIAR = 'CLR'
BILLETES_RAPIDOS = (5, 10, 20, 50)


def _pulsar_tecla(tecla):
    """Añade la tecla al buffer o lo limpia si es CLR."""
    if tecla == TECLA_LIMPIAR:
        st.session_state['tpv_teclado_buffer'] = ''
    else:
        st.session_state['tpv_teclado_buffer'] += tecla
    st.rerun()


def _render_teclado_numerico():
    """Renderiza la rejilla de teclas numéricas."""
    for fila in TECLADO_NUMERICO:
        cols = st.columns(len(fila))
        for col, tecla in zip(cols, fila):
            with col:
                if st.button(tecla, key=f"tecla_{tecla}", width="stretch"):
                    _pulsar_tecla(tecla)


def _aplicar_cantidad_teclado(linea_sel, buffer):
    """Muestra el botón de aplicar cantidad escrita con el teclado."""
    if not buffer:
        return

    try:
        cantidad = int(float(buffer))
    except ValueError:
        st.error("Cantidad inválida")
        return

    if st.button("✅ Aplicar Cantidad", width="stretch", type="primary"):
        actualizar_cantidad_linea(linea_sel, cantidad)
        st.rerun()


def _render_aplicar_rapido(linea_sel):
    """Muestra el input numérico alternative al teclado."""
    st.markdown("<p style='color: #64748b; font-size: 0.75rem; text-align: center; margin-top: 10px;'>— o escribe directamente —</p>", unsafe_allow_html=True)
    cantidad_rapida = st.number_input(
        "Cantidad",
        min_value=1,
        max_value=999,
        value=1,
        key=f"cantidad_rapida_{linea_sel}",
        label_visibility="collapsed"
    )
    if st.button("✅ Aplicar", width="stretch", key=f"btn_aplicar_rapido_{linea_sel}"):
        actualizar_cantidad_linea(linea_sel, int(cantidad_rapida))
        st.rerun()


def render_teclado_numerico():
    """Teclado numérico funcional para cambiar cantidades."""
    linea_sel = st.session_state.get('tpv_linea_seleccionada')
    if linea_sel is None:
        st.markdown("<p style='color: #64748b; font-size: 0.8rem; text-align: center;'>👆 Selecciona una línea y usa el teclado para cambiar la cantidad</p>", unsafe_allow_html=True)
        return

    buffer = st.session_state.get('tpv_teclado_buffer', '')
    st.markdown(f"<p style='color: #3b82f6; font-size: 1.2rem; text-align: center; margin: 5px 0;'>Cantidad: {buffer if buffer else '...'}</p>", unsafe_allow_html=True)

    _render_teclado_numerico()
    _aplicar_cantidad_teclado(linea_sel, buffer)
    _render_aplicar_rapido(linea_sel)


CSS_MODAL_COBRO = """
<style>
@keyframes modalFadeIn {{ from {{ opacity:0; transform:scale(0.92); }} to {{ opacity:1; transform:scale(1); }} }}
@keyframes iconoPop {{ 0% {{ transform:scale(0); }} 50% {{ transform:scale(1.2); }} 100% {{ transform:scale(1); }} }}
.modal-caja {{
    animation: modalFadeIn 0.35s ease forwards;
    background: linear-gradient(145deg, rgba(30,41,59,0.98), rgba(15,23,42,1));
    border: 1px solid rgba(59, 130, 246,0.25);
    border-radius: 18px;
    padding: 25px 20px;
    box-shadow: 0 0 40px rgba(59, 130, 246,0.12);
    text-align: center;
    margin: 15px 0;
}}
.modal-icon {{ font-size: 3rem; display:inline-block; animation: iconoPop 0.5s ease 0.1s both; margin-bottom: 5px; }}
.modal-titulo {{ color: #3b82f6; font-size: 1.6rem; font-weight: 700; }}
.modal-total {{ color: #3b82f6; font-size: 1.9rem; font-weight: 800; margin: 8px 0; }}
.modal-sub {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}
.modal-cambio {{ color: #10b981; font-size: 1.15rem; font-weight: 700; margin: 6px 0 12px 0; }}
</style>
<div class="modal-caja">
    <div class="modal-icon">{icono}</div>
    <div class="modal-titulo">Cobrar</div>
    <div class="modal-total">Total: €{total:.2f}</div>
    <div class="modal-sub">Método: {metodo_mayusculas}</div>
</div>
"""

AUDIO_COBRO = """
<audio id="sonido-cobro" preload="auto">
  <source src="https://assets.mixkit.co/active_storage/sfx/2003/2003-preview.mp3" type="audio/mpeg">
</audio>
<script>
  setTimeout(() => {
    const input = document.querySelector('input[data-testid="stNumberInput"]');
    if (input) input.focus();
  }, 400);
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      const checkbox = document.querySelector('input[type="checkbox"]');
      const btn = document.querySelector('button[kind="primary"]');
      if (checkbox && checkbox.checked && btn && !btn.disabled) { btn.click(); }
    }
  });
</script>
"""


def _pulsar_billete(valor):
    """Selecciona un billete como importe de entrega."""
    st.session_state['tpv_billete_pulsado'] = float(valor)
    st.rerun()


def _importe_entrega_por_defecto(total):
    """Devuelve la entrega sugerida: billete pulsado si cubre el total, si no total*1.1."""
    billete_pulsado = st.session_state.pop('tpv_billete_pulsado', None)
    if billete_pulsado and billete_pulsado >= total:
        return float(billete_pulsado)
    return float(total * 1.1)


def _seccion_entrega_efectivo(total):
    """Renderiza los billetes rápidos y el input de entrega. Devuelve (entrega, cambio)."""
    st.markdown("<p style='color:#64748b; font-size:0.75rem; margin:0 0 6px 0; text-align:center;'>Rápido:</p>", unsafe_allow_html=True)

    for col, valor in zip(st.columns(len(BILLETES_RAPIDOS)), BILLETES_RAPIDOS):
        with col:
            if st.button(f"€{valor}", key=f"billete_{valor}", width="stretch"):
                _pulsar_billete(valor)

    entrega = st.number_input(
        "💶 Entrega (€)", min_value=float(total), value=_importe_entrega_por_defecto(total),
        step=0.5, format="%.2f", key="modal_entrega_v2"
    )
    cambio = round(entrega - total, 2)
    st.markdown(f"<p class='modal-cambio' style='text-align:center;'>Cambio: €{cambio:.2f}</p>", unsafe_allow_html=True)

    return entrega, cambio


def _lineas_ticket_desde_carrito():
    """Construye las líneas del ticket a partir del carrito actual."""
    return [
        {
            "producto_id": linea['producto_id'],
            "cantidad": linea['cantidad'],
            "precio_unitario": linea['precio_unitario'],
            "subtotal": linea['cantidad'] * linea['precio_unitario'],
        }
        for linea in get_tpv_carrito()
    ]


def _datos_ticket(metodo, entrega, cambio):
    """Construye el payload del ticket."""
    es_efectivo = metodo == 'efectivo'
    return {
        "cajero": st.session_state['tpv_cajero'],
        "metodo_pago": metodo,
        "entrega_efectivo": entrega if es_efectivo else None,
        "cambio": cambio if es_efectivo else None,
        "total": calcular_total_carrito(),
        "lineas": _lineas_ticket_desde_carrito(),
    }


def _cerrar_modal_cobro():
    """Cierra el modal de cobro."""
    st.session_state['tpv_mostrar_cobro'] = False
    st.rerun()


def _registrar_ticket(metodo, entrega, cambio):
    """Registra la venta y prepara el ticket post-cobro."""
    db = DatabaseAccess()
    try:
        result = db.crear_ticket(_datos_ticket(metodo, entrega, cambio))
        if not result:
            st.error("❌ Error al registrar el ticket")
            return

        result_dict = _obj_to_dict(result)
        result_dict['lineas'] = [_obj_to_dict(l) for l in result.lineas]
        st.session_state['tpv_mostrar_cobro'] = False
        st.session_state['tpv_mostrar_ticket'] = True
        st.session_state['tpv_ticket_reciente'] = result_dict
        st.session_state['tpv_ticket_time'] = time.time()
        limpiar_carrito()
        st.rerun()
    finally:
        db.close()


def _finalizar_venta(metodo, entrega, cambio):
    """Ejecuta el cobro: sonido, registro y recarga."""
    components.html("""
    <script>document.getElementById('sonido-cobro').play();</script>
    """, height=0)
    with st.spinner("Registrando venta..."):
        _registrar_ticket(metodo, entrega, cambio)


def render_cobro_modal():
    """Modal centrado de cobro a pantalla completa."""
    total = calcular_total_carrito()
    metodo = st.session_state.get('tpv_metodo_pago', 'efectivo')

    components.html(AUDIO_COBRO, height=0)

    _, col_center, _ = st.columns([1, 3, 1])

    with col_center:
        st.markdown(
            CSS_MODAL_COBRO.format(
                icono="💵" if metodo == 'efectivo' else "💳",
                total=total,
                metodo_mayusculas=metodo.upper(),
            ),
            unsafe_allow_html=True,
        )

        entrega, cambio = (total, 0.0)
        if metodo == 'efectivo':
            entrega, cambio = _seccion_entrega_efectivo(total)

        confirmar = st.checkbox("✅ Confirmar cobro", key="confirmar_cobro_modal_v2")

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        col_cancelar, col_ok = st.columns(2)
        with col_cancelar:
            if st.button("❌ Cancelar", width="stretch", key="modal_btn_cancel_v2"):
                _cerrar_modal_cobro()
        with col_ok:
            if st.button(
                "✅ Finalizar Venta",
                width="stretch",
                type="primary" if confirmar else "secondary",
                disabled=not confirmar,
                key="modal_btn_ok_v2",
            ):
                _finalizar_venta(metodo, entrega, cambio)


def render_ticket_post_cobro():
    """Muestra el ticket simplificado después del cobro con auto-cierre e impresión."""
    ticket = st.session_state['tpv_ticket_reciente']

    # Sonido de éxito + auto-cierre 5s + impresión
    components.html(f"""
    <audio autoplay>
      <source src="https://assets.mixkit.co/active_storage/sfx/2000/2000-preview.mp3" type="audio/mpeg">
    </audio>
    <div id="ticket-para-imprimir" style="display:none;">
      <pre style="font-family:monospace; font-size:12px; color:#000;">
{'-'*42}
           MARKE TTALENTO
         Ticket N° {ticket['numero_ticket']}
    {ticket['fecha'][:16].replace('T', ' ')}
    Cajero: {ticket['cajero']}
{'-'*42}
      </pre>
    </div>
    <script>
      // Auto-cierre contador visual
      let seg = 5;
      const span = document.getElementById('contador-cierre');
      const timer = setInterval(() => {{
        seg--;
        if (span) span.innerText = seg;
        if (seg <= 0) clearInterval(timer);
      }}, 1000);
    </script>
    """, height=0)

    st.markdown("<div style='background: rgba(30,41,59,0.8); border-radius: 12px; padding: 25px; border: 1px solid rgba(59, 130, 246,0.3); max-width: 400px; margin: 0 auto;'>", unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: center; color: #3b82f6; margin-bottom: 5px;'>MARKE TTALENTO</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 0.9rem;'>Ticket N° {ticket['numero_ticket']}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 0.8rem;'>{ticket['fecha'][:16].replace('T', ' ')}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 0.8rem;'>Cajero: {ticket['cajero']}</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    for linea in ticket['lineas']:
        nombre = linea.get('producto', {}).get('nombre', f"Producto {linea['producto_id']}")
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin: 4px 0;">
            <span style="color: #f8fafc; font-size: 0.9rem;">{linea['cantidad']} x {nombre}</span>
            <span style="color: #10b981; font-size: 0.9rem;">€{linea['subtotal']:.2f}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: right; color: #3b82f6;'>TOTAL: €{ticket['total']:.2f}</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: right; color: #94a3b8; font-size: 0.85rem;'>Método: {ticket['metodo_pago'].upper()}</p>", unsafe_allow_html=True)

    if ticket.get('entrega_efectivo'):
        st.markdown(f"<p style='text-align: right; color: #94a3b8; font-size: 0.85rem;'>Entrega: €{ticket['entrega_efectivo']:.2f}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: right; color: #10b981; font-size: 0.85rem;'>Cambio: €{ticket['cambio']:.2f}</p>", unsafe_allow_html=True)

    st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 15px;'>¡Gracias por su visita!</p>", unsafe_allow_html=True)
    st.markdown(DIV_CLOSE, unsafe_allow_html=True)

    # Botones de acción
    ticket_txt = generar_ticket_txt(ticket)
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.download_button(
            "📥 Descargar",
            data=ticket_txt,
            file_name=f"ticket_{ticket['numero_ticket']}.txt",
            mime="text/plain",
            width="stretch"
        )
    with col_d2:
        if st.button("🖨️ Imprimir", width="stretch"):
            components.html("<script>window.print();</script>", height=0)
    with col_d3:
        if st.button("🔄 Nueva Venta", width="stretch", type="primary"):
            st.session_state['tpv_mostrar_ticket'] = False
            st.session_state['tpv_ticket_reciente'] = None
            st.rerun()

    # Contador de cierre automático
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 10px;'>⏱️ Cierre automático en <span id='contador-cierre' style='color: #3b82f6; font-weight: 700;'>5</span> segundos</p>", unsafe_allow_html=True)

    # Cierre automático real via Python (cada rerun verifica el tiempo)
    ticket_time = st.session_state.get('tpv_ticket_time')
    if ticket_time and (time.time() - ticket_time > 5):
        st.session_state['tpv_mostrar_ticket'] = False
        st.session_state['tpv_ticket_reciente'] = None
        st.rerun()


SEPARADOR_TICKET = "-" * 42


def _linea_producto_txt(linea: dict) -> str:
    """Una línea de producto formateada para el ticket en texto plano."""
    nombre = linea.get('producto', {}).get('nombre')
    if not nombre:
        nombre = "Prod %s" % linea['producto_id']
    return "%s x %-20s %7.2f €" % (linea['cantidad'], nombre, linea['subtotal'])


def _lineas_ticket_txt(ticket: dict) -> list:
    """Cabecera, líneas de producto y pie del ticket en texto plano."""
    cabecera = [
        SEPARADOR_TICKET,
        "           MARKE TTALENTO",
        f"         Ticket N° {ticket['numero_ticket']}",
        f"    {ticket['fecha'][:16].replace('T', ' ')}",
        f"    Cajero: {ticket['cajero']}",
        SEPARADOR_TICKET,
    ]

    detalle = [_linea_producto_txt(linea) for linea in ticket['lineas']]

    pie = [
        SEPARADOR_TICKET,
        f"TOTAL:{'':>28} {ticket['total']:>7.2f} €",
        f"Metodo: {ticket['metodo_pago'].upper()}",
    ]
    if ticket.get('entrega_efectivo'):
        pie += [
            f"Entrega:{'':>27} {ticket['entrega_efectivo']:>7.2f} €",
            f"Cambio:{'':>28} {ticket['cambio']:>7.2f} €",
        ]

    return cabecera + detalle + pie + [
        SEPARADOR_TICKET,
        "      ¡Gracias por su visita!",
        SEPARADOR_TICKET,
    ]


def generar_ticket_txt(ticket: dict) -> str:
    """Genera el contenido del ticket en formato texto."""
    return "\n".join(_lineas_ticket_txt(ticket))


COLORES_CAT = {
    'Bebidas': '#f59e0b', 'Cervezas': '#fbbf24', 'Whiskies': '#a78bfa',
    'Cafés': '#92400e', 'Refrescos': '#ef4444', 'Hamburguesas': '#f97316',
    'Pizzas': '#f59e0b', 'Bocadillos': '#10b981', 'Menus': '#3b82f6',
    'Todos': '#3b82f6',
}
COLOR_CAT_POR_DEFECTO = '#3b82f6'
CATEGORIA_TODOS = 'todos'
MAX_CATEGORIAS_BARRA = 6
COLS_GRID_PRODUCTOS = 4
STOCK_BAJO_UMBRAL = 5


def _cargar_categorias():
    """Carga las categorías del catálogo."""
    db = DatabaseAccess()
    try:
        return [_obj_to_dict(c) for c in db.get_categorias()]
    finally:
        db.close()


def _comprobar_datos_tpv(productos, inventarios):
    """Valida los datos cargados. Devuelve el inventario usable."""
    if not productos:
        st.warning("⚠️ No hay productos disponibles")
        return None

    if not inventarios:
        st.error("⚠️ Error al cargar inventario. Los productos pueden aparecer como no disponibles.")
        st.button("🔄 Reintentar", on_click=lambda: st.rerun(), key="retry_inventario")
        return []

    return inventarios


def _filtrar_por_busqueda(productos, busqueda):
    """Filtra los productos por nombre."""
    if not busqueda:
        return productos
    return [p for p in productos if busqueda.lower() in p.get('nombre', '').lower()]


def _filtrar_por_categoria(productos, cat_activa):
    """Filtra los productos por id de categoría."""
    if cat_activa == CATEGORIA_TODOS:
        return productos
    return [p for p in productos if p.get('categoria_id') == cat_activa]


def _css_boton_categoria(posicion, color_cat, es_activa):
    """Genera el CSS del botón de categoría activo."""
    if es_activa:
        bg = f"rgba({int(color_cat[1:3],16)},{int(color_cat[3:5],16)},{int(color_cat[5:7],16)},0.15)"
        border = f"1px solid {color_cat}"
    else:
        bg = "rgba(30,41,59,0.6)"
        border = "1px solid rgba(255,255,255,0.1)"

    return f"""
    <style>
    div[data-testid="stHorizontalBlock"] div:nth-child({posicion}) button[data-testid="baseButton-secondary"] {{
        background: {bg} !important;
        border: {border} !important;
        color: {color_cat if es_activa else '#94a3b8'} !important;
        border-radius: 10px !important;
        font-weight: {'700' if es_activa else '500'} !important;
    }}
    </style>
    """


def _activar_categoria(cat_id):
    """Selecciona la categoría activa del TPV."""
    st.session_state['tpv_categoria_activa'] = cat_id
    st.rerun()


def _render_fila_categorias(categorias, cat_activa):
    """Renderiza la barra de filtros por categoría."""
    cats_filtradas = [{"id": CATEGORIA_TODOS, "nombre": "Todos"}] + [
        {"id": c["id"], "nombre": c["nombre"]} for c in categorias
    ]
    visibles = cats_filtradas[:MAX_CATEGORIAS_BARRA]

    for posicion, (col, cat) in enumerate(zip(st.columns(min(len(cats_filtradas), MAX_CATEGORIAS_BARRA)), visibles)):
        es_activa = cat_activa == cat["id"]
        color_cat = COLORES_CAT.get(cat["nombre"], COLOR_CAT_POR_DEFECTO)

        with col:
            st.markdown(_css_boton_categoria(posicion + 1, color_cat, es_activa), unsafe_allow_html=True)
            if st.button(cat["nombre"], key=f"cat_{cat['id']}", width="stretch"):
                _activar_categoria(cat["id"])


def _calcular_mas_vendidos():
    """Devuelve un dict producto_id -> unidades vendidas. {} si falla la consulta."""
    try:
        db = DatabaseAccess()
        try:
            tickets = [_obj_to_dict(t) for t in db.get_tickets(limite=LIMITE_TICKETS_FAVORITOS)]
        finally:
            db.close()

        ventas = {}
        for t in tickets:
            for linea in t.get('lineas', []):
                pid = linea.get('producto_id')
                ventas[pid] = ventas.get(pid, 0) + linea.get('cantidad', 0)
        return ventas
    except Exception:
        return {}


def _es_favorito(prod, prod_ventas):
    """Indica si el producto tiene ventas registradas."""
    return prod_ventas.get(prod.get('id'), 0) > 0


def _estilos_tarjeta(sin_stock, es_favorito):
    """Devuelve (opacity, cursor, border_color, border_width) de la tarjeta."""
    if sin_stock:
        border_color = "#ef4444"
    elif es_favorito:
        border_color = "#f59e0b"
    else:
        border_color = "rgba(255,255,255,0.1)"

    return (
        "0.4" if sin_stock else "1",
        "not-allowed" if sin_stock else "pointer",
        border_color,
        "2px" if (sin_stock or es_favorito) else "1px",
    )


def _badge_stock_html(stock, sin_stock):
    """Devuelve el badge de stock de la tarjeta, o vacío si no hay stock."""
    if sin_stock:
        return ''

    badge_class = "tpv-badge-stock"
    if stock < STOCK_BAJO_UMBRAL:
        badge_class += " tpv-badge-stock-bajo"
    return f'<div class="{badge_class}">{stock}</div>'


def _placeholder_imagen():
    """Emoji mostrado cuando el producto no tiene imagen."""
    return '<div style="font-size: 2rem; margin: 0 auto;">📦</div>'


def _html_imagen_base64(imagen):
    """Codifica en base64 una imagen en disco. None si no se puede leer."""
    try:
        with open(imagen, "rb") as f:
            datos_b64 = base64.b64encode(f.read()).decode()
    except Exception:
        return None
    fmt = 'png' if imagen.lower().endswith('.png') else 'jpeg'
    return f'data:image/{fmt};base64,{datos_b64}'


def _html_imagen_tarjeta(imagen):
    """Devuelve el HTML de la imagen de la tarjeta, o el placeholder."""
    if not imagen:
        return _placeholder_imagen()

    if imagen.startswith("data:image"):
        return f'<img src="{imagen}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; margin: 0 auto;">'

    if os.path.exists(imagen):
        codificada = _html_imagen_base64(imagen)
        if codificada:
            return f'<img src="{codificada}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; margin: 0 auto;">'

    return _placeholder_imagen()


def _abrir_modal_cantidad(prod_id):
    """Abre el modal para elegir la cantidad a añadir."""
    st.session_state['tpv_modal_cantidad_prod_id'] = prod_id
    st.rerun()


def _agregar_al_carrito(prod):
    """Añade una unidad del producto al carrito."""
    agregar_linea_carrito(prod)
    st.rerun()


def _render_tarjeta_producto(prod, stock, es_favorito, col):
    """Renderiza la tarjeta de un producto en el grid del TPV."""
    sin_stock = stock <= 0
    imagen = _buscar_imagen_producto(prod)
    opacity, cursor, border_color, border_width = _estilos_tarjeta(sin_stock, es_favorito)
    nombre_display = prod.get('nombre') + (' ⭐' if es_favorito else '')

    with col:
        card_html = f"""
        <div style="position: relative; opacity: {opacity}; border: {border_width} solid {border_color}; border-radius: 10px; padding: 10px;
                    background: rgba(30,41,59,0.8); cursor: {cursor}; text-align: center;
                    margin-bottom: 10px; height: 150px; display: flex; flex-direction: column;
                    justify-content: space-between;">
            {_badge_stock_html(stock, sin_stock)}
        """
        card_html += _html_imagen_tarjeta(imagen)
        card_html += f"""
            <div style="font-size: 0.85rem; font-weight: 600; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{nombre_display}</div>
            <div style="font-size: 0.9rem; color: #3b82f6; font-weight: 700;">€{prod.get('precio_venta', 0):.2f}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        if sin_stock:
            return

        col_agregar, col_cantidad = st.columns(2)
        with col_agregar:
            if st.button("➕", key=f"add_prod_{prod.get('id')}", width="stretch"):
                _agregar_al_carrito(prod)
        with col_cantidad:
            if st.button("#️⃣", key=f"cant_prod_{prod.get('id')}", width="stretch", help="Cantidad"):
                _abrir_modal_cantidad(prod.get('id'))


def render_panel_productos():
    """Panel derecho: Categorías y productos con búsqueda, colores, badges y favoritos."""
    productos, inventarios, _ = _get_ventas_data()
    categorias = _cargar_categorias()

    inventarios = _comprobar_datos_tpv(productos, inventarios)
    if inventarios is None:
        return

    cat_activa = st.session_state.get('tpv_categoria_activa', CATEGORIA_TODOS)

    busqueda = st.text_input("🔍 Buscar producto...", key="tpv_busqueda_prod", label_visibility="collapsed")
    productos = _filtrar_por_busqueda(productos, busqueda)

    _render_fila_categorias(categorias, cat_activa)

    st.markdown("<hr style='margin: 10px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    productos = _filtrar_por_categoria(productos, cat_activa)

    prod_ventas = _calcular_mas_vendidos()
    productos.sort(key=lambda p: (-prod_ventas.get(p.get('id'), 0), p.get('nombre', '')))

    if st.session_state.get('tpv_modal_cantidad_prod_id'):
        _render_modal_cantidad(productos, inventarios)

    cols_grid = st.columns(COLS_GRID_PRODUCTOS)
    for idx, prod in enumerate(productos):
        stock = _get_stock(prod.get('id'), inventarios)
        _render_tarjeta_producto(prod, stock, _es_favorito(prod, prod_ventas), cols_grid[idx % COLS_GRID_PRODUCTOS])


def _render_modal_cantidad(productos, inventarios):
    """Modal para elegir cantidad al agregar producto."""
    prod_id = st.session_state.get('tpv_modal_cantidad_prod_id')
    prod = next((p for p in productos if p.get('id') == prod_id), None)
    if not prod:
        st.session_state['tpv_modal_cantidad_prod_id'] = None
        return
    stock = _get_stock(prod.get('id'), inventarios)

    st.markdown("""
    <style>
    @keyframes modalFadeIn { from { opacity:0; transform:scale(0.9); } to { opacity:1; transform:scale(1); } }
    .mini-modal { animation: modalFadeIn 0.25s ease forwards; background: rgba(30,41,59,0.95); border: 1px solid rgba(59, 130, 246,0.3); border-radius: 14px; padding: 20px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='mini-modal'>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='color: #3b82f6; text-align: center;'>📦 {prod.get('nombre')}</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #94a3b8;'>Stock disponible: {stock}</p>", unsafe_allow_html=True)

    cantidad = st.number_input("Cantidad", min_value=1, max_value=stock, value=1, key="modal_cantidad_val")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("❌ Cancelar", width="stretch", key="modal_cant_cancel"):
            st.session_state['tpv_modal_cantidad_prod_id'] = None
            st.rerun()
    with c2:
        if st.button("✅ Agregar", width="stretch", type="primary", key="modal_cant_ok"):
            for _ in range(int(cantidad)):
                agregar_linea_carrito(prod)
            st.session_state['tpv_modal_cantidad_prod_id'] = None
            st.rerun()
    st.markdown(DIV_CLOSE, unsafe_allow_html=True)


# ============================================================================
# TAB DASHBOARD
# ============================================================================

SIN_DATOS = "sin datos"
MSG_SIN_DATOS = "Sin datos"
SIN_CATEGORIA = "Sin categoría"
MODO_LINEAS = 'lines+markers'
DIAS_TENDENCIA = 15
TOP_PRODUCTOS = 10
LIMITE_TICKETS_DASHBOARD = 500
LIMITE_TICKETS_FAVORITOS = 200
COLOR_FONDO_TRANSPARENTE = 'rgba(0,0,0,0)'
COLOR_TEXTO_GRAFICA = '#94a3b8'
ALTURA_GRAFICA = 280
MARGEN_GRAFICA = {"l": 0, "r": 0, "t": 30, "b": 0}

LAYOUT_DASHBOARD = {
    "plot_bgcolor": COLOR_FONDO_TRANSPARENTE,
    "paper_bgcolor": COLOR_FONDO_TRANSPARENTE,
    "font_color": COLOR_TEXTO_GRAFICA,
    "height": ALTURA_GRAFICA,
    "margin": MARGEN_GRAFICA,
}

# (etiqueta, limite superior inclusivo; None = sin limite)
RANGOS_IMPORTE = (
    ("€0-10", 10),
    ("€10-25", 25),
    ("€25-50", 50),
    ("€50-100", 100),
    ("€100+", None),
)
COLORES_RANGOS = ["#b21798", "#116025", "#ffa200", "#dd1f1f", "#5c1bf3"]


def _aplicar_layout_dashboard(fig):
    """Aplica el layout común de las gráficas del dashboard."""
    fig.update_layout(**LAYOUT_DASHBOARD)
    return fig


def _cargar_datos_dashboard():
    """Carga resumen, tickets, productos y categorías del dashboard."""
    db = DatabaseAccess()
    try:
        return (
            db.obtener_estadisticas_resumen(),
            [_obj_to_dict(t) for t in db.get_tickets(limite=LIMITE_TICKETS_DASHBOARD)],
            [_obj_to_dict(p) for p in db.get_productos()],
            [_obj_to_dict(c) for c in db.get_categorias()],
        )
    finally:
        db.close()


def _render_metricas(resumen):
    """Muestra las 4 métricas principales."""
    st.metric("💰 Total Ingresos", f"€{resumen.get('total_ingresos', 0):.2f}")
    st.metric("🎫 Tickets", resumen.get('total_tickets', 0))
    st.metric("📦 Unidades", resumen.get('total_unidades', 0))
    st.metric("📈 Ticket Promedio", f"€{resumen.get('ticket_promedio', 0):.2f}")


def _ventas_por_dia(tickets):
    """Devuelve un dict fecha (YYYY-MM-DD) -> ingresos acumulados."""
    ventas = {}
    for t in tickets:
        fecha = str(t.get('fecha', ''))[:10]
        ventas[fecha] = ventas.get(fecha, 0) + t.get('total', 0)
    return ventas


def _grafica_tendencia_ventas(tickets):
    """Gráfica 1: ingresos por día."""
    ventas_dia = _ventas_por_dia(tickets)
    if not ventas_dia:
        return

    st.markdown("#### 📈 Tendencia de Ventas")
    fechas = sorted(ventas_dia.keys())[-DIAS_TENDENCIA:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fechas, y=[ventas_dia[f] for f in fechas], mode=MODO_LINEAS,
        line={"color": '#3b82f6', "width": 2}, fill='tozeroy', fillcolor='rgba(59, 130, 246,0.1)',
    ))
    st.plotly_chart(_aplicar_layout_dashboard(fig), width="stretch")


def _nombre_por_producto(productos):
    """Devuelve un dict producto_id -> nombre de producto."""
    return {p.get('id'): p.get('nombre') for p in productos}


def _ventas_por_producto(tickets, productos):
    """Devuelve un dict nombre_producto -> unidades vendidas."""
    nombres = _nombre_por_producto(productos)
    ventas = {}
    for t in tickets:
        for linea in t.get('lineas', []):
            nombre = nombres.get(linea.get('producto_id')) or f"Prod {linea.get('producto_id')}"
            ventas[nombre] = ventas.get(nombre, 0) + linea.get('cantidad', 0)
    return ventas


def _grafica_top_productos(tickets, productos):
    """Gráfica 2: top de productos por unidades."""
    st.markdown("#### 🏆 Top Productos")
    ventas = _ventas_por_producto(tickets, productos)

    if not ventas:
        ventas = {p.get('nombre', f"Prod {p.get('id')}"): 0 for p in productos[:5]}

    top = sorted(ventas.items(), key=lambda x: x[1], reverse=True)[:TOP_PRODUCTOS]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[n for n, _ in top], y=[c for _, c in top], marker_color='#10b981'))
    st.plotly_chart(_aplicar_layout_dashboard(fig), width="stretch")


def _ventas_por_hora(tickets):
    """Devuelve un dict hora (0-23) -> ingresos acumulados."""
    horas = dict.fromkeys(range(24), 0)
    for t in tickets:
        fecha = str(t.get('fecha', ''))
        if len(fecha) <= 13:
            continue
        try:
            hora = int(fecha[11:13])
        except ValueError:
            continue
        horas[hora] += t.get('total', 0)
    return horas


def _grafica_ventas_por_hora(tickets):
    """Gráfica 3: ingresos por hora del día."""
    st.markdown("#### ⏰ Ventas por Hora")
    horas = _ventas_por_hora(tickets)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(horas.keys()), y=list(horas.values()), marker_color='#f59e0b'))
    st.plotly_chart(_aplicar_layout_dashboard(fig), width="stretch")


def _grafica_metodos_pago(tickets):
    """Gráfica 4: reparto por método de pago."""
    st.markdown("#### 💳 Métodos de Pago")
    metodos = {}
    for t in tickets:
        mp = t.get('metodo_pago', 'desconocido')
        metodos[mp] = metodos.get(mp, 0) + 1

    if not metodos:
        metodos = {SIN_DATOS: 1}

    fig = go.Figure()
    fig.add_trace(go.Pie(labels=list(metodos.keys()), values=list(metodos.values()), hole=0.4))
    st.plotly_chart(_aplicar_layout_dashboard(fig), width="stretch")


def _categoria_por_producto(productos):
    """Devuelve un dict producto_id -> id de categoría."""
    return {p.get('id'): p.get('categoria_id') for p in productos}


def _ingresos_por_categoria(tickets, productos, categorias):
    """Devuelve un dict nombre_categoria -> ingresos acumulados."""
    cat_map = {c.get('id'): c.get('nombre', SIN_CATEGORIA) for c in categorias}
    cat_por_producto = _categoria_por_producto(productos)

    ingresos = {}
    for t in tickets:
        for linea in t.get('lineas', []):
            cat_id = cat_por_producto.get(linea.get('producto_id'))
            cat_nombre = cat_map.get(cat_id, SIN_CATEGORIA)
            ingresos[cat_nombre] = ingresos.get(cat_nombre, 0) + linea.get('subtotal', 0)
    return ingresos


def _grafica_ingresos_por_categoria(tickets, productos, categorias):
    """Gráfica 5: ingresos por categoría."""
    st.markdown("#### 🏷️ Ingresos por Categoría")
    ingresos = _ingresos_por_categoria(tickets, productos, categorias)

    if not ingresos:
        ingresos = {SIN_DATOS: 0}

    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(ingresos.keys()), y=list(ingresos.values()), marker_color='#8b5cf6'))
    st.plotly_chart(_aplicar_layout_dashboard(fig), width="stretch")


def _grafica_ticket_promedio(tickets):
    """Gráfica 6: evolución del ticket promedio."""
    st.markdown("#### 📊 Evolución Ticket Promedio")
    dia_tickets = {}
    for t in tickets:
        fecha = str(t.get('fecha', ''))[:10]
        dia = dia_tickets.setdefault(fecha, {'total': 0, 'count': 0})
        dia['total'] += t.get('total', 0)
        dia['count'] += 1

    fechas = sorted(dia_tickets.keys())[-DIAS_TENDENCIA:] if dia_tickets else []
    if not fechas:
        fechas = [SIN_DATOS]
        promedios = [0]
    else:
        promedios = [
            round(dia_tickets[f]['total'] / dia_tickets[f]['count'], 2) if dia_tickets[f]['count'] > 0 else 0
            for f in fechas
        ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fechas, y=promedios, mode=MODO_LINEAS,
        line={"color": '#ef4444', "width": 2}, fill='tozeroy', fillcolor='rgba(239,68,68,0.1)',
    ))
    st.plotly_chart(_aplicar_layout_dashboard(fig), width="stretch")


def _rango_importe(total):
    """Devuelve la etiqueta del rango de importe al que pertenece un total."""
    for etiqueta, limite in RANGOS_IMPORTE:
        if limite is None or total <= limite:
            return etiqueta
    return RANGOS_IMPORTE[-1][0]


def _contar_por_rango_importe(tickets):
    """Devuelve un dict etiqueta_de_rango -> número de tickets."""
    rangos = dict.fromkeys((etiqueta for etiqueta, _ in RANGOS_IMPORTE), 0)
    for t in tickets:
        rangos[_rango_importe(t.get('total', 0))] += 1
    return rangos


def _grafica_distribucion_importe(tickets):
    """Gráfica 7: distribución de tickets por rango de importe."""
    st.markdown("#### 💰 Distribución por Importe")
    rangos = _contar_por_rango_importe(tickets)

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=list(rangos.keys()), values=list(rangos.values()),
        hole=0.4, marker_colors=COLORES_RANGOS,
    ))
    st.plotly_chart(_aplicar_layout_dashboard(fig), width="stretch")


def render_dashboard():
    """Dashboard completo con métricas y gráficas."""
    resumen, tickets_dict, productos, categorias = _cargar_datos_dashboard()

    if not tickets_dict or resumen.get('total_tickets', 0) == 0:
        st.info("📊 No hay tickets registrados aún. ¡Usa el TPV para registrar ventas!")
        return

    st.info("📊 Dashboard de ventas requiere iniciar la API con: uvicorn src.api:app --port 8002")
    st.markdown("### Datos Disponibles")
    _render_metricas(resumen)
    st.markdown("---")

    try:
        _grafica_tendencia_ventas(tickets_dict)
        _grafica_top_productos(tickets_dict, productos)
        _grafica_ventas_por_hora(tickets_dict)
        _grafica_metodos_pago(tickets_dict)
        _grafica_ingresos_por_categoria(tickets_dict, productos, categorias)
        _grafica_ticket_promedio(tickets_dict)
        _grafica_distribucion_importe(tickets_dict)
    except Exception as e:
        st.warning(f"Error cargando gráficas: {str(e)}")


def _plotly_config(fig, height=ALTURA_GRAFICA):
    fig.update_layout(
        plot_bgcolor=COLOR_FONDO_TRANSPARENTE,
        paper_bgcolor=COLOR_FONDO_TRANSPARENTE,
        font_color=COLOR_TEXTO_GRAFICA,
        margin=MARGEN_GRAFICA,
        height=height,
        xaxis_gridcolor='rgba(255,255,255,0.05)',
        yaxis_gridcolor='rgba(255,255,255,0.05)',
    )
    return fig


def grafica_tendencia(datos):
    st.markdown("#### 📈 Tendencia de Ventas")
    if not datos:
        st.info(MSG_SIN_DATOS)
        return
    df = pd.DataFrame(datos)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['ingresos'],
        mode=MODO_LINEAS,
        name='Ingresos',
        line={"color": '#3b82f6', "width": 3},
        fill='tozeroy', fillcolor='rgba(59, 130, 246,0.1)'
    ))
    fig.update_layout(title_text="Ingresos por día", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_top_productos_unidades(datos):
    st.markdown("#### 🥇 Top Productos (Unidades)")
    if not datos:
        st.info(MSG_SIN_DATOS)
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Bar(
        x=df['producto'], y=df['unidades'],
        marker_color='#10b981', text=df['unidades'], textposition='auto'
    )])
    fig.update_layout(title_text="Más vendidos por cantidad", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_ventas_por_hora(datos):
    st.markdown("#### ⏰ Ventas por Hora")
    if not datos:
        st.info(MSG_SIN_DATOS)
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Bar(
        x=df['hora'], y=df['ventas'],
        marker_color='#f59e0b'
    )])
    fig.update_layout(title_text="Distribución horaria", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_distribucion_ingresos():
    st.markdown("#### 📊 Distribución Ingresos")
    db = DatabaseAccess()
    try:
        tickets = db.get_tickets(limite=LIMITE_TICKETS_DASHBOARD)
        tickets = [_obj_to_dict(t) for t in tickets]
    finally:
        db.close()
    
    if not tickets:
        st.info(MSG_SIN_DATOS)
        return

    rangos = _contar_por_rango_importe(tickets)
    fig = go.Figure(data=[go.Pie(
        labels=list(rangos.keys()), values=list(rangos.values()),
        hole=0.4,
        marker_colors=COLORES_RANGOS
    )])
    fig.update_layout(title_text="Por rango de ticket", title_font_size=12, showlegend=True,
                      legend={"orientation": "h", "yanchor": "bottom", "y": -0.2})
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_ventas_por_categoria(datos):
    st.markdown("#### 🏷️ Ventas por Categoría")
    if not datos:
        st.info(MSG_SIN_DATOS)
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Pie(
        labels=df['categoria'], values=df['ingresos'],
        hole=0.5,
        marker_colors=px.colors.sequential.Plasma
    )])
    fig.update_layout(title_text="Ingresos por categoría", title_font_size=12,
                      legend={"orientation": "h", "yanchor": "bottom", "y": -0.2})
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_ticket_promedio(datos):
    st.markdown("#### 📉 Ticket Promedio")
    if not datos:
        st.info(MSG_SIN_DATOS)
        return
    df = pd.DataFrame(datos)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['ticket_promedio'],
        mode=MODO_LINEAS,
        line={"color": '#8b5cf6', "width": 3},
        fill='tozeroy', fillcolor='rgba(139,92,246,0.1)'
    ))
    fig.update_layout(title_text="Evolución del ticket promedio", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_top_productos_ingresos(datos):
    st.markdown("#### 💶 Top Productos (Ingresos)")
    if not datos:
        st.info(MSG_SIN_DATOS)
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Bar(
        x=df['ingresos'], y=df['producto'], orientation='h',
        marker_color='#3b82f6', text=[f"€{x:.2f}" for x in df['ingresos']], textposition='auto'
    )])
    fig.update_layout(title_text="Más rentables", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_mapa_calor(datos):
    st.markdown("#### 🔥 Mapa de Calor (Día/Hora)")
    if not datos:
        st.info(MSG_SIN_DATOS)
        return
    # Construir matriz
    horas = list(range(24))
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    matriz = [[0 for _ in horas] for _ in dias]
    for fila in datos:
        d = fila['dia_num']
        for h_data in fila['horas']:
            matriz[d][h_data['hora']] = h_data['ventas']

    fig = go.Figure(data=go.Heatmap(
        z=matriz,
        x=[f"{h:02d}h" for h in horas],
        y=dias,
        colorscale='YlOrRd'
    ))
    fig.update_layout(title_text="Tickets por día y hora", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_metodos_pago(resumen):
    st.markdown("#### 💳 Métodos de Pago")
    metodos = resumen.get('metodos_pago', {})
    if not metodos:
        st.info(MSG_SIN_DATOS)
        return
    fig = go.Figure(data=[go.Bar(
        x=list(metodos.keys()), y=list(metodos.values()),
        marker_color=['#10b981', '#3b82f6', '#f59e0b']
    )])
    fig.update_layout(title_text="Preferencia de pago", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_comparativa_mes(datos):
    st.markdown("#### 📅 Mes Actual vs Anterior")
    if not datos:
        st.info(MSG_SIN_DATOS)
        return
    actual = datos.get('mes_actual', {})
    anterior = datos.get('mes_anterior', {})
    categorias = ['Ingresos', 'Tickets', 'Unidades']
    valores_actual = [actual.get('ingresos', 0), actual.get('tickets', 0), actual.get('unidades', 0)]
    valores_anterior = [anterior.get('ingresos', 0), anterior.get('tickets', 0), anterior.get('unidades', 0)]

    fig = go.Figure()
    fig.add_trace(go.Bar(name=datos.get('nombre_mes_actual', 'Actual'), x=categorias, y=valores_actual, marker_color='#3b82f6'))
    fig.add_trace(go.Bar(name=datos.get('nombre_mes_anterior', 'Anterior'), x=categorias, y=valores_anterior, marker_color='#64748b'))
    fig.update_layout(barmode='group', title_text="Comparativa mensual", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_objetivos(resumen, meta):
    """Gráfica de meta diaria vs ventas reales."""
    if not resumen:
        st.info(MSG_SIN_DATOS)
        return
    ingresos_hoy = resumen.get('total_ingresos', 0)
    pct = min((ingresos_hoy / meta * 100), 100) if meta > 0 else 0
    restante = max(meta - ingresos_hoy, 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Meta', 'Real'], y=[meta, ingresos_hoy],
        marker_color=['#64748b', '#3b82f6'],
        text=[f"€{meta:.0f}", f"€{ingresos_hoy:.2f}"],
        textposition='auto',
        textfont={"size": 14, "color": 'white'}
    ))
    fig.add_hline(y=meta, line_dash="dash", line_color="#f59e0b", annotation_text="🎯 Meta")
    fig.update_layout(title_text=f"Progreso: {pct:.0f}%", title_font_size=12, showlegend=False)
    st.plotly_chart(_plotly_config(fig, height=220), width="stretch")
    if restante > 0:
        st.markdown(f"<p style='text-align:center; color:#94a3b8; font-size:0.8rem;'>Faltan €{restante:.2f} para la meta</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='text-align:center; color:#10b981; font-size:0.85rem; font-weight:600;'>🎉 ¡Meta alcanzada!</p>", unsafe_allow_html=True)


# ============================================================================
# TAB HISTORIAL
# ============================================================================

FILTRO_TODOS = "Todos"
LIMITE_TICKETS_HISTORIAL = 200
TICKETS_POR_PAGINA_HISTORIAL = 10
COLOR_ESTADO_COMPLETADO = "#10b981"
COLOR_ESTADO_ANULADO = "#ef4444"
ESTADO_COMPLETADO = 'completado'
ESTADO_ANULADO = 'anulado'

# (etiqueta, días hacia atrás, días hacia atrás del extremo "hasta")
FILTROS_FECHA_RAPIDOS = (
    ("Hoy", 0, 0),
    ("Ayer", 1, 1),
    ("Últimos 7 días", 7, 0),
    ("Este mes", 30, 0),
    ("Todo", 365, 0),
)
DIAS_TODO_HISTORIAL = 365


def _aplicar_filtro_rapido(dias_atras, dias_fin):
    """Fija el rango de fechas del historial. 365 días significa 'todo' (sin rango)."""
    if dias_atras == DIAS_TODO_HISTORIAL:
        st.session_state['hist_fecha_desde'] = None
        st.session_state['hist_fecha_hasta'] = None
    else:
        hoy = datetime.now().date()
        st.session_state['hist_fecha_desde'] = (hoy - timedelta(days=dias_atras)).isoformat()
        st.session_state['hist_fecha_hasta'] = (hoy - timedelta(days=dias_fin)).isoformat()
    st.rerun()


def _render_filtro_rapido():
    """Renderiza los botones de filtro rápido por fecha."""
    st.markdown("<p style='color: #64748b; font-size: 0.85rem; margin-bottom: 5px;'>📅 Filtro rápido:</p>", unsafe_allow_html=True)

    for col, (label, dias_atras, dias_fin) in zip(st.columns(len(FILTROS_FECHA_RAPIDOS)), FILTROS_FECHA_RAPIDOS):
        with col:
            if st.button(label, width="stretch", key=f"hist_fecha_{label.replace(' ', '_')}"):
                _aplicar_filtro_rapido(dias_atras, dias_fin)


def _fecha_desde_session(key):
    """Convierte un valor ISO del session_state en date, o None."""
    valor = st.session_state.get(key)
    return datetime.fromisoformat(valor).date() if valor else None


def _render_filtros_avanzados():
    """Renderiza los filtros de cajero y rango de fechas. Devuelve (cajero, desde, hasta)."""
    col_cajero, col_desde, col_hasta, col_refrescar = st.columns([2, 2, 2, 1])

    with col_cajero:
        filtro_cajero = st.selectbox("Cajero", [FILTRO_TODOS] + CAJEROS, key="hist_cajero")
    with col_desde:
        fecha_desde = st.date_input("Desde", value=_fecha_desde_session('hist_fecha_desde'), key="hist_desde")
    with col_hasta:
        fecha_hasta = st.date_input("Hasta", value=_fecha_desde_session('hist_fecha_hasta'), key="hist_hasta")
    with col_refrescar:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", width="stretch"):
            st.rerun()

    return filtro_cajero, fecha_desde, fecha_hasta


def _filtrar_tickets(tickets, filtro_cajero, fecha_desde, fecha_hasta):
    """Aplica los filtros de cajero y rango de fechas sobre los tickets."""
    if filtro_cajero != FILTRO_TODOS:
        tickets = [t for t in tickets if t.get('cajero') == filtro_cajero]
    if fecha_desde:
        tickets = [t for t in tickets if str(t.get('fecha', '')) >= str(fecha_desde)]
    if fecha_hasta:
        tickets = [t for t in tickets if str(t.get('fecha', ''))[:10] <= str(fecha_hasta)]
    return tickets


def _cargar_tickets_historial(filtro_cajero, fecha_desde, fecha_hasta):
    """Carga y filtra los tickets del historial."""
    db = DatabaseAccess()
    try:
        tickets = [_obj_to_dict(t) for t in db.get_tickets(limite=LIMITE_TICKETS_HISTORIAL)]
    finally:
        db.close()

    return _filtrar_tickets(tickets, filtro_cajero, fecha_desde, fecha_hasta)


def _nombre_linea(linea):
    """Nombre del producto de una línea de ticket, o su id si no viene resuelto."""
    nombre = linea.get('producto', {}).get('nombre')
    return nombre or f"Producto {linea.get('producto_id', 'N/A')}"


def _filas_exportacion(tickets):
    """Aplana los tickets a filas para la exportación a Excel."""
    filas = []
    for t in tickets:
        for linea in t.get('lineas', []):
            filas.append({
                "ticket": t['numero_ticket'],
                "fecha": t['fecha'][:16].replace('T', ' '),
                "cajero": t['cajero'],
                "estado": t['estado'],
                "metodo_pago": t['metodo_pago'],
                "producto": _nombre_linea(linea),
                "cantidad": linea['cantidad'],
                "precio_unitario": linea['precio_unitario'],
                "subtotal": linea['subtotal'],
                "total_ticket": t['total'],
            })
    return filas


def _render_exportar_historial(tickets):
    """Muestra el botón de exportación a Excel del historial."""
    filas = _filas_exportacion(tickets)
    if not filas:
        return

    st.download_button(
        "📥 Exportar Excel",
        data=to_excel(pd.DataFrame(filas)),
        file_name=f"historial_tickets_{datetime.now().strftime('%Y%m%d')}.xlsx",
        width="stretch",
    )


def _render_lineas_ticket(ticket):
    """Muestra la tabla de líneas de un ticket."""
    filas = [
        {
            "Producto": _nombre_linea(linea),
            "Cantidad": linea.get('cantidad', 0),
            "P. Unitario": f"€{linea.get('precio_unitario', 0):.2f}",
            "Subtotal": f"€{linea.get('subtotal', 0):.2f}",
        }
        for linea in ticket.get('lineas', [])
    ]
    if filas:
        st.table(pd.DataFrame(filas))


def _anular_ticket(ticket_id):
    """Marca un ticket como anulado. Muestra el resultado."""
    from src.dominio.entidades.entidades import Ticket

    db = DatabaseAccess()
    try:
        ticket_db = db.session.query(Ticket).get(ticket_id)
        if not ticket_db:
            st.error("Ticket no encontrado")
            return
        ticket_db.estado = ESTADO_ANULADO
        db.session.commit()
        st.success("Ticket anulado correctamente")
        st.rerun()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        db.session.rollback()
    finally:
        db.close()


def _render_boton_anular(ticket):
    """Muestra el botón de anulación para tickets completados."""
    if ticket['estado'] != ESTADO_COMPLETADO:
        return

    col_anular, _ = st.columns([1, 3])
    with col_anular:
        if st.button("❌ Anular Ticket", key=f"anular_{ticket['id']}", width="stretch"):
            with st.spinner("Anulando..."):
                _anular_ticket(ticket['id'])


def _render_ticket_historial(ticket):
    """Renderiza un ticket completo dentro de su expander."""
    titulo = (
        f"🎫 Ticket N° {ticket.get('numero_ticket', 'N/A')} | "
        f"€{ticket.get('total', 0):.2f} | {ticket.get('cajero', 'N/A')} | "
        f"{_format_fecha(ticket.get('fecha', ''))}"
    )
    with st.expander(titulo):
        color = COLOR_ESTADO_COMPLETADO if ticket['estado'] == ESTADO_COMPLETADO else COLOR_ESTADO_ANULADO
        st.markdown(f"<p style='color: {color}; font-weight: 600;'>Estado: {ticket['estado'].upper()}</p>", unsafe_allow_html=True)
        st.markdown(f"**Método de pago:** {ticket['metodo_pago'].upper()}")

        if ticket.get('entrega_efectivo'):
            st.markdown(f"**Entrega:** €{ticket['entrega_efectivo']:.2f} | **Cambio:** €{ticket['cambio']:.2f}")

        _render_lineas_ticket(ticket)
        _render_boton_anular(ticket)


def _paginar_tickets(tickets):
    """Devuelve (tickets_de_la_pagina, pagina, total_paginas)."""
    pagina = min(
        st.session_state.get('tpv_pagina_historial', 1),
        max(1, (len(tickets) + TICKETS_POR_PAGINA_HISTORIAL - 1) // TICKETS_POR_PAGINA_HISTORIAL),
    )
    inicio = (pagina - 1) * TICKETS_POR_PAGINA_HISTORIAL
    fin = min(inicio + TICKETS_POR_PAGINA_HISTORIAL, len(tickets))
    total_paginas = max(1, (len(tickets) + TICKETS_POR_PAGINA_HISTORIAL - 1) // TICKETS_POR_PAGINA_HISTORIAL)
    return tickets[inicio:fin], pagina, total_paginas


def _ir_a_pagina_historial(pagina):
    """Cambia de página en el historial."""
    st.session_state['tpv_pagina_historial'] = pagina
    st.rerun()


def _render_paginacion_historial(pagina, total_paginas):
    """Muestra los controles de paginación del historial."""
    if total_paginas <= 1:
        return

    col_ant, col_info, col_sig = st.columns([1, 2, 1])
    with col_ant:
        if st.button("⬅️ Anterior", disabled=pagina <= 1, key="hist_ant"):
            _ir_a_pagina_historial(pagina - 1)
    with col_info:
        st.markdown(f"<p style='text-align: center;'>Página {pagina} de {total_paginas}</p>", unsafe_allow_html=True)
    with col_sig:
        if st.button("Siguiente ➡️", disabled=pagina >= total_paginas, key="hist_sig"):
            _ir_a_pagina_historial(pagina + 1)


def render_historial():
    """Historial de tickets con filtros rápidos y anulación."""
    st.markdown("### 📋 Historial de Tickets")

    _render_filtro_rapido()
    filtro_cajero, fecha_desde, fecha_hasta = _render_filtros_avanzados()

    tickets = _cargar_tickets_historial(filtro_cajero, fecha_desde, fecha_hasta)

    if not tickets:
        st.info("📭 No hay tickets en el período seleccionado")
        return

    _render_exportar_historial(tickets)

    tickets_pagina, pagina, total_paginas = _paginar_tickets(tickets)

    for ticket in tickets_pagina:
        _render_ticket_historial(ticket)

    _render_paginacion_historial(pagina, total_paginas)
