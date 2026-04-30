"""
Test del endpoint de visión e inventario
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar main desde la raíz
sys.path.insert(0, 'D:/ADEV/ProyectosVScode/MarkeTTalento')

from main import app
from fastapi.testclient import TestClient

cliente = TestClient(app)

print("Probando endpoint de vision e inventario...")

if not os.path.exists('test.jpg'):
    print("No hay imagen test.jpg")
    sys.exit(1)

with open('test.jpg', 'rb') as f:
    response = cliente.post(
        '/api/v1/vision/analizar-y-actualizar',
        files={'archivo': ('test.jpg', f, 'image/jpeg')},
        data={'confianza_min': 0.15, 'actualizar_stock': 'false'}
    )

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    det = data.get('deteccion', {})
    print(f"\nObjetos detectados: {det.get('total_objetos', 0)}")
    
    if det.get('objetos'):
        print("Lista de objetos:")
        for obj in det['objetos']:
            print(f"  - {obj['nombre']}: {obj['confianza']}")
    
    mapa = data.get('mapeo', {})
    print(f"\nMapeados a BD: {mapa.get('total_mapeado', 0)}")
    
    no_encontrados = mapa.get('no_encontrados', [])
    print(f"NO encontrados en BD: {len(no_encontrados)}")
    
    if no_encontrados:
        print("\nEstos objetos NO estan en tu base de datos:")
        for item in no_encontrados:
            print(f"  {item['objeto']}: {item['cantidad']}")
            
    print("\nPara mapear estos productos, agrega mas items al MAPA_YOLO_A_PRODUCTO en inventario_vision.py")
else:
    print("Error:", response.text[:500])