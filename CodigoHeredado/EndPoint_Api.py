# ============================================================
# codigoInicio.py - SISTEMA DE INVENTARIO INTELIGENTE
# Versión unificada con DASHBOARD DE ENDPOINTS
# ============================================================

import random
import statistics
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# ============================================================
# BASE DE DATOS SIMULADA
# ============================================================

product_database = {
    "Leche": {
        "id": "PROD001", "nombre": "Leche", "categoria": "Lácteos",
        "precio": 1.20, "unidad": "litro", "stock_minimo": 5,
        "stock_maximo": 30, "tiempo_reposicion": 2,
        "historial_ventas": [3, 4, 5, 2, 6, 4, 5, 3, 4, 6, 5, 4, 3, 5, 4, 6, 3, 5, 4, 5]
    },
    "Huevos": {
        "id": "PROD002", "nombre": "Huevos", "categoria": "Huevos",
        "precio": 2.50, "unidad": "docena", "stock_minimo": 3,
        "stock_maximo": 20, "tiempo_reposicion": 1,
        "historial_ventas": [2, 3, 2, 4, 3, 2, 3, 4, 2, 3, 4, 2, 3, 2, 4, 3, 2, 3, 2, 4]
    },
    "Pan": {
        "id": "PROD003", "nombre": "Pan", "categoria": "Panadería",
        "precio": 0.90, "unidad": "unidad", "stock_minimo": 10,
        "stock_maximo": 50, "tiempo_reposicion": 1,
        "historial_ventas": [8, 10, 9, 7, 11, 8, 10, 9, 8, 12, 10, 9, 8, 11, 9, 10, 8, 9, 10, 11]
    },
    "Agua": {
        "id": "PROD004", "nombre": "Agua", "categoria": "Bebidas",
        "precio": 0.60, "unidad": "botella", "stock_minimo": 15,
        "stock_maximo": 100, "tiempo_reposicion": 3,
        "historial_ventas": [10, 12, 11, 9, 13, 10, 12, 11, 10, 14, 12, 11, 10, 13, 11, 12, 10, 11, 12, 13]
    },
    "Café": {
        "id": "PROD005", "nombre": "Café", "categoria": "Bebidas",
        "precio": 4.50, "unidad": "paquete", "stock_minimo": 3,
        "stock_maximo": 25, "tiempo_reposicion": 5,
        "historial_ventas": [1, 2, 1, 3, 2, 1, 2, 3, 1, 2, 3, 1, 2, 1, 3, 2, 1, 2, 1, 3]
    },
    "Arroz": {
        "id": "PROD006", "nombre": "Arroz", "categoria": "Alimentos básicos",
        "precio": 1.80, "unidad": "kg", "stock_minimo": 10,
        "stock_maximo": 60, "tiempo_reposicion": 4,
        "historial_ventas": [3, 4, 3, 5, 4, 3, 4, 5, 3, 4, 5, 3, 4, 3, 5, 4, 3, 4, 3, 5]
    },
        "Aceite": {
        "id": "PROD007",
        "nombre": "Aceite",
        "categoria": "Aceites",
        "precio": 4.20,
        "unidad": "litro",
        "stock_minimo": 8,
        "stock_maximo": 40,
        "tiempo_reposicion": 4,
        "historial_ventas": [2, 3, 2, 4, 3, 2, 3, 2, 4, 3, 2, 3, 2, 4, 3, 2, 3, 4, 2, 3]
    },
    "Azúcar": {
        "id": "PROD008",
        "nombre": "Azúcar",
        "categoria": "Alimentos básicos",
        "precio": 1.50,
        "unidad": "kg",
        "stock_minimo": 10,
        "stock_maximo": 50,
        "tiempo_reposicion": 3,
        "historial_ventas": [4, 5, 4, 6, 5, 4, 5, 6, 4, 5, 6, 4, 5, 4, 6, 5, 4, 5, 4, 6]
    },
    "Harina": {
        "id": "PROD009",
        "nombre": "Harina",
        "categoria": "Alimentos básicos",
        "precio": 1.20,
        "unidad": "kg",
        "stock_minimo": 10,
        "stock_maximo": 60,
        "tiempo_reposicion": 3,
        "historial_ventas": [3, 4, 3, 5, 4, 3, 4, 5, 3, 4, 5, 3, 4, 3, 5, 4, 3, 4, 3, 5]
    },
    "Galletas": {
        "id": "PROD010",
        "nombre": "Galletas",
        "categoria": "Snacks",
        "precio": 2.30,
        "unidad": "paquete",
        "stock_minimo": 12,
        "stock_maximo": 45,
        "tiempo_reposicion": 2,
        "historial_ventas": [5, 6, 5, 7, 6, 5, 6, 7, 5, 6, 7, 5, 6, 5, 7, 6, 5, 6, 5, 7]
    },
    "Cereal": {
        "id": "PROD011",
        "nombre": "Cereal",
        "categoria": "Desayuno",
        "precio": 3.80,
        "unidad": "caja",
        "stock_minimo": 6,
        "stock_maximo": 30,
        "tiempo_reposicion": 5,
        "historial_ventas": [2, 3, 2, 4, 3, 2, 3, 4, 2, 3, 4, 2, 3, 2, 4, 3, 2, 3, 2, 4]
    }
}

