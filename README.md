# MarkeTTalento - Inventario Inteligente

Sistema de gestión de inventario con **Dashboard Streamlit** + **FastAPI**.

---

## 🏗️ Arquitectura de Producción

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Cloud                        │
│              https://tu-app.streamlit.io                │
│                      Frontend                            │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP (requests)
                      │ Puerto 8501
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    Render Free                          │
│              https://markettalento-api.onrender.com     │
│                    Backend FastAPI                      │
│                       Puerto 8002                       │
└─────────────────────┬───────────────────────────────────┘
                      │ SQLAlchemy
                      ▼
┌─────────────────────────────────────────────────────────┐
│                  PostgreSQL (Render)                    │
│              markettalento-db onrender.com              │
│                        Puerto 5432                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Despliegue Paso a Paso

### 1. Crear cuenta en servicios necesarios

- **Render**: https://render.com (Free tier)
- **Streamlit Cloud**: https://streamlit.io/cloud (Free)

### 2. Desplegar API en Render

1. **Fork o sube** este repo a GitHub

2. **Crear PostgreSQL** en Render:
   - Ve a Dashboard → New → PostgreSQL
   - Nombre: `markettalento-db`
   - Plan: Free tier
   - Region: Frankfurt (o la más cercana)

3. **Desplegar API**:
   - Dashboard → New → Web Service
   - Conecta tu repo de GitHub
   - Configura:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `sh -c "python scripts/init_db.py && uvicorn src.api:app --host 0.0.0.0 --port 8002"`
   - **Environment**: Docker (o Python)
   - **Variables de Entorno**:
     - `DATABASE_URL`: PostgreSQL connection string (del paso anterior)
     - `API_HOST`: `0.0.0.0`
     - `API_PORT`: `8002`
     - `CORS_ORIGINS`: `*`
     - `LOG_LEVEL`: `INFO`
   - **Health Check**: `/api/v1/salud`

4. **Esperar despliegue** (2-3 minutos)
   - Anotar URL: `https://markettalento-api.onrender.com`

### 3. Desplegar Dashboard en Streamlit Cloud

1. **Ve a** https://streamlit.io/cloud → New App

2. **Configura**:
   - **Repository**: Tu repo de GitHub
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - **Python version**: `3.11`

3. **Secrets** (en Streamlit Cloud Settings):
   ```
   API_URL = https://markettalento-api.onrender.com
   ```

4. **Deploy!** (1-2 minutos)

---

## 🔐 Autenticación

**Usuario por defecto:**
- Username: `admin`
- Contraseña: `admin123`

---

## 📊 Features

| Feature | Estado |
|---------|--------|
| Dashboard | ✅ |
| Gestión Productos | ✅ |
| Control Inventario | ✅ |
| TPV Ventas | ✅ |
| Predicciones ML | ✅ |
| Inspector Código Barras | ✅ |

---

## 🗄️ Base de Datos

- **Modo Desarrollo**: SQLite (`data/markettalento.db`)
- **Modo Producción**: PostgreSQL (Render Free)

---

## 📋 Requisitos

Ver `requirements.txt` para todas las dependencias.

| Paquete | Uso |
|---------|-----|
| `fastapi` | API REST |
| `uvicorn` | Servidor ASGI |
| `sqlalchemy` | ORM |
| `streamlit` | Dashboard |
| `plotly` | Gráficos |
| `scikit-learn` | ML predictions |

---

## 🛠️ Desarrollo Local

```bash
# Clonar repo
git clone https://github.com/tu-user/markettalento.git
cd markettalento

# Crear entorno
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar BD con datos demo
python scripts/init_db.py
python scripts/crear_admin.py
python scripts/generar_datos_demo.py

# Ejecutar todo (API + Dashboard)
python run.py
```

**Resultado:**
- API: http://localhost:8002/docs
- Dashboard: http://localhost:8501

---

## 📁 Estructura de Archivos

```
markettalento/
├── app/                    # Aplicación Streamlit
│   ├── main.py            # Entry point
│   ├── views/             # Vistas de cada sección
│   ├── utils/api.py       # Cliente API
│   └── components/        # Componentes UI
├── src/                   # Backend FastAPI
│   ├── api/              # Endpoints REST
│   ├── dominio/          # Entidades DB
│   └── aplicacion/      # Lógica de negocio
├── data/                 # SQLite local (desarrollo)
├── scripts/             # Scripts de utilidad
└── requirements.txt    # Dependencias Python
```

---

## ⚠️ Notas Importantes

### Render Free Tier
- La app se "duerme" tras ~15 min de inactividad
- Tiempo de inicio: ~30 segundos ( cold start)
- Límite: 750 horas/mes

### Streamlit Cloud
- No hay cold start (siempre activo)
- Memoria: ~800MB
- Sin workers en background

### Persistencia de Datos
- **PostgreSQL** en Render: Datos persistentes ✅
- **Streamlit Cloud**: Solo lectura de datos

---

## 📞 Soporte

Para issues o problemas: https://github.com/tu-user/markettalento/issues