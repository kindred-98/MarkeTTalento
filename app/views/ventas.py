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
        tickets = db.get_tickets(limite=500)
        
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


def _buscar_imagen_producto(producto: dict) -> Optional[str]:
    """Intenta encontrar una imagen para el producto (redimensionada a thumbnail)."""
    imagen_url = producto.get('imagen_url')
    candidatos = []
    if imagen_url and os.path.exists(imagen_url):
        candidatos.append(imagen_url)

    # Buscar en docs/img_productos/
    nombre = producto.get('nombre', '').lower().replace(' ', '_')
    docs_dir = 'docs/img_productos'
    if os.path.exists(docs_dir):
        for ext in ['.jpg', '.jpeg', '.png']:
            for fname in os.listdir(docs_dir):
                if fname.lower().endswith(ext):
                    if nombre in fname.lower() or fname.lower().replace(ext, '') in nombre:
                        candidatos.append(os.path.join(docs_dir, fname))

    for path in candidatos:
        try:
            if PIL_AVAILABLE:
                with Image.open(path) as img:
                    img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                    buffer = io.BytesIO()
                    fmt = 'PNG' if path.lower().endswith('.png') else 'JPEG'
                    img.save(buffer, format=fmt)
                    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buffer.getvalue()).decode()
            else:
                # Fallback: devolver path directo
                return path
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


