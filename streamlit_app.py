import streamlit as st
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

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


def conectar_api():
    """Verifica conexión a la API"""
    try:
        r = requests.get(f"{API_URL}/api/v1/salud", timeout=3)
        return r.status_code == 200
    except:
        return False


if not conectar_api():
    st.error("❌ No conectado a la API. Inicia 'python main.py' en otra terminal")
    st.stop()

st.sidebar.success("✅ API Conectada")

menu = st.sidebar.selectbox(
    "Menú",
    ["Dashboard", "Productos", "Inventario", "Ventas", "Predicciones", "Visión Artificial"]
)


if menu == "Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    
    resumen = api_get("/api/v1/inventario/resumen")
    
    with col1:
        st.metric("Productos", resumen.get("total_productos", 0))
    with col2:
        st.metric("Stock Total", resumen.get("total_unidades", 0))
    with col3:
        st.metric("Críticos", resumen.get("productos_criticos", 0))
    with col4:
        valor = resumen.get("valor_total", 0)
        st.metric("Valor", f"€{valor:.2f}")
    
    st.markdown("---")
    
    # Gráfico de estado del inventario
    st.subheader("📊 Estado del Inventario")
    
    datos = [
        {"Estado": "Críticos", "Cantidad": resumen.get("productos_criticos", 0)},
        {"Estado": "Bajos", "Cantidad": resumen.get("productos_bajos", 0)},
        {"Estado": "Adecuados", "Cantidad": resumen.get("productos_adecuados", 0)},
    ]
    
    if any(d["Cantidad"] > 0 for d in datos):
        fig = px.bar(
            datos, 
            x="Estado", 
            y="Cantidad",
            color="Estado",
            color_discrete_map={
                "Críticos": "#FF4B4B",
                "Bajos": "#FFA500",
                "Adecuados": "#4CAF50"
            }
        )
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos suficientes")
    
    # Recomendaciones
    recomendaciones = resumen.get("recomendaciones", [])
    if recomendaciones:
        st.subheader("⚠️ Recomendaciones de Reposición")
        
        for rec in recomendaciones[:5]:
            with st.expander(f"{rec.get('producto')} - {rec.get('estado')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Stock Actual", rec.get("stock_actual", 0))
                    st.metric("Mínimo", rec.get("stock_minimo", 0))
                with col2:
                    st.metric("Días Restantes", rec.get("dias_restantes", 0))
                    st.metric("Cantidad a Reponer", rec.get("cantidad_recomendada", 0))
        
        st.metric("Total Recomendaciones", len(recomendaciones))


elif menu == "Productos":
    st.header("📦 Gestión de Productos")
    
    tab1, tab2, tab3 = st.tabs(["Listar", "Crear", "Buscar"])
    
    with tab1:
        productos = api_get("/api/v1/productos")
        if productos:
            df = pd.DataFrame(productos)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay productos")
    
    with tab2:
        categorias = api_get("/api/v1/categorias")
        
        with st.form("crear_producto"):
            sku = st.text_input("SKU (único)")
            nombre = st.text_input("Nombre")
            precio = st.number_input("Precio Venta", min_value=0.0)
            precio_coste = st.number_input("Precio Coste", min_value=0.0)
            unidad = st.selectbox("Unidad", ["litro", "kg", "unidad", "paquete", "caja", "botella"])
            stock_min = st.number_input("Stock Mínimo", min_value=0, value=5)
            stock_max = st.number_input("Stock Máximo", min_value=0, value=30)
            tiempo_repo = st.number_input("Tiempo Reposición (días)", min_value=1, value=3)
            
            cat_options = {c.get("nombre"): c.get("id") for c in categorias}
            categoria_nombre = st.selectbox("Categoría", list(cat_options.keys()))
            categoria_id = cat_options.get(categoria_nombre)
            
            submit = st.form_submit_button("Crear Producto")
            
            if submit:
                data = {
                    "sku": sku,
                    "nombre": nombre,
                    "precio_venta": precio,
                    "precio_coste": precio_coste,
                    "unidad": unidad,
                    "stock_minimo": stock_min,
                    "stock_maximo": stock_max,
                    "tiempo_reposicion": tiempo_repo,
                    "categoria_id": categoria_id
                }
                result = api_post("/api/v1/productos", data)
                if result:
                    st.success("✅ Producto creado")
                    # Actualizar inventario
                    prod_id = result.get("id")
                    api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": stock_min, "ubicacion": "Por asignar"})
                else:
                    st.error("❌ Error al crear")
    
    with tab3:
        st.text_input("Buscar por nombre o SKU")
        st.info("Funcionalidad de búsqueda")


