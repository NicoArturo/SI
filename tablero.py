
import json
import cv2
import numpy as np
import mss
import os

with open("config_tablero.json", "r") as archivo:
    config = json.load(archivo)

filas = 15
columnas = 10

with mss.mss() as captura:
    pantalla = np.array(captura.grab(captura.monitors[1]))
    pantalla = cv2.cvtColor(pantalla, cv2.COLOR_BGRA2BGR)

x = config["x"]
y = config["y"]
ancho = config["ancho"]
alto = config["alto"]

imagen = pantalla[y:y + alto, x:x + ancho]

if imagen.size == 0:
    raise ValueError("No se pudo capturar el tablero.")

alto_real, ancho_real = imagen.shape[:2]
casillas = []

for f in range(filas):
    fila = []

    for c in range(columnas):
        x1 = round(c * ancho_real / columnas)
        x2 = round((c + 1) * ancho_real / columnas)
        y1 = round(f * alto_real / filas)
        y2 = round((f + 1) * alto_real / filas)

        casilla = imagen[y1:y2, x1:x2]
        fila.append(casilla)

    casillas.append(fila)

os.makedirs("casillas", exist_ok=True)

for f in range(filas):
    for c in range(columnas):
        cv2.imwrite(
            f"casillas/casilla_{f}_{c}.png",
            casillas[f][c]
        )

print(f"Tablero dividido en {filas} filas y {columnas} columnas.")
print("Las imágenes de las casillas se guardaron en la carpeta casillas.")

vista = imagen.copy()

for f in range(filas + 1):
    py = round(f * alto_real / filas)
    cv2.line(vista, (0, py), (ancho_real - 1, py), (0, 255, 0), 1)

for c in range(columnas + 1):
    px = round(c * ancho_real / columnas)
    cv2.line(vista, (px, 0), (px, alto_real - 1), (0, 255, 0), 1)

cv2.imshow("Tablero detectado", vista)
cv2.waitKey(0)
cv2.destroyAllWindows()
