
import json
import cv2
import numpy as np
import mss

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

tablero = pantalla[y:y + alto, x:x + ancho].copy()

alto_real, ancho_real = tablero.shape[:2]

for c in range(columnas + 1):
    px = round(c * ancho_real / columnas)
    cv2.line(tablero, (px, 0), (px, alto_real - 1), (0, 255, 0), 1)

for f in range(filas + 1):
    py = round(f * alto_real / filas)
    cv2.line(tablero, (0, py), (ancho_real - 1, py), (0, 255, 0), 1)

cv2.imshow("Cuadricula", tablero)
cv2.waitKey(0)
cv2.destroyAllWindows()
