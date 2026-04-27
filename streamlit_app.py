import streamlit as st
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

API_URL = "http://127.0.0.1:8002"

st.set_page_config(page_title="MarkeTTalento", page_icon="📦", layout="wide")

st.title("📦 MarkeTTalento - Sistema de Inventario Inteligente")

st.markdown("---")

def api_get(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}


def api_post(endpoint, data):
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=5)
        return r.json() if r.status_code in [200, 201] else {}
    except:
        return {}


menu = st.sidebar.selectbox(
    "Menú",
    ["Dashboard", "Productos", "Inventario", "Ventas", "Predicciones", "Visión Artificial"]
)

if menu == "Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Productos", "0")
    with col2:
        st.metric("Stock Total", "0")
    with col3:
        st.metric("Críticos", "0")
    with col4:
        st.metric("Valor", "0€")

    st.markdown("---")
    st.subheader("📊 Estado del Sistema")
    
    try:
        r = requests.get(f"{API_URL}/api/v1/salud", timeout=3)
        if r.status_code == 200:
            data = r.json()
            st.success(f"✅ API Funcionando - {data.get('timestamp', '')}")
        else:
            st.error("❌ API no responde")
    except:
        st.error("❌ No se puede conectar a la API. ¿Está iniciada?")


elif menu == "Productos":
    st.header("📦 Gestión de Productos")
    
    tab1, tab2 = st.tabs(["Listar", "Crear"])
    
    with tab1:
        productos = api_get("/api/v1/productos")
        if productos:
            st.dataframe(productos, use_container_width=True)
        else:
            st.info("No hay productos")
    
    with tab2:
        with st.form("crear_producto"):
            sku = st.text_input("SKU")
            nombre = st.text_input("Nombre")
            precio = st.number_input("Precio", min_value=0.0)
            unidad = st.selectbox("Unidad", ["litro", "kg", "unidad", "paquete", "caja"])
            stock_min = st.number_input("Stock Mínimo", min_value=0)
            stock_max = st.number_input("Stock Máximo", min_value=0)
            tiempo_repo = st.number_input("Tiempo Reposición (días)", min_value=1)
            categoria = st.number_input("Categoría ID", min_value=1)
            
            submit = st.form_submit_button("Crear")
            
            if submit:
                data = {
                    "sku": sku,
                    "nombre": nombre,
                    "precio_venta": precio,
                    "precio_coste": precio * 0.7,
                    "unidad": unidad,
                    "stock_minimo": stock_min,
                    "stock_maximo": stock_max,
                    "tiempo_reposicion": tiempo_repo,
                    "categoria_id": categoria
                }
                result = api_post("/api/v1/productos", data)
                if result:
                    st.success("✅ Producto creado")
                else:
                    st.error("❌ Error al crear")


elif menu == "Inventario":
    st.header("📊 Inventario")
    
    resumen = api_get("/api/v1/inventario/resumen")
    
    if resumen:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Productos", resumen.get("total_productos", 0))
        with col2:
            st.metric("Críticos", resumen.get("productos_criticos", 0))
        with col3:
            st.metric("Valor Total", f"{resumen.get('valor_total', 0)}€")
        
        recomendaciones = resumen.get("recomendaciones", [])
        if recomendaciones:
            st.subheader("⚠️ Recomendaciones")
            st.dataframe(recomendaciones, use_container_width=True)
    else:
        st.info("No hay datos de inventario")


elif menu == "Ventas":
    st.header("💰 Ventas")
    
    tab1, tab2 = st.tabs(["Historial", "Registrar"])
    
    with tab1:
        ventas = api_get("/api/v1/ventas")
        if ventas:
            st.dataframe(ventas, use_container_width=True)
        else:
            st.info("No hay ventas")
    
    with tab2:
        with st.form("registrar_venta"):
            producto_id = st.number_input("Producto ID", min_value=1)
            cantidad = st.number_input("Cantidad", min_value=1)
            precio = st.number_input("Precio Unitario", min_value=0.0)
            
            submit = st.form_submit_button("Registrar")
            
            if submit:
                data = {
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                    "precio_unitario": precio
                }
                result = api_post("/api/v1/ventas", data)
                if result:
                    st.success("✅ Venta registrada")
                else:
                    st.error("❌ Error al registrar")


elif menu == "Predicciones":
    st.header("🔮 Predicciones")
    
    predicciones = api_get("/api/v1/prediccion/todos")
    
    if predicciones:
        for pred in predicciones:
            with st.expander(pred.get("producto", "Producto")):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Días hasta agotarse", pred.get("dias_hasta_agotarse", 0))
                with col2:
                    st.metric("Estado", pred.get("estado", "N/A"))
    else:
        st.info("No hay predicciones disponibles")


elif menu == "Visión Artificial":
    st.header("📸 Detección de Productos")
    
    st.info("Sube una imagen de tu estantería para detectar productos")
    
    archivo = st.file_uploader("Seleccionar imagen", type=["jpg", "png", "jpeg"])
    
    if archivo:
        st.image(archivo, caption="Imagen seleccionada")
        
        if st.button("🔍 Analizar"):
            st.warning("Analizando...")
            # Aquí iría la llamada a la API de visión


st.markdown("---")
st.caption("MarkeTTalento v1.0 - Sistema de Inventario Inteligente")