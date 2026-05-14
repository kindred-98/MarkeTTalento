#!/usr/bin/env python3
"""
MarkeTTalento - Iniciar Todo (API + Dashboard)
"""
import subprocess
import sys
import os
import webbrowser
import time
import threading

def iniciar_api():
    print("Iniciando API FastAPI...")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api:app", "--host", "127.0.0.1", "--port", "8002", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return api_process

def iniciar_dashboard():
    print("Iniciando Dashboard Streamlit...")
    dash_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless", "true", "--server.port", "8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return dash_process

def abrir_navegador():
    time.sleep(6)
    webbrowser.open("http://localhost:8501")
    webbrowser.open("http://localhost:8002/docs")

def main():
    print()
    print("=" * 55)
    print("  MarkeTTalento - Iniciando Todo...")
    print("=" * 55)
    print()
    
    api_process = iniciar_api()
    time.sleep(4)
    dash_process = iniciar_dashboard()
    
    browser_thread = threading.Thread(target=abrir_navegador)
    browser_thread.daemon = True
    browser_thread.start()
    
    print()
    print("=" * 55)
    print("  Todo corriendo!")
    print("  Dashboard: http://localhost:8501")
    print("  API Docs:  http://localhost:8002/docs")
    print("  Presiona Ctrl+C para detener")
    print("=" * 55)
    print()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Cerrando servicios...")
        dash_process.terminate()
        api_process.terminate()
        print("  MarkeTTalento cerrado")

if __name__ == "__main__":
    main()