def render_panel_ticket():
    """Panel izquierdo: Ticket actual con scroll, barcode, descuento y alertas."""
    st.markdown("<div style='background: rgba(30,41,59,0.6); border-radius: 10px; padding: 15px; border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    # Header
    cajero = st.selectbox("🧑‍💼 Cajero", CAJEROS, key="tpv_cajero_select")
    st.session_state['tpv_cajero'] = cajero
    st.markdown(f"<p style='color: #64748b; font-size: 0.8rem;'>📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>", unsafe_allow_html=True)

    # Input código de barras
    barcode = st.text_input("🔍 Código de barras / Nombre", placeholder="Escanea o escribe...", key="tpv_barcode", label_visibility="collapsed")
    if barcode:
        _procesar_barcode(barcode)

    st.markdown("---")

    carrito = get_tpv_carrito()

    # Scroll de líneas
    st.markdown("<div class='tpv-panel-scroll'>", unsafe_allow_html=True)
    if not carrito:
        st.markdown("<p style='color: #64748b; text-align: center; padding: 30px 0;'>🛒 Ticket vacío<br>Haz clic en un producto para agregarlo</p>", unsafe_allow_html=True)
    else:
        for idx, linea in enumerate(carrito):
            seleccionada = st.session_state.get('tpv_linea_seleccionada') == idx
            bg_color = "rgba(59, 130, 246,0.1)" if seleccionada else "transparent"
            border_color = "#3b82f6" if seleccionada else "rgba(255,255,255,0.05)"

            cols = st.columns([1, 4, 2, 2, 1, 1, 1])
            with cols[0]:
                if st.button(f"{'●' if seleccionada else '○'}", key=f"sel_linea_{idx}", help="Seleccionar línea"):
                    st.session_state['tpv_linea_seleccionada'] = idx
                    st.session_state['tpv_teclado_buffer'] = ''
                    st.rerun()
            with cols[1]:
                st.markdown(f"<div style='font-size: 0.9rem; color: #f8fafc;'>{linea['cantidad']} x {linea['nombre']}</div>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<div style='font-size: 0.85rem; color: #94a3b8; text-align: right;'>€{linea['precio_unitario']:.2f}</div>", unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f"<div style='font-size: 0.9rem; color: #10b981; text-align: right; font-weight: 600;'>€{linea['subtotal']:.2f}</div>", unsafe_allow_html=True)
            with cols[4]:
                if st.button("➖", key=f"btn_menos_{idx}"):
                    actualizar_cantidad_linea(idx, linea['cantidad'] - 1)
                    st.rerun()
            with cols[5]:
                if st.button("➕", key=f"btn_mas_{idx}"):
                    actualizar_cantidad_linea(idx, linea['cantidad'] + 1)
                    st.rerun()
            with cols[6]:
                if st.button("🗑️", key=f"btn_del_{idx}"):
                    actualizar_cantidad_linea(idx, 0)
                    st.rerun()

            st.markdown(f"<div style='background: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; margin: 2px -5px; padding: 4px 8px;'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Teclado numérico funcional
    if carrito:
        render_teclado_numerico()

    st.markdown("---")

    # Total y descuento
    total = calcular_total_carrito()
    descuento_pct = st.session_state.get('tpv_descuento', 0)
    total_con_desc = round(total * (1 - descuento_pct / 100), 2)

    if descuento_pct > 0:
        st.markdown(f"<p style='text-align: center; color: #f59e0b; font-size: 0.85rem;'>Descuento: {descuento_pct}% | Original: €{total:.2f}</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: #3b82f6; margin: 5px 0;'>Total: €{total_con_desc:.2f}</h2>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h2 style='text-align: center; color: #3b82f6; margin: 10px 0;'>Total: €{total:.2f}</h2>", unsafe_allow_html=True)

    # Botón descuento rápido
    if carrito:
        col_dto1, col_dto2, col_dto3 = st.columns(3)
        for col, pct in zip([col_dto1, col_dto2, col_dto3], [5, 10, 20]):
            with col:
                if st.button(f"DTO {pct}%", key=f"dto_{pct}", width="stretch"):
                    st.session_state['tpv_descuento'] = pct if st.session_state.get('tpv_descuento') != pct else 0
                    st.rerun()

    # Botones de acción con gradientes (usando markdown HTML porque Streamlit no permite clases CSS en buttons)
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] div:nth-child(1) button[data-testid="baseButton-primary"],
        div[data-testid="stHorizontalBlock"] div:nth-child(1) button[data-testid="baseButton-secondary"] {
            background: linear-gradient(135deg, #10b981, #059669) !important;
            color: white !important; border: none !important;
            border-radius: 10px !important; font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(16,185,129,0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("💶 Efectivo", width="stretch", type="primary", disabled=not carrito, key="btn_efectivo_grad"):
            st.session_state['tpv_metodo_pago'] = 'efectivo'
            st.session_state['tpv_mostrar_cobro'] = True
            st.rerun()
    with col2:
        st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] div:nth-child(2) button[data-testid="baseButton-primary"],
        div[data-testid="stHorizontalBlock"] div:nth-child(2) button[data-testid="baseButton-secondary"] {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
            color: #0f172a !important; border: none !important;
            border-radius: 10px !important; font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246,0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("💳 Tarjeta", width="stretch", type="primary", disabled=not carrito, key="btn_tarjeta_grad"):
            st.session_state['tpv_metodo_pago'] = 'tarjeta'
            st.session_state['tpv_mostrar_cobro'] = True
            st.rerun()
    with col3:
        st.markdown("""
        <style>
        div[data-testid="stHorizontalBlock"] div:nth-child(3) button[data-testid="baseButton-primary"],
        div[data-testid="stHorizontalBlock"] div:nth-child(3) button[data-testid="baseButton-secondary"] {
            background: linear-gradient(135deg, #64748b, #475569) !important;
            color: white !important; border: none !important;
            border-radius: 10px !important; font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("🧹 Limpiar", width="stretch", type="secondary", key="btn_limpiar_grad"):
            st.session_state['tpv_descuento'] = 0
            limpiar_carrito()
            st.rerun()

    # Alerta de stock bajo
    if carrito:
        _render_alerta_stock_bajo(carrito)

    st.markdown("</div>", unsafe_allow_html=True)


def _procesar_barcode(texto: str):
    """Busca producto por código de barras o nombre y lo agrega al carrito."""
    texto = texto.strip().lower()
    if not texto:
        return
    productos, inventarios, tickets = _get_ventas_data()
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
    productos, inventarios, tickets = _get_ventas_data()
    inv_dict = {i['producto_id']: i['cantidad'] for i in inventarios}
    alertas = []
    for linea in carrito:
        stock_restante = inv_dict.get(linea['producto_id'], 0)
        if stock_restante < 5:
            alertas.append(f"⚠️ {linea['nombre']}: quedan {stock_restante} unidades")
    if alertas:
        st.markdown(f"<div class='alerta-stock-bajo'>{'<br>'.join(alertas)}</div>", unsafe_allow_html=True)


def render_teclado_numerico():
    """Teclado numérico funcional para cambiar cantidades."""
    linea_sel = st.session_state.get('tpv_linea_seleccionada')
    if linea_sel is None:
        st.markdown("<p style='color: #64748b; font-size: 0.8rem; text-align: center;'>👆 Selecciona una línea y usa el teclado para cambiar la cantidad</p>", unsafe_allow_html=True)
        return

    buffer = st.session_state.get('tpv_teclado_buffer', '')
    st.markdown(f"<p style='color: #3b82f6; font-size: 1.2rem; text-align: center; margin: 5px 0;'>Cantidad: {buffer if buffer else '...'}</p>", unsafe_allow_html=True)

    teclas = [
        ['7', '8', '9'],
        ['4', '5', '6'],
        ['1', '2', '3'],
        ['0', '.', 'CLR']
    ]

    for fila in teclas:
        cols = st.columns(3)
        for i, tecla in enumerate(fila):
            with cols[i]:
                if st.button(tecla, key=f"tecla_{tecla}", width="stretch"):
                    if tecla == 'CLR':
                        st.session_state['tpv_teclado_buffer'] = ''
                    else:
                        st.session_state['tpv_teclado_buffer'] += tecla
                    st.rerun()

    # Botón aplicar (teclado)
    if buffer:
        try:
            cantidad = int(float(buffer))
            if st.button("✅ Aplicar Cantidad", width="stretch", type="primary"):
                actualizar_cantidad_linea(linea_sel, cantidad)
                st.rerun()
        except ValueError:
            st.error("Cantidad inválida")

    # Alternativa rápida: input directo
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


def render_cobro_modal():
    """Modal centrado de cobro a pantalla completa."""
    total = calcular_total_carrito()
    metodo = st.session_state.get('tpv_metodo_pago', 'efectivo')
    icono = "💵" if metodo == 'efectivo' else "💳"

    # ========== SONIDO AL COBRAR (precarga) ==========
    components.html("""
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
    """, height=0)

    # ========== LAYOUT DEL MODAL ==========
    # Centramos todo usando columnas de Streamlit (sin position:fixed que tapa widgets)
    _, col_center, _ = st.columns([1, 3, 1])

    with col_center:
        # Caja del modal con animación CSS inline
        st.markdown(f"""
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
            <div class="modal-sub">Método: {metodo.upper()}</div>
        </div>
        """, unsafe_allow_html=True)

        entrega = total
        cambio = 0.0

        if metodo == 'efectivo':
            # Botones rápidos de billetes
            st.markdown("<p style='color:#64748b; font-size:0.75rem; margin:0 0 6px 0; text-align:center;'>Rápido:</p>", unsafe_allow_html=True)
            bc1, bc2, bc3, bc4 = st.columns(4)
            for col, val in zip([bc1, bc2, bc3, bc4], [5, 10, 20, 50]):
                with col:
                    if st.button(f"€{val}", key=f"billete_{val}", width="stretch"):
                        st.session_state['tpv_billete_pulsado'] = float(val)
                        st.rerun()

            # Si se pulsó un billete, usar ese valor
            billete_pulsado = st.session_state.pop('tpv_billete_pulsado', None)
            default_val = float(billete_pulsado) if billete_pulsado and billete_pulsado >= total else float(total * 1.1)

            entrega = st.number_input(
                "💶 Entrega (€)", min_value=float(total), value=default_val,
                step=0.5, format="%.2f", key="modal_entrega_v2"
            )
            cambio = round(entrega - total, 2)
            st.markdown(f"<p class='modal-cambio' style='text-align:center;'>Cambio: €{cambio:.2f}</p>", unsafe_allow_html=True)

        # Checkbox
        confirmar = st.checkbox("✅ Confirmar cobro", key="confirmar_cobro_modal_v2")

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # Botones de acción
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❌ Cancelar", width="stretch", key="modal_btn_cancel_v2"):
                st.session_state['tpv_mostrar_cobro'] = False
                st.rerun()
        with c2:
            disabled = not confirmar
            btn_type = "primary" if confirmar else "secondary"
            if st.button("✅ Finalizar Venta", width="stretch", type=btn_type, disabled=disabled, key="modal_btn_ok_v2"):
                # Reproducir sonido
                components.html("""
                <script>document.getElementById('sonido-cobro').play();</script>
                """, height=0)
                with st.spinner("Registrando venta..."):
                    db = DatabaseAccess()
                    try:
                        lineas_data = []
                        for linea in get_tpv_carrito():
                            lineas_data.append({
                                "producto_id": linea['producto_id'],
                                "cantidad": linea['cantidad'],
                                "precio_unitario": linea['precio_unitario'],
                                "subtotal": linea['cantidad'] * linea['precio_unitario']
                            })
                        data = {
                            "cajero": st.session_state['tpv_cajero'],
                            "metodo_pago": metodo,
                            "entrega_efectivo": entrega if metodo == 'efectivo' else None,
                            "cambio": cambio if metodo == 'efectivo' else None,
                            "total": calcular_total_carrito(),
                            "lineas": lineas_data
                        }
                        result = db.crear_ticket(data)
                        if result:
                            result_dict = _obj_to_dict(result)
                            result_dict['lineas'] = [_obj_to_dict(l) for l in result.lineas]
                            st.session_state['tpv_mostrar_cobro'] = False
                            st.session_state['tpv_mostrar_ticket'] = True
                            st.session_state['tpv_ticket_reciente'] = result_dict
                            st.session_state['tpv_ticket_time'] = time.time()
                            limpiar_carrito()
                            st.rerun()
                        else:
                            st.error("❌ Error al registrar el ticket")
                    finally:
                        db.close()


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
    st.markdown("</div>", unsafe_allow_html=True)

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


def generar_ticket_txt(ticket: dict) -> str:
    """Genera el contenido del ticket en formato texto."""
    lineas = []
    lineas.append("-" * 42)
    lineas.append("           MARKE TTALENTO")
    lineas.append(f"         Ticket N° {ticket['numero_ticket']}")
    lineas.append(f"    {ticket['fecha'][:16].replace('T', ' ')}")
    lineas.append(f"    Cajero: {ticket['cajero']}")
    lineas.append("-" * 42)
    for linea in ticket['lineas']:
        nombre = linea.get('producto', {}).get('nombre', f"Prod {linea['producto_id']}")
        lineas.append(f"{linea['cantidad']} x {nombre:<20} {linea['subtotal']:>7.2f} €")
    lineas.append("-" * 42)
    lineas.append(f"TOTAL:{'':>28} {ticket['total']:>7.2f} €")
    lineas.append(f"Metodo: {ticket['metodo_pago'].upper()}")
    if ticket.get('entrega_efectivo'):
        lineas.append(f"Entrega:{'':>27} {ticket['entrega_efectivo']:>7.2f} €")
        lineas.append(f"Cambio:{'':>28} {ticket['cambio']:>7.2f} €")
    lineas.append("-" * 42)
    lineas.append("      ¡Gracias por su visita!")
    lineas.append("-" * 42)
    return "\n".join(lineas)


def render_panel_productos():
    """Panel derecho: Categorías y productos con búsqueda, colores, badges y favoritos."""
    productos, inventarios, tickets = _get_ventas_data()
    db = DatabaseAccess()
    try:
        categorias = db.get_categorias()
        categorias = [_obj_to_dict(c) for c in categorias]
    finally:
        db.close()

    if not productos:
        st.warning("⚠️ No hay productos disponibles")
        return

    if not inventarios:
        st.error("⚠️ Error al cargar inventario. Los productos pueden aparecer como no disponibles.")
        st.button("🔄 Reintentar", on_click=lambda: st.rerun(), key="retry_inventario")
        inventarios = []

    cat_activa = st.session_state.get('tpv_categoria_activa', 'todos')

    # ========== BARRA DE BÚSQUEDA ==========
    busqueda = st.text_input("🔍 Buscar producto...", key="tpv_busqueda_prod", label_visibility="collapsed")
    if busqueda:
        productos = [p for p in productos if busqueda.lower() in p.get('nombre', '').lower()]

    # ========== COLORES POR CATEGORÍA ==========
    COLORES_CAT = {
        'Bebidas': '#f59e0b', 'Cervezas': '#fbbf24', 'Whiskies': '#a78bfa',
        'Cafés': '#92400e', 'Refrescos': '#ef4444', 'Hamburguesas': '#f97316',
        'Pizzas': '#f59e0b', 'Bocadillos': '#10b981', 'Menus': '#3b82f6',
        'Todos': '#3b82f6'
    }

    # Fila de categorías
    cats_filtradas = [{"id": "todos", "nombre": "Todos"}] + [{"id": c["id"], "nombre": c["nombre"]} for c in categorias]
    cols_cats = st.columns(min(len(cats_filtradas), 6))
    for i, cat in enumerate(cats_filtradas[:6]):
        with cols_cats[i]:
            es_activa = cat_activa == cat["id"]
            color_cat = COLORES_CAT.get(cat["nombre"], '#3b82f6')
            bg = f"rgba({int(color_cat[1:3],16)},{int(color_cat[3:5],16)},{int(color_cat[5:7],16)},0.15)" if es_activa else "rgba(30,41,59,0.6)"
            border = f"1px solid {color_cat}" if es_activa else "1px solid rgba(255,255,255,0.1)"
            st.markdown(f"""
            <style>
            div[data-testid="stHorizontalBlock"] div:nth-child({i+1}) button[data-testid="baseButton-secondary"] {{
                background: {bg} !important;
                border: {border} !important;
                color: {color_cat if es_activa else '#94a3b8'} !important;
                border-radius: 10px !important;
                font-weight: {'700' if es_activa else '500'} !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            if st.button(cat["nombre"], key=f"cat_{cat['id']}", width="stretch"):
                st.session_state['tpv_categoria_activa'] = cat["id"]
                st.rerun()

    st.markdown("<hr style='margin: 10px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    # Filtrar por categoría
    if cat_activa != 'todos':
        productos = [p for p in productos if p.get('categoria_id') == cat_activa]

    # ========== ORDENAR POR MÁS VENDIDOS (FAVORITOS) ==========
    try:
        db = DatabaseAccess()
        tickets = db.get_tickets(limite=200)
        tickets = [_obj_to_dict(t) for t in tickets]
        db.close()
        
        prod_ventas = {}
        for t in tickets:
            for linea in t.get('lineas', []):
                pid = linea.get('producto_id')
                prod_ventas[pid] = prod_ventas.get(pid, 0) + linea.get('cantidad', 0)
        
        productos.sort(key=lambda p: (-prod_ventas.get(p.get('id'), 0), p.get('nombre', '')))
    except Exception:
        pass

    # ========== MODAL CANTIDAD (doble-click simulado) ==========
    if st.session_state.get('tpv_modal_cantidad_prod_id'):
        _render_modal_cantidad(productos, inventarios)

    # Grid de productos
    cols_grid = st.columns(4)
    for idx, prod in enumerate(productos):
        stock = _get_stock(prod.get('id'), inventarios)
        sin_stock = stock <= 0
        imagen = _buscar_imagen_producto(prod)
        es_favorito = prod.get('id') in prod_ventas and prod_ventas.get(prod.get('id'), 0) > 0

        with cols_grid[idx % 4]:
            opacity = "0.4" if sin_stock else "1"
            cursor = "not-allowed" if sin_stock else "pointer"
            border_color = "#ef4444" if sin_stock else ("#f59e0b" if es_favorito else "rgba(255,255,255,0.1)")
            border_width = "2px" if (sin_stock or es_favorito) else "1px"

            # Badge stock
            badge_class = "tpv-badge-stock"
            if stock <= 0:
                badge_class += " tpv-badge-stock-critico"
            elif stock < 5:
                badge_class += " tpv-badge-stock-bajo"
            badge_html = f'<div class="{badge_class}">{stock}</div>' if not sin_stock else ''

            card_html = f"""
            <div style="position: relative; opacity: {opacity}; border: {border_width} solid {border_color}; border-radius: 10px; padding: 10px;
                        background: rgba(30,41,59,0.8); cursor: {cursor}; text-align: center;
                        margin-bottom: 10px; height: 150px; display: flex; flex-direction: column;
                        justify-content: space-between;">
                {badge_html}
            """

            if imagen and imagen.startswith("data:image"):
                card_html += f'<img src="{imagen}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; margin: 0 auto;">'
            elif imagen and os.path.exists(imagen):
                try:
                    with open(imagen, "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode()
                    fmt = 'png' if imagen.lower().endswith('.png') else 'jpeg'
                    card_html += f'<img src="data:image/{fmt};base64,{img_b64}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; margin: 0 auto;">'
                except Exception:
                    card_html += f'<div style="font-size: 2rem; margin: 0 auto;">📦</div>'
            else:
                card_html += f'<div style="font-size: 2rem; margin: 0 auto;">📦</div>'

            nombre_display = prod.get('nombre') + (' ⭐' if es_favorito else '')
            card_html += f"""
                <div style="font-size: 0.85rem; font-weight: 600; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{nombre_display}</div>
                <div style="font-size: 0.9rem; color: #3b82f6; font-weight: 700;">€{prod.get('precio_venta', 0):.2f}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            if not sin_stock:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("➕", key=f"add_prod_{prod.get('id')}", width="stretch"):
                        agregar_linea_carrito(prod)
                        st.rerun()
                with c2:
                    if st.button("#️⃣", key=f"cant_prod_{prod.get('id')}", width="stretch", help="Cantidad"):
                        st.session_state['tpv_modal_cantidad_prod_id'] = prod.get('id')
                        st.rerun()


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

    st.markdown(f"<div class='mini-modal'>", unsafe_allow_html=True)
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
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# TAB DASHBOARD
# ============================================================================

def render_dashboard():
    """Dashboard completo con métricas y 10 gráficas."""
    db = DatabaseAccess()
    try:
        resumen = db.obtener_estadisticas_resumen()
        tickets = db.get_tickets(limite=500)
        tickets_dict = [_obj_to_dict(t) for t in tickets]
    finally:
        db.close()
    
    if not tickets_dict or resumen.get('total_tickets', 0) == 0:
        st.info("📊 No hay tickets registrados aún. ¡Usa el TPV para registrar ventas!")
        return
    
    st.info("📊 Dashboard de ventas requiere iniciar la API con: uvicorn src.api:app --port 8002")
    st.markdown("### Datos Disponibles")
    st.metric("💰 Total Ingresos", f"€{resumen.get('total_ingresos', 0):.2f}")
    st.metric("🎫 Tickets", resumen.get('total_tickets', 0))
    st.metric("📦 Unidades", resumen.get('total_unidades', 0))
    st.metric("📈 Ticket Promedio", f"€{resumen.get('ticket_promedio', 0):.2f}")
    st.markdown("---")
    
    # Gráficas básicas
    try:
        db = DatabaseAccess()
        tickets = db.get_tickets(limite=500)
        productos = db.get_productos()
        categorias = db.get_categorias()
        tickets_dict = [_obj_to_dict(t) for t in tickets]
        productos = [_obj_to_dict(p) for p in productos]
        categorias = [_obj_to_dict(c) for c in categorias]
        db.close()
        
        if tickets_dict:
            # Gráfica 1: Ventas por día
            st.markdown("#### 📈 Tendencia de Ventas")
            ventas_dia = {}
            for t in tickets_dict:
                fecha = str(t.get('fecha', ''))[:10]
                ventas_dia[fecha] = ventas_dia.get(fecha, 0) + t.get('total', 0)
            
            if ventas_dia:
                fechas = sorted(ventas_dia.keys())[-15:]
                valores = [ventas_dia[f] for f in fechas]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=fechas, y=valores, mode='lines+markers', line=dict(color='#3b82f6', width=2), fill='tozeroy', fillcolor='rgba(59, 130, 246,0.1)'))
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94a3b8', height=280, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, width="stretch")
            
            # Gráfica 2: Top productos (siempre mostrar)
            st.markdown("#### 🏆 Top Productos")
            prod_ventas = {}
            for t in tickets_dict:
                for linea in t.get('lineas', []):
                    pid = linea.get('producto_id')
                    nombre = f"Prod {pid}"
                    for p in productos:
                        if p.get('id') == pid:
                            nombre = p.get('nombre', f"Prod {pid}")
                            break
                    prod_ventas[nombre] = prod_ventas.get(nombre, 0) + linea.get('cantidad', 0)
            
            if not prod_ventas:
                # Demo data si no hay ventas
                for p in productos[:5]:
                    prod_ventas[p.get('nombre', f"Prod {p.get('id')}")] = 0
            
            top_prods = sorted(prod_ventas.items(), key=lambda x: x[1], reverse=True)[:10]
            nombres = [p[0] for p in top_prods]
            cantidades = [p[1] for p in top_prods]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=nombres, y=cantidades, marker_color='#10b981'))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94a3b8', height=280, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, width="stretch")
            
            # Gráfica 3: Ventas por hora
            st.markdown("#### ⏰ Ventas por Hora")
            horas = {h: 0 for h in range(24)}
            for t in tickets_dict:
                fecha = str(t.get('fecha', ''))
                if len(fecha) > 13:
                    try:
                        hora = int(fecha[11:13])
                    except ValueError:
                        continue
                    horas[hora] += t.get('total', 0)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=list(horas.keys()), y=list(horas.values()), marker_color='#f59e0b'))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94a3b8', height=280, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, width="stretch")
            
            # Gráfica 4: Métodos de pago (siempre mostrar aunque vacío)
            st.markdown("#### 💳 Métodos de Pago")
            metodos = {}
            for t in tickets_dict:
                mp = t.get('metodo_pago', 'desconocido')
                metodos[mp] = metodos.get(mp, 0) + 1
            
            if not metodos:
                metodos = {"sin datos": 1}
            fig = go.Figure()
            fig.add_trace(go.Pie(labels=list(metodos.keys()), values=list(metodos.values()), hole=0.4))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94a3b8', height=280, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, width="stretch")
            
            # Gráfica 5: Ingresos por categoría (siempre mostrar)
            st.markdown("#### 🏷️ Ingresos por Categoría")
            cat_ingresos = {}
            cat_map = {c.get('id'): c.get('nombre', 'Sin categoría') for c in categorias}
            for t in tickets_dict:
                for linea in t.get('lineas', []):
                    pid = linea.get('producto_id')
                    cat_id = None
                    for p in productos:
                        if p.get('id') == pid:
                            cat_id = p.get('categoria_id')
                            break
                    cat_nombre = cat_map.get(cat_id, 'Sin categoría')
                    cat_ingresos[cat_nombre] = cat_ingresos.get(cat_nombre, 0) + linea.get('subtotal', 0)
            
            if not cat_ingresos:
                cat_ingresos = {"sin datos": 0}
            fig = go.Figure()
            fig.add_trace(go.Bar(x=list(cat_ingresos.keys()), y=list(cat_ingresos.values()), marker_color='#8b5cf6'))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94a3b8', height=280, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, width="stretch")
            
            # Gráfica 6: Ticket promedio por día (siempre mostrar)
            st.markdown("#### 📊 Evolución Ticket Promedio")
            dia_tickets = {}
            for t in tickets_dict:
                fecha = str(t.get('fecha', ''))[:10]
                if fecha not in dia_tickets:
                    dia_tickets[fecha] = {'total': 0, 'count': 0}
                dia_tickets[fecha]['total'] += t.get('total', 0)
                dia_tickets[fecha]['count'] += 1
            
            fechas = sorted(dia_tickets.keys())[-15:] if dia_tickets else []
            prom_tickets = [round(dia_tickets[f]['total'] / dia_tickets[f]['count'], 2) if dia_tickets[f]['count'] > 0 else 0 for f in fechas]
            if not fechas:
                fechas = ["sin datos"]
                prom_tickets = [0]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=fechas, y=prom_tickets, mode='lines+markers', line=dict(color='#ef4444', width=2), fill='tozeroy', fillcolor='rgba(239,68,68,0.1)'))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94a3b8', height=280, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, width="stretch")
            
            # Gráfica 7: Distribución tickets por rango de precio (siempre mostrar)
            st.markdown("#### 💰 Distribución por Importe")
            rangos = {"€0-10": 0, "€10-25": 0, "€25-50": 0, "€50-100": 0, "€100+": 0}
            for t in tickets_dict:
                total = t.get('total', 0)
                if total <= 10:
                    rangos["€0-10"] += 1
                elif total <= 25:
                    rangos["€10-25"] += 1
                elif total <= 50:
                    rangos["€25-50"] += 1
                elif total <= 100:
                    rangos["€50-100"] += 1
                else:
                    rangos["€100+"] += 1
            
            fig = go.Figure()
            fig.add_trace(go.Pie(labels=list(rangos.keys()), values=list(rangos.values()), hole=0.4, marker_colors=["#b21798", "#116025", "#ffa200", "#dd1f1f", "#5c1bf3"]))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#94a3b8', height=280, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, width="stretch")
    except Exception as e:
        st.warning(f"Error cargando gráficas: {str(e)}")


def _plotly_config(fig, height=280):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8',
        margin=dict(l=0, r=0, t=30, b=0),
        height=height,
        xaxis_gridcolor='rgba(255,255,255,0.05)',
        yaxis_gridcolor='rgba(255,255,255,0.05)',
    )
    return fig


def grafica_tendencia(datos):
    st.markdown("#### 📈 Tendencia de Ventas")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['ingresos'],
        mode='lines+markers',
        name='Ingresos',
        line=dict(color='#3b82f6', width=3),
        fill='tozeroy', fillcolor='rgba(59, 130, 246,0.1)'
    ))
    fig.update_layout(title_text="Ingresos por día", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_top_productos_unidades(datos):
    st.markdown("#### 🥇 Top Productos (Unidades)")
    if not datos:
        st.info("Sin datos")
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
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Bar(
        x=df['hora'], y=df['ventas'],
        marker_color='#f59e0b'
    )])
    fig.update_layout(title_text="Distribución horaria", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_distribucion_ingresos(resumen):
    st.markdown("#### 📊 Distribución Ingresos")
    db = DatabaseAccess()
    try:
        tickets = db.get_tickets(limite=500)
        tickets = [_obj_to_dict(t) for t in tickets]
    finally:
        db.close()
    
    if not tickets:
        st.info("Sin datos")
        return
    rangos = {"€0-10": 0, "€10-25": 0, "€25-50": 0, "€50-100": 0, "€100+": 0}
    for t in tickets:
        total = t.get('total', 0)
        if total <= 10:
            rangos["€0-10"] += 1
        elif total <= 25:
            rangos["€10-25"] += 1
        elif total <= 50:
            rangos["€25-50"] += 1
        elif total <= 100:
            rangos["€50-100"] += 1
        else:
            rangos["€100+"] += 1
    fig = go.Figure(data=[go.Pie(
        labels=list(rangos.keys()), values=list(rangos.values()),
        hole=0.4,
        marker_colors=["#b21798", "#116025", "#ffa200", "#dd1f1f", "#5c1bf3"]
    )])
    fig.update_layout(title_text="Por rango de ticket", title_font_size=12, showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_ventas_por_categoria(datos):
    st.markdown("#### 🏷️ Ventas por Categoría")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Pie(
        labels=df['categoria'], values=df['ingresos'],
        hole=0.5,
        marker_colors=px.colors.sequential.Plasma
    )])
    fig.update_layout(title_text="Ingresos por categoría", title_font_size=12,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_ticket_promedio(datos):
    st.markdown("#### 📉 Ticket Promedio")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['ticket_promedio'],
        mode='lines+markers',
        line=dict(color='#8b5cf6', width=3),
        fill='tozeroy', fillcolor='rgba(139,92,246,0.1)'
    ))
    fig.update_layout(title_text="Evolución del ticket promedio", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), width="stretch")


def grafica_top_productos_ingresos(datos):
    st.markdown("#### 💶 Top Productos (Ingresos)")
    if not datos:
        st.info("Sin datos")
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
        st.info("Sin datos")
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
        st.info("Sin datos")
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
        st.info("Sin datos")
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
        st.info("Sin datos")
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
        textfont=dict(size=14, color='white')
    ))
    fig.add_hline(y=meta, line_dash="dash", line_color="#f59e0b", annotation_text="🎯 Meta")
    fig.update_layout(title_text=f"Progreso: {pct:.0f}%", title_font_size=12, showlegend=False)
    st.plotly_chart(_plotly_config(fig, height=220), width="stretch")
    if restante > 0:
        st.markdown(f"<p style='text-align:center; color:#94a3b8; font-size:0.8rem;'>Faltan €{restante:.2f} para la meta</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p style='text-align:center; color:#10b981; font-size:0.85rem; font-weight:600;'>🎉 ¡Meta alcanzada!</p>", unsafe_allow_html=True)


# ============================================================================
# TAB HISTORIAL
# ============================================================================

def render_historial():
    """Historial de tickets con filtros rápidos y anulación."""
    st.markdown("### 📋 Historial de Tickets")

    # Botones de filtro rápido de fecha
    st.markdown("<p style='color: #64748b; font-size: 0.85rem; margin-bottom: 5px;'>📅 Filtro rápido:</p>", unsafe_allow_html=True)
    cols_fecha = st.columns(5)
    opciones_fecha = [
        ("Hoy", 0, 0), ("Ayer", 1, 1), ("Últimos 7 días", 7, 0),
        ("Este mes", 30, 0), ("Todo", 365, 0)
    ]
    fecha_desde = None
    fecha_hasta = None
    for col, (label, dias_atras, dias_fin) in zip(cols_fecha, opciones_fecha):
        with col:
            if st.button(label, width="stretch", key=f"hist_fecha_{label.replace(' ', '_')}"):
                hoy = datetime.now().date()
                if dias_atras == 365:
                    st.session_state['hist_fecha_desde'] = None
                    st.session_state['hist_fecha_hasta'] = None
                else:
                    st.session_state['hist_fecha_desde'] = (hoy - timedelta(days=dias_atras)).isoformat()
                    st.session_state['hist_fecha_hasta'] = (hoy - timedelta(days=dias_fin)).isoformat()
                st.rerun()

    # Filtros avanzados
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        cajeros_opciones = ["Todos"] + CAJEROS
        filtro_cajero = st.selectbox("Cajero", cajeros_opciones, key="hist_cajero")

    with col2:
        default_desde = None
        if st.session_state.get('hist_fecha_desde'):
            default_desde = datetime.fromisoformat(st.session_state['hist_fecha_desde']).date()
        fecha_desde = st.date_input("Desde", value=default_desde, key="hist_desde")

    with col3:
        default_hasta = None
        if st.session_state.get('hist_fecha_hasta'):
            default_hasta = datetime.fromisoformat(st.session_state['hist_fecha_hasta']).date()
        fecha_hasta = st.date_input("Hasta", value=default_hasta, key="hist_hasta")

    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", width="stretch"):
            st.rerun()

    # Construir query params
    params = {"limite": 200}
    if filtro_cajero != "Todos":
        params["cajero"] = filtro_cajero
    if fecha_desde:
        params["fecha_desde"] = fecha_desde.isoformat()
    if fecha_hasta:
        params["fecha_hasta"] = fecha_hasta.isoformat()

    # Cargar tickets
    db = DatabaseAccess()
    try:
        tickets_db = db.get_tickets(limite=200)
        tickets = [_obj_to_dict(t) for t in tickets_db]
        
        if filtro_cajero != "Todos":
            tickets = [t for t in tickets if t.get('cajero') == filtro_cajero]
        if fecha_desde:
            tickets = [t for t in tickets if str(t.get('fecha', '')) >= str(fecha_desde)]
        if fecha_hasta:
            tickets = [t for t in tickets if str(t.get('fecha', ''))[:10] <= str(fecha_hasta)]
    finally:
        db.close()

    if not tickets:
        st.info("📭 No hay tickets en el período seleccionado")
        return

    # Exportar
    if tickets:
        df_export = []
        for t in tickets:
            for linea in t.get('lineas', []):
                df_export.append({
                    "ticket": t['numero_ticket'],
                    "fecha": t['fecha'][:16].replace('T', ' '),
                    "cajero": t['cajero'],
                    "estado": t['estado'],
                    "metodo_pago": t['metodo_pago'],
                    "producto": linea.get('producto', {}).get('nombre', ''),
                    "cantidad": linea['cantidad'],
                    "precio_unitario": linea['precio_unitario'],
                    "subtotal": linea['subtotal'],
                    "total_ticket": t['total']
                })
        if df_export:
            excel_data = to_excel(pd.DataFrame(df_export))
            st.download_button("📥 Exportar Excel", data=excel_data,
                               file_name=f"historial_tickets_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               width="stretch")

    # Paginación
    pagina = st.session_state.get('tpv_pagina_historial', 1)
    por_pagina = 10
    total_paginas = max(1, (len(tickets) + por_pagina - 1) // por_pagina)
    pagina = min(pagina, total_paginas)
    inicio = (pagina - 1) * por_pagina
    fin = min(inicio + por_pagina, len(tickets))

    # Mostrar tickets
    for t in tickets[inicio:fin]:
        estado_color = "#10b981" if t['estado'] == 'completado' else "#ef4444"
        with st.expander(f"🎫 Ticket N° {t.get('numero_ticket', 'N/A')} | €{t.get('total', 0):.2f} | {t.get('cajero', 'N/A')} | {_format_fecha(t.get('fecha', ''))}"):
            st.markdown(f"<p style='color: {estado_color}; font-weight: 600;'>Estado: {t['estado'].upper()}</p>", unsafe_allow_html=True)
            st.markdown(f"**Método de pago:** {t['metodo_pago'].upper()}")
            if t.get('entrega_efectivo'):
                st.markdown(f"**Entrega:** €{t['entrega_efectivo']:.2f} | **Cambio:** €{t['cambio']:.2f}")

            # Tabla de líneas
            lineas_data = []
            for linea in t.get('lineas', []):
                prod_id = linea.get('producto_id', 'N/A')
                nombre = f"Producto {prod_id}"
                lineas_data.append({
                    "Producto": nombre,
                    "Cantidad": linea.get('cantidad', 0),
                    "P. Unitario": f"€{linea.get('precio_unitario', 0):.2f}",
                    "Subtotal": f"€{linea.get('subtotal', 0):.2f}"
                })
            if lineas_data:
                st.table(pd.DataFrame(lineas_data))

            # Botón anular (solo si está completado)
            if t['estado'] == 'completado':
                col_a, _ = st.columns([1, 3])
                with col_a:
                    if st.button("❌ Anular Ticket", key=f"anular_{t['id']}", width="stretch"):
                        with st.spinner("Anulando..."):
                            db = DatabaseAccess()
                            try:
                                from src.dominio.entidades.entidades import Ticket
                                ticket_db = db.session.query(Ticket).get(t['id'])
                                if ticket_db:
                                    ticket_db.estado = 'anulado'
                                    db.session.commit()
                                    st.success("Ticket anulado correctamente")
                                    st.rerun()
                                else:
                                    st.error("Ticket no encontrado")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                                db.session.rollback()
                            finally:
                                db.close()

    # Controles paginación
    if total_paginas > 1:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("⬅️ Anterior", disabled=pagina <= 1, key="hist_ant"):
                st.session_state['tpv_pagina_historial'] = pagina - 1
                st.rerun()
        with c2:
            st.markdown(f"<p style='text-align: center;'>Página {pagina} de {total_paginas}</p>", unsafe_allow_html=True)
        with c3:
            if st.button("Siguiente ➡️", disabled=pagina >= total_paginas, key="hist_sig"):
                st.session_state['tpv_pagina_historial'] = pagina + 1
                st.rerun()
