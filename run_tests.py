"""
Script para ejecutar tests fácilmente.
Uso: python run_tests.py
"""
import subprocess
import sys


def run_tests():
    """Ejecuta todos los tests con pytest."""
    print("=" * 70)
    print("EJECUTANDO TODOS LOS TESTS DEL PROYECTO")
    print("=" * 70)
    print()
    
    # Ejecutar pytest para todos los tests
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=False,
        text=True
    )
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("[OK] TODOS LOS TESTS PASARON")
    else:
        print("[FAIL] ALGUNOS TESTS FALLARON")
    print("=" * 70)
    
    return result.returncode


def run_tests_with_coverage():
    """Ejecuta todos los tests con cobertura."""
    print("=" * 70)
    print("EJECUTANDO TESTS CON COBERTURA")
    print("=" * 70)
    print()
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--cov=app", "--cov-report=term-missing"],
        capture_output=False,
        text=True
    )
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("[OK] TODOS LOS TESTS PASARON")
    else:
        print("[FAIL] ALGUNOS TESTS FALLARON")
    print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ejecutar tests del proyecto")
    parser.add_argument("--cov", action="store_true", help="Ejecutar con cobertura")
    args = parser.parse_args()
    
    if args.cov:
        exit_code = run_tests_with_coverage()
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)
