# MarkeTTalento - Imagen de Produccion
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p data docs/img_productos logs

# Puerto de la API
EXPOSE 8002

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/api/v1/salud')" || exit 1

# Comando por defecto: iniciar API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
