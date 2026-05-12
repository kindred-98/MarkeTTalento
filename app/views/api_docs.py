"""
API Docs - Documentación de referencia del sistema
Se muestra como un apartado del sidebar
"""
import streamlit as st
import os

ENDPOINTS = [
    {
        "method": "POST",
        "path": "/api/v1/auth/login",
        "desc": "Autenticación de usuario",
        "params": {"username": "string", "password": "string"},
        "response": '{"access_token": "jwt...", "token_type": "bearer", "usuario": {...}}'
    },
    {
        "method": "GET",
        "path": "/api/v1/productos",
        "desc": "Listar todos los productos activos",
        "response": '[{"id": 1, "sku": "PROD-001", "nombre": "...", ...}]'
    },
    {
        "method": "POST",
        "path": "/api/v1/productos",
        "desc": "Crear nuevo producto",
        "params": {"sku": "string", "nombre": "string", "precio_venta": "float", "categoria_id": "int"},
        "response": '{"id": 1, "sku": "PROD-001", ...}'
    },
    {
        "method": "PUT",
        "path": "/api/v1/productos/{id}",
        "desc": "Actualizar producto existente",
        "params": {"nombre": "string", "precio_venta": "float"},
        "response": '{"id": 1, "mensaje": "Producto actualizado"}'
    },
    {
        "method": "DELETE",
        "path": "/api/v1/productos/{id}",
        "desc": "Eliminar producto (soft delete)",
        "response": "true"
    },
    {
        "method": "GET",
        "path": "/api/v1/categorias",
        "desc": "Listar categorías activas",
        "response": '[{"id": 1, "nombre": "Bebidas", ...}]'
    },
    {
        "method": "POST",
        "path": "/api/v1/categorias",
        "desc": "Crear nueva categoría",
        "params": {"nombre": "string", "descripcion": "string"},
        "response": '{"id": 1, "nombre": "Bebidas", ...}'
    },
    {
        "method": "GET",
        "path": "/api/v1/proveedores",
        "desc": "Listar proveedores activos",
        "response": '[{"id": 1, "nombre": "Proveedor A", ...}]'
    },
    {
        "method": "POST",
        "path": "/api/v1/proveedores",
        "desc": "Crear nuevo proveedor",
        "params": {"nombre": "string", "email": "string", "telefono": "string"},
        "response": '{"id": 1, "nombre": "Proveedor A"}'
    },
    {
        "method": "GET",
        "path": "/api/v1/inventario",
        "desc": "Listar inventario con datos de productos",
        "response": '[{"producto_id": 1, "stock": 50, "max_s": 100, ...}]'
    },
    {
        "method": "GET",
        "path": "/api/v1/inventario/resumen",
        "desc": "Resumen del inventario (total productos, unidades, valor)",
        "response": '{"total_productos": 10, "total_unidades": 500, "valor_total": 15000}'
    },
    {
        "method": "POST",
        "path": "/api/v1/tickets",
        "desc": "Crear ticket de venta (TPV)",
        "params": {"cajero": "string", "metodo_pago": "string", "lineas": [{"producto_id": 1, "cantidad": 1}]},
        "response": '{"id": 1, "numero_ticket": "TKT-000001", "total": 25.50, ...}'
    },
    {
        "method": "GET",
        "path": "/api/v1/tickets",
        "desc": "Listar tickets (historial de ventas)",
        "response": '[{"numero_ticket": "TKT-000001", "cajero": "admin", "total": 25.50, ...}]'
    },
    {
        "method": "GET",
        "path": "/api/v1/tickets/estadisticas/resumen",
        "desc": "Estadísticas resumen de ventas",
        "response": '{"total_tickets": 50, "total_ingresos": 1250.00, ...}'
    },
    {
        "method": "GET",
        "path": "/api/v1/prediccion/dashboard",
        "desc": "Dashboard de predicciones ML",
        "response": '{"alertas": [], "predicciones": {...}}'
    },
    {
        "method": "GET",
        "path": "/api/v1/salud",
        "desc": "Health check del sistema",
        "response": '{"estado": "saludable", "servicios": ["FastAPI", "SQLite"]}'
    }
]


def render():
    st.markdown("<h2>📚 API Docs</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b;'>Documentación de referencia de los endpoints del sistema</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <style>
    .api-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .api-card:hover {
        border-color: rgba(0, 240, 255, 0.3);
        background: rgba(30, 41, 59, 0.7);
    }
    .api-method {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        font-family: monospace;
        text-transform: uppercase;
    }
    .method-GET { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .method-POST { background: rgba(0, 240, 255, 0.15); color: #00f0ff; border: 1px solid rgba(0, 240, 255, 0.3); }
    .method-PUT { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    .method-DELETE { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .api-path {
        font-family: monospace;
        font-size: 0.9rem;
        color: #e2e8f0;
        margin-left: 10px;
    }
    .api-desc {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 6px;
    }
    .api-code {
        background: rgba(0,0,0,0.3);
        padding: 6px 10px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.75rem;
        color: #a5b4fc;
        margin-top: 6px;
        overflow-x: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    col_filtro, _ = st.columns([2, 3])
    with col_filtro:
        filtro = st.text_input("🔍 Buscar endpoint", placeholder="Nombre o ruta...", label_visibility="collapsed")

    endpoints_filtrados = ENDPOINTS
    if filtro:
        f = filtro.lower()
        endpoints_filtrados = [e for e in ENDPOINTS if f in e["path"].lower() or f in e["desc"].lower()]

    for ep in endpoints_filtrados:
        method = ep["method"]
        method_class = f"method-{method}"

        st.markdown(f"""
        <div class="api-card">
            <div style="display: flex; align-items: center;">
                <span class="api-method {method_class}">{method}</span>
                <span class="api-path">{ep["path"]}</span>
            </div>
            <div class="api-desc">{ep["desc"]}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📄 Detalles", expanded=False):
            if ep.get("params"):
                st.markdown("**Parámetros:**")
                for k, v in ep["params"].items():
                    st.markdown(f"- `{k}`: {v}")
            if ep.get("response"):
                st.markdown("**Respuesta:**")
                st.code(ep["response"], language="json")

    st.markdown("---")
    st.markdown("<p style='color: #64748b; font-size: 0.85rem; text-align: center;'>📌 Todos los endpoints requieren autenticación JWT excepto /salud y /auth/login</p>", unsafe_allow_html=True)