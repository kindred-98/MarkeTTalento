#!/usr/bin/env python3
"""
MarkeTTalento - Desarrollo local
Inicia el Dashboard Streamlit con acceso directo a SQLite
"""
import subprocess
import sys
import os
import webbrowser
import threading
import time


def iniciar_dashboard():
    print("📦 Iniciando MarkeTTalento...")
    dashboard_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless", "true"],
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=subprocess.DEVNULL,
    )
    return dashboard_process


def abrir_navegador():
    time.sleep(4)
    webbrowser.open("http://localhost:8501")
    print("    ✅ Dashboard abierto: http://localhost:8501")


def main():
    process = iniciar_dashboard()
    browser_thread = threading.Thread(target=abrir_navegador)
    browser_thread.daemon = True
    browser_thread.start()

    print()
    print("=" * 50)
    print("  ✅ MarkeTTalento está corriendo!")
    print("  📊 http://localhost:8501")
    print("  Presiona Ctrl+C para detener")
    print("=" * 50)
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Cerrando...")
        process.terminate()
        process.wait()
        print("✅ MarkeTTalento cerrado")


if __name__ == "__main__":
    main()