def get_product_info(product_name):
    return product_database.get(product_name, None)

def get_sales_history(product_name, days=20):
    product = get_product_info(product_name)
    if product:
        return product["historial_ventas"][-days:] if days > 0 else product["historial_ventas"]
    return []

def get_all_products():
    return list(product_database.values())

# ============================================================
# SERVICIO DE VISIÓN ARTIFICIAL (simulado)
# ============================================================

def detect_products(image_path=None):
    print("📸 Analizando imagen para detección de productos...")
    escenarios = [
        {"descripcion": "Estantería de supermercado - Stock moderado", "productos": [
            {"nombre": "Leche", "cantidad": 8, "confianza": 0.92},
            {"nombre": "Huevos", "cantidad": 5, "confianza": 0.88},
            {"nombre": "Pan", "cantidad": 3, "confianza": 0.85},
            {"nombre": "Agua", "cantidad": 12, "confianza": 0.95},
            {"nombre": "Café", "cantidad": 6, "confianza": 0.90}
        ]},
        {"descripcion": "Almacén de tienda - Stock alto", "productos": [
            {"nombre": "Arroz", "cantidad": 25, "confianza": 0.94},
            {"nombre": "Leche", "cantidad": 18, "confianza": 0.91},
            {"nombre": "Huevos", "cantidad": 22, "confianza": 0.89},
            {"nombre": "Agua", "cantidad": 30, "confianza": 0.96},
            {"nombre": "Café", "cantidad": 15, "confianza": 0.87}
        ]},
        {"descripcion": "Nevera comercial - Stock bajo", "productos": [
            {"nombre": "Yogur", "cantidad": 4, "confianza": 0.83},
            {"nombre": "Queso", "cantidad": 2, "confianza": 0.80},
            {"nombre": "Mantequilla", "cantidad": 3, "confianza": 0.82},
            {"nombre": "Zumo", "cantidad": 5, "confianza": 0.86},
            {"nombre": "Fiambre", "cantidad": 1, "confianza": 0.78}
        ]}
    ]
    escenario = random.choice(escenarios)
    print(f"✅ Detección simulada: {escenario['descripcion']}")
    return escenario

# ============================================================
# SERVICIO DE INVENTARIO
# ============================================================

def calculate_inventory_metrics(detected_products, product_database):
    total_products = len(detected_products)
    total_units = sum(p["cantidad"] for p in detected_products)
    
    critical_products = []
    low_stock_products = []
    adequate_products = []
    
    for detected in detected_products:
        product_name = detected["nombre"]
        current_stock = detected["cantidad"]
        product_info = product_database.get(product_name)
        
        if product_info:
            min_stock = product_info.get("stock_minimo", 5)
            if current_stock == 0:
                critical_products.append({"producto": product_name, "stock_actual": current_stock, "stock_minimo": min_stock, "estado": "AGOTADO ❌"})
            elif current_stock < min_stock:
                low_stock_products.append({"producto": product_name, "stock_actual": current_stock, "stock_minimo": min_stock, "estado": "BAJO ⚠️"})
            else:
                adequate_products.append({"producto": product_name, "stock_actual": current_stock, "stock_minimo": min_stock, "estado": "ADEQUADO ✅"})
    
    return {
        "resumen": {
            "total_productos": total_products,
            "total_unidades": total_units,
            "productos_criticos": len(critical_products),
            "productos_bajos": len(low_stock_products),
            "productos_adecuados": len(adequate_products),
        },
        "recomendaciones": generate_recommendations(critical_products + low_stock_products)
    }

def generate_recommendations(products_needing_attention):
    recommendations = []
    for product in products_needing_attention:
        producto = product["producto"]
        stock_actual = product["stock_actual"]
        stock_minimo = product.get("stock_minimo", 5)
        if stock_actual == 0:
            rec = f"🔄 Reponer urgentemente {producto}. Stock agotado."
        else:
            rec = f"📦 Reponer {stock_minimo * 2 - stock_actual} unidades de {producto}. Stock bajo."
        recommendations.append({"producto": producto, "recomendacion": rec, "prioridad": "ALTA" if stock_actual == 0 else "MEDIA"})
    return recommendations

