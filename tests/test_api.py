import subprocess
import time
import requests
import sys

proceso = None

try:
    print("Iniciando servidor...")
    proceso = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd="D:/ADEV/ProyectosVScode/MarkeTTalento",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(6)
    
    print("Probando /api/v1/salud...")
    r = requests.get("http://127.0.0.1:8000/api/v1/salud", timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Respuesta: {r.json()}")
    
    print("\nProbando /api/v1/productos...")
    r = requests.get("http://127.0.0.1:8000/api/v1/productos", timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Total productos: {len(r.json())}")
    
    print("\nAPI funcionando correctamente!")
    
finally:
    if proceso:
        proceso.terminate()
        proceso.wait()