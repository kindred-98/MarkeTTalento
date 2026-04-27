import subprocess
import time
import sys
import requests

print("Iniciando API...")
api = subprocess.Popen(
    [sys.executable, "main.py"],
    cwd="D:/ADEV/ProyectosVScode/MarkeTTalento",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print("Esperando que inicie...")
time.sleep(4)

print("Probando...")
try:
    r = requests.get("http://127.0.0.1:8000/api/v1/salud", timeout=5)
    print(f"API respondiendo: {r.status_code}")
    print(r.json())
except Exception as e:
    print(f"Error: {e}")
    print("Revisa que el puerto 8000 no esté bloqueado")