def calculate_inventory_value(detected_products, product_database):
    total_value = 0
    for detected in detected_products:
        product_info = product_database.get(detected["nombre"])
        if product_info and "precio" in product_info:
            total_value += detected["cantidad"] * product_info["precio"]
    return round(total_value, 2)

# ============================================================
# SERVICIO DE PREDICCIÓN
# ============================================================

def predict_stock_outage(sales_history, current_stock, product_info=None):
    if not sales_history or current_stock <= 0:
        return {"dias_hasta_agotarse": 0, "cantidad_recomendada": 10, "estado": "AGOTADO" if current_stock <= 0 else "SIN HISTORIAL"}
    
    avg_daily_sales = sum(sales_history) / len(sales_history)
    if len(sales_history) >= 5:
        recent_avg = sum(sales_history[-5:]) / 5
        trend_factor = recent_avg / avg_daily_sales if avg_daily_sales > 0 else 1
        adjusted_daily = avg_daily_sales * trend_factor
    else:
        adjusted_daily = avg_daily_sales
    
    days_until_out = max(0, min(90, round(current_stock / adjusted_daily, 1))) if adjusted_daily > 0 else 999
    
    if days_until_out <= 2:
        estado = "CRÍTICO ⚠️"
    elif days_until_out <= 5:
        estado = "BAJO ⚠️"
    elif days_until_out <= 10:
        estado = "MODERADO ℹ️"
    else:
        estado = "ADEQUADO ✅"
    
    return {
        "dias_hasta_agotarse": days_until_out,
        "cantidad_recomendada": round(avg_daily_sales * 10),
        "estado": estado,
        "consumo_promedio_diario": round(adjusted_daily, 2)
    }

