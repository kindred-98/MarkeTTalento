"""
Prueba de detección de productos en imagen de estantería
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ultralytics import YOLO

print("=" * 50)
print("DETECTOR DE PRODUCTOS - YOLOv8")
print("=" * 50)

print("\nCargando modelo...")
modelo = YOLO("yolov8n.pt")

ruta_imagen = "test.jpg"

if not os.path.exists(ruta_imagen):
    print(f"\nERROR: No encontrada imagen: {ruta_imagen}")
    sys.exit(1)

print(f"Analizando: {ruta_imagen}")
print("(Esto puede tomar unos segundos...)\n")

# Confianza más baja para detectar más objetos
resultados = modelo(ruta_imagen, conf=0.15, verbose=False)

print("=" * 50)
print("RESULTADOS")
print("=" * 50)

conteo_total = 0

for i, resultado in enumerate(resultados):
    boxes = resultado.boxes
    
    if len(boxes) == 0:
        print("No se detectó ningún objeto")
        continue
    
    print(f"\nObjetos detectados: {len(boxes)}\n")
    
    conteo = {}
    for box in boxes:
        clase_id = int(box.cls[0])
        nombre = resultado.names[clase_id]
        confianza = float(box.conf[0]) * 100
        
        if nombre in conteo:
            conteo[nombre] += 1
        else:
            conteo[nombre] = 1
        
        print(f"  [{confianza:5.1f}%] {nombre}")
    
    print("\n" + "-" * 30)
    print("CONTEO TOTAL:")
    for nombre, cantidad in conteo.items():
        print(f"  {nombre}: {cantidad}")
        conteo_total += cantidad

print("\n" + "=" * 50)
print(f"Total objetos: {conteo_total}")
print("=" * 50)