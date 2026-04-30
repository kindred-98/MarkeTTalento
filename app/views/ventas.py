"""
Página de Ventas
"""
import streamlit as st
import pandas as pd
from app.utils.api import api_get, api_post
from app.utils.helpers import to_excel, format_currency
from app.logic.venta import preparar_datos_ventas, validar_venta


def render():
    """Renderiza la página de ventas."""
    st.markdown("<h2>💰 Gestión de Ventas</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Historial", "➕ Nueva"])
    
    with tab1:
        ventas = api_get("/api/v1/ventas")
        productos = api_get("/api/v1/productos")
        
        # Exportar
        if ventas:
            def get_prod_name(pid):
                for p in productos:
                    if p.get("id") == pid:
                        return p.get("nombre", "Producto")
                return "Producto"
            
            df_ventas = pd.DataFrame([{
                "Fecha": v.get("fecha", "")[:10],
                "Producto": get_prod_name(v.get("producto_id")),
                "Cantidad": v.get("cantidad"),
                "Precio Unit.": v.get("precio_unitario"),
                "Total": v.get("cantidad", 0) * v.get("precio_unitario", 0)
            } for v in ventas])
            
            excel_ventas = to_excel(df_ventas)
            col_exp, _ = st.columns([1, 3])
            with col_exp:
                st.download_button("📥 Exportar Excel", data=excel_ventas, file_name="ventas.xlsx", use_container_width=True)
        
        # Mostrar ventas
        if ventas:
            for venta in ventas[:20]:
                cantidad = venta.get("cantidad", 0)
                precio = venta.get("precio_unitario", 0)
                total = cantidad * precio
                
                prod_nombre = "Producto"
                for p in productos:
                    if p.get("id") == venta.get("producto_id"):
                        prod_nombre = p.get("nombre", "Producto")
                        break
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(26,35,50,0.8) 0%, rgba(26,35,50,0.6) 100%); border: 1px solid rgba(0,240,255,0.15); border-radius: 14px; padding: 16px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 1rem; font-weight: 600; color: #00f0ff;">{prod_nombre}</div>
                        <div style="color: #94a3b8; font-size: 0.8rem;">{venta.get('fecha', '')[:10]}</div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px;">
                        <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Cantidad</div>
                            <div style="font-size: 1rem; font-weight: 600; color: #f1f5f9; margin-top: 4px;">{cantidad}</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Precio unit.</div>
                            <div style="font-size: 1rem; font-weight: 600; color: #f1f5f9; margin-top: 4px;">€{precio:.2f}</div>
                        </div>
                        <div style="background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(0,240,255,0.1)); border-radius: 10px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Total</div>
                            <div style="font-size: 1rem; font-weight: 600; color: #10b981; margin-top: 4px;">€{total:.2f}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay ventas registradas")
    
    with tab2:
        productos = api_get("/api/v1/productos")
        inventarios = api_get("/api/v1/inventario")
        
        if productos:
            with st.form("nueva_venta"):
                prod_options = {f"{p.get('nombre')} (Stock: {get_stock(p.get('id'), inventarios)})": p.get("id") for p in productos}
                producto_sel = st.selectbox("Producto", list(prod_options.keys()))
                producto_id = prod_options.get(producto_sel)
                
                stock_actual = get_stock(producto_id, inventarios)
                st.info(f"Stock disponible: {stock_actual}")
                
                cantidad = st.number_input("Cantidad", min_value=1, max_value=stock_actual, value=1)
                
                precio = 0
                for p in productos:
                    if p.get("id") == producto_id:
                        precio = p.get("precio_venta", 0)
                        break
                
                st.write(f"Precio unitario: €{precio:.2f}")
                st.write(f"**Total: €{cantidad * precio:.2f}**")
                
                if st.form_submit_button("💾 Registrar Venta"):
                    if cantidad > stock_actual:
                        st.error("Stock insuficiente")
                    else:
                        result = api_post("/api/v1/ventas", {
                            "producto_id": producto_id,
                            "cantidad": cantidad,
                            "precio_unitario": precio
                        })
                        if result:
                            st.success("✅ Venta registrada")
                            st.rerun()
                        else:
                            st.error("❌ Error al registrar")
        else:
            st.warning("No hay productos disponibles")


def get_stock(producto_id, inventarios):
    """Obtiene el stock de un producto."""
    for inv in inventarios:
        if inv.get("producto_id") == producto_id:
            return inv.get("cantidad", 0)
    return 0
