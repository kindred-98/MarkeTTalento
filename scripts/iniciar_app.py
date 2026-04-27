"""
MarkeTTalento - Launcher
Ejecuta API y Dashboard con un solo comando
"""
import subprocess
import sys
import os
import time
import signal

def iniciar():
    print("=" * 50)
    print("MarkeTTalento - Iniciando...")
    print("=" * 50)
    
    # Procesos
    procesos = []
    
    # 1. API
    print("\n[1] Iniciando API...")
    api = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    procesos.append(("API", api))
    
    time.sleep(3)
    
    # 2. Streamlit
    print("[2] Iniciando Dashboard...")
    streamlit = subprocess.Popen(
        ["streamlit", "run", "streamlit_app.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    procesos.append(("Streamlit", streamlit))
    
    print("\n" + "=" * 50)
    print("MarkeTTalento iniciado!")
    print("=" * 50)
    print("\nAccesos:")
    print("  API:       http://localhost:8002")
    print("  Docs:     http://localhost:8002/docs")
    print("  Dashboard: http://localhost:8501")
    print("\nPresiona Ctrl+C para detener...")
    print("=" * 50)
    
    # Esperar a que termine
    try:
        for nombre, proceso in procesos:
            proceso.wait()
    except KeyboardInterrupt:
        print("\nDeteniendo servicios...")
        for nombre, proceso in procesos:
            proceso.terminate()
        print("Listo!")


if __name__ == "__main__":
    iniciar()