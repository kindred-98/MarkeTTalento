"""
Limpia la galería de referencia para empezar de cero.
NO borra los archivos físicos, solo los registros de la BD.
"""
import sqlite3
import os

DB_PATH = r'D:\ADEV\ProyectosVScode\MarkeTTalento\data\markettalento.db'
EMB_PATH = r'D:\ADEV\ProyectosVScode\MarkeTTalento\data\embeddings_productos.pkl'

conn = sqlite3.connect(DB_PATH)
cur = conn.execute("SELECT COUNT(*) FROM producto_imagenes_referencia")
count = cur.fetchone()[0]
print(f"Imagenes de referencia actuales en BD: {count}")

if count > 0:
    conn.execute("DELETE FROM producto_imagenes_referencia")
    conn.commit()
    print("[OK] Tabla limpiada. Todos los registros de referencia eliminados.")
else:
    print("La tabla ya estaba vacia.")

conn.close()

if os.path.exists(EMB_PATH):
    os.remove(EMB_PATH)
    print(f"[OK] Archivo de embeddings eliminado: {EMB_PATH}")
else:
    print("No habia archivo de embeddings.")

print("\n=== LISTO ===")
print("Ahora puedes ir a la app (Vision AI -> Galeria de Referencia)")
print("y subir las fotos manualmente producto por producto.")
print("Cuando termines, pulsa 'Re-entrenar Modelo Visual'.")