elif menu == "Inventario":
    st.header("📊 Control de Inventario")
    
    # Tabla de inventario
    inventarios = api_get("/api/v1/inventario")
    productos = api_get("/api/v1/productos")
    
    if inventarios and productos:
        # Combinar datos
        datos_tabla = []
        for inv in inventarios:
            prod = next((p for p in productos if p.get("id") == inv.get("producto_id")), None)
            if prod:
                datos_tabla.append({
                    "Producto": prod.get("nombre"),
                    "Stock": inv.get("cantidad"),
                    "Mínimo": prod.get("stock_minimo"),
                    "Máximo": prod.get("stock_maximo"),
                    "Estado": "BAJO" if inv.get("cantidad", 0) < prod.get("stock_minimo", 0) else "OK",
                    "Ubicación": inv.get("ubicacion", "N/A")
                })
        
        if datos_tabla:
            df = pd.DataFrame(datos_tabla)
            
            st.dataframe(df, use_container_width=True)
            
            # Gráfico de stock
            st.subheader("📈 Distribución de Stock")
            
            fig = px.histogram(
                df, 
                x="Stock",
                color="Estado",
                color_discrete_map={"BAJO": "#FF4B4B", "OK": "#4CAF50"},
                nbins=10,
                title="Histograma de Stock"
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    # Atualizar stock
    st.markdown("---")
    st.subheader("✏️ Actualizar Stock")
    
    with st.form("actualizar_stock"):
        prod_id = st.number_input("Producto ID", min_value=1)
        nueva_cantidad = st.number_input("Nueva Cantidad", min_value=0)
        ubicacion = st.text_input("Ubicación")
        
        submit = st.form_submit_button("Actualizar")
        
        if submit:
            result = api_post(f"/api/v1/inventario/{prod_id}", {
                "cantidad": nueva_cantidad,
                "ubicacion": ubicacion
            })
            if result:
                st.success("✅ Stock actualizado")
            else:
                st.error("❌ Error")


elif menu == "Ventas":
    st.header("💰 Gestión de Ventas")
    
    tab1, tab2 = st.tabs(["Historial", "Registrar Nueva"])
    
    with tab1:
        ventas = api_get("/api/v1/ventas")
        if ventas:
            df = pd.DataFrame(ventas)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay ventas registradas")
    
    with tab2:
        productos = api_get("/api/v1/productos")
        
        if productos:
            with st.form("nueva_venta"):
                prod_options = {f"{p.get('nombre')} (ID: {p.get('id')})": p.get("id") for p in productos}
                producto_sel = st.selectbox("Producto", list(prod_options.keys()))
                producto_id = prod_options.get(producto_sel)
                
                cantidad = st.number_input("Cantidad", min_value=1, value=1)
                
                # Obtener precio del producto
                prod = next((p for p in productos if p.get("id") == producto_id), None)
                precio = prod.get("precio_venta", 0) if prod else 0
                
                st.metric("Precio Unitario", f"€{precio}")
                st.metric("Total", f"€{cantidad * precio}")
                
                submit = st.form_submit_button("Registrar Venta")
            
            if 'submit' in locals() and submit:
                data = {
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                    "precio_unitario": precio
                }
                result = api_post("/api/v1/ventas", data)
                if result:
                    st.success("✅ Venta registrada")
                else:
                    st.error("❌ Error")
        else:
            st.info("Crea productos primero")


elif menu == "Predicciones":
    st.header("🔮 Predicciones de Demanda")
    
    st.info("Basado en historial de ventas")
    
    predicciones = api_get("/api/v1/prediccion/todos")
    
    if predicciones:
        # Preparar datos para gráfico
        datos_grafico = []
        for pred in predicciones:
            datos_grafico.append({
                "Producto": pred.get("producto"),
                "Días Restantes": pred.get("dias_hasta_agotarse"),
                "Estado": pred.get("estado"),
                "Tendencia": pred.get("tendencia")
            })
        
        df = pd.DataFrame(datos_grafico)
        
        # Ordenar por días restantes
        df = df.sort_values("Días Restantes")
        
        # Gráfico de barras horizontal
        fig = px.bar(
            df.head(10),
            y="Producto",
            x="Días Restantes",
            color="Estado",
            color_discrete_map={
                "CRÍTICO": "#FF4B4B",
                "BAJO": "#FFA500",
                "MODERADO": "#FFEB3B",
                "ADECUADO": "#4CAF50"
            },
            orientation="h",
            title="Días hasta agotarse (Top 10)"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de detalles
        st.subheader("📋 Detalles")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Registra ventas para ver predicciones")


elif menu == "Visión Artificial":
    st.header("📸 Detección con YOLOv8")
    
    st.info("Sube una imagen de tu estantería para detectar productos")
    
    archivo = st.file_uploader("Seleccionar imagen", type=["jpg", "png", "jpeg"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if archivo:
            st.image(archivo, caption="Imagen", use_container_width=True)
    
    with col2:
        if archivo:
            st.subheader("Análisis")
            
            # Aquí iría la llamada a la API de visión
            # Por ahora mensaje informativo
            st.warning("Función en desarrollo...")
            st.info("Próximamente: Detección automática de productos")

st.markdown("---")
st.caption("MarkeTTalento v1.0 - Sistema de Inventario Inteligente")