# ============================================================
# TEMPLATE HTML CON BOTONES PARA CADA ENDPOINT
# ============================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Inventario Inteligente</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .card { border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 20px; border: none; }
        .card-header { background: linear-gradient(45deg, #667eea, #764ba2); color: white; border-radius: 15px 15px 0 0 !important; }
        .btn-api { margin: 5px; border-radius: 20px; }
        .endpoint-url { font-family: monospace; font-size: 0.8em; color: #666; }
        .response-area { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 10px; font-family: monospace; font-size: 12px; overflow-x: auto; max-height: 400px; }
        .stat-card { text-align: center; padding: 20px; border-radius: 10px; color: white; }
        .loading { display: none; text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="text-center mb-4">
            <h1 class="text-white">📦 Sistema de Inventario Inteligente</h1>
            <p class="text-white-50">Análisis con Visión Artificial y Predicción de Demanda</p>
        </div>
        
        <div class="row">
            <!-- Panel izquierdo: Botones de API -->
            <div class="col-md-4 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">🔌 Endpoints de la API</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <button class="btn btn-primary btn-api" onclick="callAPI('/api/test')">
                                <i class="fas fa-vial"></i> GET /api/test
                            </button>
                            <button class="btn btn-success btn-api" onclick="callAPI('/api/analizar-inventario')">
                                <i class="fas fa-chart-line"></i> GET /api/analizar-inventario
                            </button>
                            <button class="btn btn-info btn-api" onclick="callAPI('/api/productos')">
                                <i class="fas fa-boxes"></i> GET /api/productos
                            </button>
                            <button class="btn btn-warning btn-api" onclick="callAPI('/api/producto/Leche')">
                                <i class="fas fa-box"></i> GET /api/producto/Leche
                            </button>
                            <button class="btn btn-secondary btn-api" onclick="callAPI('/api/recomendaciones')">
                                <i class="fas fa-lightbulb"></i> GET /api/recomendaciones
                            </button>
                        </div>
                        <hr>
                        <div class="d-grid gap-2">
                            <button class="btn btn-outline-primary" onclick="location.href='/'">
                                <i class="fas fa-home"></i> Inicio
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Tarjeta de información del sistema -->
                <div class="card mt-3">
                    <div class="card-header">
                        <h5 class="mb-0">ℹ️ Información del Sistema</h5>
                    </div>
                    <div class="card-body">
                        <p><i class="fas fa-camera"></i> <strong>Visión Artificial:</strong> Detecta productos en imágenes (simulado)</p>
                        <p><i class="fas fa-chart-line"></i> <strong>Predicción:</strong> Estima fecha de agotamiento</p>
                        <p><i class="fas fa-lightbulb"></i> <strong>Recomendación:</strong> Sugiere cantidades de reposición</p>
                        <hr>
                        <p><strong>Flujo del Sistema:</strong></p>
                        <ol class="small">
                            <li>Captura de imagen</li>
                            <li>Detección de productos</li>
                            <li>Análisis de stock</li>
                            <li>Predicción de demanda</li>
                            <li>Recomendaciones</li>
                            <li>Dashboard interactivo</li>
                        </ol>
                    </div>
                </div>
            </div>
            
            <!-- Panel derecho: Resultados -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">📊 Respuesta de la API</h5>
                    </div>
                    <div class="card-body">
                        <div id="loading" class="loading">
                            <div class="spinner-border text-primary"></div>
                            <p class="mt-2">Consultando API...</p>
                        </div>
                        <div id="response" class="response-area">
                            <i class="fas fa-info-circle"></i> Haz clic en cualquier botón para probar un endpoint
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function callAPI(url) {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando...';
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('response').innerHTML = 
                        '<div class="mb-2"><strong>📡 Endpoint:</strong> ' + url + '</div>' +
                        '<div class="mb-2"><strong>✅ Status:</strong> ' + (data.status || 'success') + '</div>' +
                        '<hr>' +
                        '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                })
                .catch(error => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('response').innerHTML = 
                        '<div class="alert alert-danger">❌ Error: ' + error + '</div>';
                });
        }
        
        // Función para analizar inventario y mostrar en formato amigable
        function analizarInventario() {
            callAPI('/api/analizar-inventario');
        }
        
        function verProductos() {
            callAPI('/api/productos');
        }
    </script>
</body>
</html>
'''

# ============================================================
# RUTAS DE LA APLICACIÓN
# ============================================================

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/test')
def test_api():
    return jsonify({
        "status": "success",
        "message": "✅ API de Inventario Inteligente funcionando",
        "version": "3.0",
        "timestamp": datetime.now().isoformat(),
        "servicios": ["vision", "database", "prediction", "inventory"]
    })

@app.route('/api/analizar-inventario')
def analizar_inventario():
    print("\n🔄 INICIANDO ANÁLISIS DE INVENTARIO")
    deteccion = detect_products()
    productos_detectados = deteccion.get("productos", [])
    
    productos_analizados = []
    for producto_detectado in productos_detectados:
        nombre = producto_detectado["nombre"]
        stock_actual = producto_detectado["cantidad"]
        producto_info = get_product_info(nombre)
        
        if producto_info:
            historial_ventas = get_sales_history(nombre, days=30)
            prediccion = predict_stock_outage(historial_ventas, stock_actual, producto_info)
            productos_analizados.append({
                "producto": nombre,
                "stock_actual": stock_actual,
                "informacion": {"categoria": producto_info.get("categoria"), "precio": producto_info.get("precio")},
                "prediccion": prediccion
            })
        else:
            productos_analizados.append({
                "producto": nombre,
                "stock_actual": stock_actual,
                "informacion": None,
                "prediccion": {"dias_hasta_agotarse": "N/A", "estado": "NO ENCONTRADO EN BD"}
            })
    
    analisis = calculate_inventory_metrics(productos_detectados, product_database)
    valor_inventario = calculate_inventory_value(productos_detectados, product_database)
    
    return jsonify({
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "deteccion": deteccion,
        "productos": productos_analizados,
        "analisis": analisis,
        "valor_inventario": valor_inventario,
        "resumen": {
            "total_productos": len(productos_analizados),
            "productos_criticos": analisis["resumen"]["productos_criticos"],
            "valor_total": valor_inventario
        }
    })

@app.route('/api/productos')
def obtener_productos():
    return jsonify({"status": "success", "total": len(get_all_products()), "productos": get_all_products()})

@app.route('/api/producto/<nombre>')
def obtener_producto(nombre):
    producto = get_product_info(nombre)
    if producto:
        return jsonify({"status": "success", "producto": producto})
    else:
        return jsonify({"status": "error", "message": f"Producto '{nombre}' no encontrado"}), 404

@app.route('/api/recomendaciones')
def obtener_recomendaciones():
    productos = get_all_products()
    recomendaciones = []
    for producto in productos[:5]:
        recomendaciones.append({
            "producto": producto["nombre"],
            "accion": "REVISAR STOCK",
            "prioridad": "MEDIA",
            "motivo": f"Producto con historial de {len(producto['historial_ventas'])} días"
        })
    return jsonify({"status": "success", "recomendaciones": recomendaciones, "total": len(recomendaciones)})

# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("📦 SISTEMA DE INVENTARIO INTELIGENTE - VERSIÓN UNIFICADA")
    print("=" * 60)
    print("📌 Endpoints disponibles:")
    print("   GET /api/test")
    print("   GET /api/analizar-inventario")
    print("   GET /api/productos")
    print("   GET /api/producto/<nombre>")
    print("   GET /api/recomendaciones")
    print("=" * 60)
    print("🌐 Abre en tu navegador: http://localhost:5002")
    print("📝 Presiona Ctrl+C para detener")
    print("=" * 60)
    app.run(debug=True, port=5002, host='0.0.0.0', threaded=True)