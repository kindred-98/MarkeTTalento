#!/usr/bin/env python3
"""
MarkeTTalento - Punto único de entrada
Inicia API + Dashboard con un solo comando
"""
import subprocess
import sys
import os
import time
import webbrowser
import signal
import atexit
import threading

# Procesos activos
processes = []


def iniciar_api():
    """Inicia el servidor de la API."""
    print("[1/2] Iniciando API en http://127.0.0.1:8002...")
    
    # Sin CREATE_NEW_CONSOLE para que use la misma consola
    # Sin PIPE para que la salida vaya a la consola actual
    api_process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=subprocess.DEVNULL,
        creationflags=0
    )
    processes.append(api_process)
    print("    ✅ API iniciada")
    return api_process


def iniciar_dashboard():
    """Inicia el dashboard de Streamlit."""
    print("[2/2] Iniciando Dashboard en http://localhost:8501...")
    
    # Sin CREATE_NEW_CONSOLE para que use la misma consola
    # Sin PIPE para que la salida vaya a la consola actual
    dashboard_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app/main.py", "--server.headless", "true"],
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=subprocess.DEVNULL,
        creationflags=0
    )
    processes.append(dashboard_process)
    print("    ✅ Dashboard iniciado")
    return dashboard_process


def verificar_api():
    """Verifica si la API está corriendo."""
    try:
        import requests
        r = requests.get("http://127.0.0.1:8002/api/v1/salud", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def abrir_navegador():
    """Abre el navegador con las URLs de la aplicación."""
    time.sleep(6)  # Esperar a que todo esté listo
    print("\n[3/3] Abriendo navegador...")
    
    # Abrir ambas URLs
    webbrowser.open("http://localhost:8501")  # Dashboard
    time.sleep(1)  # Pequeña pausa entre ventanas
    webbrowser.open("http://localhost:8002/docs")  # API Docs
    
    print("    ✅ Dashboard abierto: http://localhost:8501")
    print("    ✅ API Docs abierto:  http://localhost:8002/docs")


def cleanup():
    """Limpia los procesos al cerrar."""
    print("\n🛑 Cerrando procesos...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("✅ Procesos cerrados")


def signal_handler(sig, frame):
    """Maneja la señal de interrupción (Ctrl+C)."""
    print("\n\n👋 Cerrando MarkeTTalento...")
    cleanup()
    sys.exit(0)


def main():
    """Función principal."""
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(cleanup)
    
    # Limpiar pantalla
    os.system('cls' if sys.platform == "win32" else 'clear')
    
    # Banner
    print("=" * 60)
    print("  📦 MarkeTTalento - Sistema de Inventario Inteligente")
    print("=" * 60)
    print()
    
    # Verificar si la API ya está corriendo
    if verificar_api():
        print("ℹ️  La API ya está corriendo")
        iniciar_dashboard()
    else:
        # Iniciar ambos servicios
        iniciar_api()
        time.sleep(3)  # Esperar a que la API esté lista
        iniciar_dashboard()
    
    # Abrir navegador en thread separado para no bloquear
    browser_thread = threading.Thread(target=abrir_navegador)
    browser_thread.daemon = True
    browser_thread.start()
    
    print()
    print("=" * 60)
    print("  ✅ MarkeTTalento está corriendo!")
    print()
    print("  📊 Dashboard:  http://localhost:8501")
    print("  📚 API Docs:   http://localhost:8002/docs")
    print()
    print("  Presiona Ctrl+C para detener todo")
    print("=" * 60)
    print()
    
    # Mantener el proceso vivo y mostrar logs
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
