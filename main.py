from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timezone
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config.config import settings
from src.core.database.database import init_db, get_db
from src.dominio.entidades.entidades import Categoria, Proveedor, Producto, Inventario, Venta
from src.dominio.repositorios.repositorios import ProductoRepositorio, InventarioRepositorio, VentaRepositorio
from src.infraestructura.repositorios.repositorios_impl import (
    SQLAlchemyProductoRepositorio,
    SQLAlchemyInventarioRepositorio,
    SQLAlchemyVentaRepositorio,
)
from src.aplicacion.servicios.producto_servicio import ProductoServicio
from src.aplicacion.servicios.inventario_servicio import InventarioServicio
from src.aplicacion.servicios.prediccion_servicio import PrediccionServicio
from src.aplicacion.servicios.vision_servicio import VisionServicio, ResultadoVision
from src.aplicacion.schemas.schemas import (
    CategoriaCreate, CategoriaResponse,
    ProveedorCreate, ProveedorResponse,
    ProductoCreate, ProductoResponse,
    InventarioCreate, InventarioResponse,
    VentaCreate, VentaResponse,
)


app = FastAPI(
    title="MarkeTTalento API",
    description="""
## Sistema de Inventario Inteligente

### Características
- **Gestión de Productos**: CRUD completo de productos, categorías y proveedores
- **Control de Inventario**: Seguimiento de stock en tiempo real con alertas
- **Ventas**: Registro y seguimiento de ventas
- **Predicciones ML**: Predicción de demanda basada en historial
- **Visión Artificial**: Detección de productos con YOLOv8 + actualización automática de inventario

### Autenticación
Por ahora en modo desarrollo (sin autenticación).

### Notas
- Base de datos: SQLite (desarrollo)
- Puerto: 8002
- Dashboard: http://localhost:8501
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_producto_repo() -> ProductoRepositorio:
    return SQLAlchemyProductoRepositorio()


def get_inventario_repo() -> InventarioRepositorio:
    return SQLAlchemyInventarioRepositorio()


def get_venta_repo() -> VentaRepositorio:
    return SQLAlchemyVentaRepositorio()


@app.on_event("startup")
async def startup_event():
    """Inicializa la base de datos al iniciar."""
    try:
        init_db()
        print("[OK] Base de datos inicializada")
    except Exception as e:
        print(f"[WARN] BD no disponible - modo desarrollo: {e}")


@app.get("/")
async def raiz():
    """Página principal."""
    return {
        "mensaje": "MarkeTTalento API",
        "version": "1.0.0",
        "documentacion": "/docs"
    }


@app.get("/api/v1/salud", tags=["Sistema"])
async def salud():
    """Estado de salud del sistema."""
    return {
        "estado": "saludable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "servicios": ["FastAPI", "SQLite", "YOLOv8"]
    }


@app.post("/api/v1/categorias", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED, tags=["Categorías"])
async def crear_categoria(
    categoria: CategoriaCreate,
    db = Depends(get_db)
):
    """Crea una nueva categoría."""
    db_categoria = Categoria(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@app.get("/api/v1/categorias", response_model=List[CategoriaResponse], tags=["Categorías"])
async def listar_categorias(db = Depends(get_db)):
    """Lista todas las categorías."""
    return db.query(Categoria).filter(Categoria.activo == True).all()


@app.post("/api/v1/proveedores", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED, tags=["Proveedores"])
async def crear_proveedor(
    proveedor: ProveedorCreate,
    db = Depends(get_db)
):
    """Crea un nuevo proveedor."""
    db_proveedor = Proveedor(**proveedor.model_dump())
    db.add(db_proveedor)
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor


@app.get("/api/v1/proveedores", response_model=List[ProveedorResponse], tags=["Proveedores"])
async def listar_proveedores(db = Depends(get_db)):
    """Lista todos los proveedores."""
    return db.query(Proveedor).filter(Proveedor.activo == True).all()


@app.post("/api/v1/productos", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED, tags=["Productos"])
async def crear_producto(
    producto: ProductoCreate,
    db = Depends(get_db)
):
    """Crea un nuevo producto con inventario inicial."""
    # Extraer campos de inventario antes de crear el producto
    cantidad_inicial = getattr(producto, 'cantidad_inicial', 0) or 0
    ubicacion = getattr(producto, 'ubicacion', None) or "Almacén A"
    
    # Crear el producto (sin los campos de inventario)
    producto_data = producto.model_dump(exclude={'cantidad_inicial', 'ubicacion'})
    db_producto = Producto(**producto_data)
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    
    # Crear el inventario con la cantidad inicial
    inventario = Inventario(
        producto_id=db_producto.id,
        cantidad=cantidad_inicial,
        ubicacion=ubicacion
    )
    db.add(inventario)
    db.commit()
    
    return db_producto


@app.get("/api/v1/productos", response_model=List[ProductoResponse], tags=["Productos"])
async def listar_productos(
    categoria_id: Optional[int] = None,
    db = Depends(get_db)
):
    """Lista productos."""
    query = db.query(Producto).filter(Producto.activo == True)
    
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    
    return query.all()


@app.get("/api/v1/productos/{producto_id}", response_model=ProductoResponse, tags=["Productos"])
async def obtener_producto(producto_id: int, db = Depends(get_db)):
    """Obtiene un producto por ID."""
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.activo == True
    ).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado"
        )
    
    return producto


@app.get("/api/v1/productos/sku/{sku}", response_model=ProductoResponse, tags=["Productos"])
async def obtener_producto_por_sku(sku: str, db = Depends(get_db)):
    """Obtiene un producto por SKU."""
    producto = db.query(Producto).filter(
        Producto.sku == sku,
        Producto.activo == True
    ).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con SKU {sku} no encontrado"
        )
    
    return producto


@app.put("/api/v1/productos/{producto_id}", response_model=ProductoResponse, tags=["Productos"])
async def actualizar_producto(
    producto_id: int,
    producto_data: ProductoCreate,
    db = Depends(get_db)
):
    """Actualiza un producto."""
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado"
        )
    
    for key, value in producto_data.model_dump().items():
        setattr(db_producto, key, value)
    
    db.commit()
    db.refresh(db_producto)
    return db_producto


@app.delete("/api/v1/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Productos"])
async def eliminar_producto(producto_id: int, db = Depends(get_db)):
    """Elimina (soft delete) un producto."""
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado"
        )
    
    db_producto.activo = False
    db.commit()
    return None


@app.post("/api/v1/inventario/{producto_id}", response_model=InventarioResponse, tags=["Inventario"])
async def actualizar_inventario(
    producto_id: int,
    inventario_data: InventarioCreate,
    db = Depends(get_db)
):
    """Actualiza el inventario de un producto."""
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrar do"
        )
    
    inventario = db.query(Inventario).filter(Inventario.producto_id == producto_id).first()
    
    if inventario:
        inventario.cantidad = inventario_data.cantidad
        inventario.ubicacion = inventario_data.ubicacion
        inventario.fecha_ultima_actualizacion = datetime.now(timezone.utc)
    else:
        inventario = Inventario(
            producto_id=producto_id,
            cantidad=inventario_data.cantidad,
            ubicacion=inventario_data.ubicacion
        )
        db.add(inventario)
    
    db.commit()
    db.refresh(inventario)
    return inventario


@app.get("/api/v1/inventario", response_model=List[InventarioResponse], tags=["Inventario"])
async def listar_inventario(db = Depends(get_db)):
    """Lista todo el inventario."""
    return db.query(Inventario).all()


@app.get("/api/v1/inventario/bajo-stock", response_model=List[InventarioResponse], tags=["Inventario"])
async def productos_bajo_stock(
    limite: int = 10,
    db = Depends(get_db)
):
    """Lista productos con stock bajo."""
    inventarios = db.query(Inventario).all()
    resultados = []
    
    for inv in inventarios:
        producto = db.query(Producto).filter(Producto.id == inv.producto_id).first()
        if producto and inv.cantidad < producto.stock_minimo:
            resultados.append(inv)
    
    return resultados[:limite]


@app.get("/api/v1/inventario/resumen", tags=["Inventario"])
async def resumen_inventario(db = Depends(get_db)):
    """Obtiene resumen completo del inventario."""
    try:
        from src.dominio.entidades.entidades import Producto, Inventario
        
        productos = db.query(Producto).filter(Producto.activo == True).all()
        inventarios = db.query(Inventario).all()
        
        total_productos = len(productos)
        total_unidades = sum(i.cantidad for i in inventarios)
        productos_criticos = 0
        productos_bajos = 0
        productos_adecuados = 0
        valor_total = 0.0
        
        for inv in inventarios:
            prod = next((p for p in productos if p.id == inv.producto_id), None)
            if prod:
                if inv.cantidad < prod.stock_minimo:
                    if inv.cantidad <= prod.stock_minimo * 0.3:
                        productos_criticos += 1
                    else:
                        productos_bajos += 1
                else:
                    productos_adecuados += 1
                valor_total += inv.cantidad * prod.precio_venta
        
        return {
            "total_productos": total_productos,
            "total_unidades": total_unidades,
            "productos_criticos": productos_criticos,
            "productos_bajos": productos_bajos,
            "productos_adecuados": productos_adecuados,
            "valor_total": round(valor_total, 2),
            "recomendaciones": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/inventario/recomendaciones", tags=["Inventario"])
async def recomendaciones(
    producto_repo: ProductoRepositorio = Depends(get_producto_repo),
    inventario_repo: InventarioRepositorio = Depends(get_inventario_repo),
    venta_repo: VentaRepositorio = Depends(get_venta_repo)
):
    """Genera recomendaciones de reposición."""
    servicio = InventarioServicio(inventario_repo, venta_repo)
    return servicio.generar_recomendaciones()


@app.post("/api/v1/ventas", response_model=VentaResponse, status_code=status.HTTP_201_CREATED, tags=["Ventas"])
async def registrar_venta(
    venta: VentaCreate,
    db = Depends(get_db)
):
    """Registra una venta."""
    producto = db.query(Producto).filter(Producto.id == venta.producto_id).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {venta.producto_id} no encontrado"
        )
    
    db_venta = Venta(
        producto_id=venta.producto_id,
        cantidad=venta.cantidad,
        precio_unitario=venta.precio_unitario,
       tipo_operacion=venta.tipo_operacion,
        fecha=datetime.now(timezone.utc)
    )
    db.add(db_venta)
    
    # Actualizar inventario
    inventario = db.query(Inventario).filter(Inventario.producto_id == venta.producto_id).first()
    if inventario:
        if venta.tipo_operacion == "venta":
            inventario.cantidad -= venta.cantidad
        else:
            inventario.cantidad += venta.cantidad
        inventario.fecha_ultima_actualizacion = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_venta)
    return db_venta


@app.get("/api/v1/ventas", response_model=List[VentaResponse], tags=["Ventas"])
async def listar_ventas(
    limite: int = 100,
    db = Depends(get_db)
):
    """Lista últimas ventas."""
    return db.query(Venta).order_by(Venta.fecha.desc()).limit(limite).all()


@app.get("/api/v1/ventas/producto/{producto_id}", response_model=List[VentaResponse], tags=["Ventas"])
async def ventas_por_producto(
    producto_id: int,
    limite: int = 30,
    db = Depends(get_db)
):
    """Obtiene historial de ventas de un producto."""
    return db.query(Venta).filter(
        Venta.producto_id == producto_id
    ).order_by(Venta.fecha.desc()).limit(limite).all()


@app.get("/api/v1/predicccion/{producto_id}", tags=["Predicciones"])
async def predecir_demanda(
    producto_id: int,
    venta_repo: VentaRepositorio = Depends(get_venta_repo)
):
    """Predice la demanda para un producto."""
    servicio = PrediccionServicio(venta_repo)
    prediccion = servicio.predecir_demanda(producto_id)
    
    return {
        "producto": prediccion.producto_nombre,
        "dias_hasta_agotarse": round(prediccion.dias_hasta_agotarse, 1),
        "consumo_promedio_diario": round(prediccion.consumo_promedio, 2),
        "tendencia": prediccion.tendencia,
        "estado": prediccion.estado,
        "historial": prediccion.datos_grafico
    }


@app.get("/api/v1/prediccion/todos", tags=["Predicciones"])
async def predecir_todos(
    venta_repo: VentaRepositorio = Depends(get_venta_repo)
):
    """Predice demanda para todos los productos."""
    servicio = PrediccionServicio(venta_repo)
    predicciones = servicio.predecir_todos()
    
    return [
        {
            "producto": p.producto_nombre,
            "dias_hasta_agotarse": round(p.dias_hasta_agotarse, 1),
            "consumo_promedio_diario": round(p.consumo_promedio, 2),
            "tendencia": p.tendencia,
            "estado": p.estado
        }
        for p in predicciones
    ]


@app.get("/api/v1/prediccion/semanal/{producto_id}", tags=["Predicciones"])
async def pronostico_semanal(
    producto_id: int,
    venta_repo: VentaRepositorio = Depends(get_venta_repo)
):
    """Genera pronóstico semanal."""
    servicio = PrediccionServicio(venta_repo)
    return servicio.generar_pronostico_semanal(producto_id)


@app.post("/api/v1/vision/detectar", tags=["Visión Artificial"])
async def detectar_en_imagen(
    archivo: UploadFile = File(...),
    confianza_min: float = 0.15
):
    """Detecta productos en una imagen."""
    # Guardar archivo temporalmente
    timestamp = datetime.now(timezone.utc).timestamp()
    ruta_temporal = f"temp_{timestamp}_{archivo.filename}"
    
    try:
        with open(ruta_temporal, "wb") as f:
            contenido = await archivo.read()
            f.write(contenido)
        
        # Detectar
        vision = VisionServicio()
        resultado = vision.detectar_en_imagen(ruta_temporal, confianza_min)
        
        return resultado.to_dict()
    
    finally:
        # Limpiar archivo temporal
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@app.post("/api/v1/vision/analizar-y-actualizar", tags=["Visión Artificial"])
async def detectar_y_actualizar_inventario(
    archivo: UploadFile = File(...),
    confianza_min: float = 0.15,
    actualizar_stock: bool = True
):
    """
    Detecta productos en imagen y opcionalmente actualiza el inventario.
    """
    from src.aplicacion.servicios.inventario_vision import MapeoProducto, actualizar_inventario_desde_deteccion
    
    # Guardar archivo temporalmente
    timestamp = datetime.now(timezone.utc).timestamp()
    ruta_temporal = f"temp_{timestamp}_{archivo.filename}"
    
    try:
        with open(ruta_temporal, "wb") as f:
            contenido = await archivo.read()
            f.write(contenido)
        
        # 1. Detectar objetos en la imagen
        vision = VisionServicio()
        resultado_vision = vision.detectar_en_imagen(ruta_temporal, confianza_min)
        
        # Obtener objetos detectados como lista de diccionarios
        objetos_detectados = []
        for det in resultado_vision.productos_detectados:
            objetos_detectados.append({
                "nombre": det.nombre,
                "confianza": det.confianza,
                "cantidad": det.cantidad
            })
        
        # 2. Mapear objetos a productos de la BD
        mapeo = MapeoProducto.mapear_todos(objetos_detectados)
        
        resultado = {
            "deteccion": {
                "total_objetos": resultado_vision.total_productos,
                "objetos": objetos_detectados
            },
            "mapeo": mapeo
        }
        
        # 3. Actualizar inventario si se solicita
        if actualizar_stock and mapeo["mapeados"]:
            resultado["actualizacion"] = actualizar_inventario_desde_deteccion(mapeo)
        
        return resultado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@app.get("/api/v1/analisis/completo", tags=["Análisis"])
async def analisis_completo(
    producto_repo: ProductoRepositorio = Depends(get_producto_repo),
    inventario_repo: InventarioRepositorio = Depends(get_inventario_repo),
    venta_repo: VentaRepositorio = Depends(get_venta_repo)
):
    """Análisis completo del inventario con predicciones."""
    inv_servicio = InventarioServicio(inventario_repo, venta_repo)
    pred_servicio = PrediccionServicio(venta_repo)
    
    resumen = inv_servicio.obtener_resumen()
    predicciones = pred_servicio.predecir_todos()
    
    return {
        "resumen_inventario": resumen,
        "predicciones": [
            {
                "producto": p.producto_nombre,
                "dias_hasta_agotarse": round(p.dias_hasta_agotarse, 1),
                "estado": p.estado
            }
            for p in predicciones
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)