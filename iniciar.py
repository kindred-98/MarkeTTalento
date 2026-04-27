"""
MarkeTTalento - Launcher
Inicia toda la aplicación con un solo comando
"""
import subprocess
import sys
import os
import time
import webbrowser

def iniciar():
    print("=" * 50)
    print("MarkeTTalento - Iniciando...")
    print("=" * 50)
    
    proyecto_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(proyecto_dir)
    
    # 1. Verificar si la API ya está corriendo
    try:
        import requests
        r = requests.get("http://127.0.0.1:8002/api/v1/salud", timeout=2)
        api_ya_esta = r.status_code == 200
    except:
        api_ya_esta = False
    
    if not api_ya_esta:
        print("\n[1] Iniciando API...")
        api = subprocess.Popen(
            [sys.executable, "main.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print("    API iniciada en http://127.0.0.1:8002")
    else:
        print("\n[1] API ya estaba corriendo")
    
    # 2. Verificar si Streamlit ya está corriendo
    import socket
    def puerto_ocupado(puerto):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', puerto)) == 0
    
    if not puerto_ocupado(8501):
        print("\n[2] Iniciando Streamlit Dashboard...")
        streamlit = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless", "true"],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print("    Dashboard iniciado en http://localhost:8501")
    else:
        print("\n[2] Streamlit ya estaba corriendo")
    
    # 3. Abrir navegador
    print("\n[3] Abriendo navegador...")
    time.sleep(4)
    webbrowser.open("http://localhost:8501")
    webbrowser.open("http://localhost:8002/docs")
    
    print("\n" + "=" * 50)
    print("MarkeTTalento iniciado!")
    print("=" * 50)
    print("\nAccesos:")
    print("  http://localhost:8501  (Dashboard)")
    print("  http://localhost:8002/docs  (API Docs)")
    print("\nCierra esta ventana para detener todo")
    print("=" * 50)
    
    # Mantener el proceso vivo
    time.sleep(999999)

if __name__ == "__main__":
    iniciar()