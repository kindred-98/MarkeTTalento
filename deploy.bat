@echo off
REM Script de deploy para Windows - MarkeTTalento

echo =========================================
echo MarkeTTalento - Deploy en Produccion
echo =========================================
echo.

REM Verificar que existe .env
if not exist .env (
    echo [ERROR] No se encontro archivo .env
    echo Creando .env con valores por defecto...
    echo SECRET_KEY=markettalento-production-secret-key > .env
    echo DATABASE_URL=sqlite:///data/markettalento.db >> .env
    echo API_HOST=0.0.0.0 >> .env
    echo API_PORT=8002 >> .env
    echo.
)

REM Crear directorios necesarios
if not exist data mkdir data
if not exist logs mkdir logs
if not exist backups mkdir backups
if not exist docs\img_productos mkdir docs\img_productos

echo [1/5] Verificando base de datos...
if not exist data\markettalento.db (
    echo [INFO] Base de datos no encontrada. Se creara al iniciar.
) else (
    echo [OK] Base de datos existe
)

echo.
echo [2/5] Verificando dependencias...
python -c "import fastapi, sqlalchemy, streamlit" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Instalando dependencias...
    pip install -r requirements.txt --quiet
) else (
    echo [OK] Dependencias instaladas
)

echo.
echo [3/5] Creando usuarios por defecto...
python scripts\crear_admin.py

echo.
echo [4/5] Aplicando migraciones (si existen)...
alembic upgrade head 2>nul
if %errorlevel% neq 0 (
    echo [INFO] No hay migraciones pendientes o Alembic no esta configurado
)

echo.
echo [5/5] Iniciando servicios...
echo.
echo La API estara disponible en: http://localhost:8002
echo El Dashboard en: http://localhost:8501
echo.
echo Para detener, presiona Ctrl+C en ambas ventanas
echo.

start "MarkeTTalento API" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8002"
timeout /t 3 >nul
start "MarkeTTalento Dashboard" cmd /k "streamlit run app\main.py --server.port 8501 --server.address 0.0.0.0"

echo [OK] Servicios iniciados!
echo.
pause
