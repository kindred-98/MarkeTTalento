"""
Configuración de pytest para el proyecto.
"""
import sys
import os

# Agregar el directorio raíz al path para poder importar app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuración de pytest
def pytest_configure(config):
    """Configuración adicional de pytest."""
    config.addinivalue_line("markers", "slow: marca tests que son lentos")
    config.addinivalue_line("markers", "unit: marca tests unitarios")
