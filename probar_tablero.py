
import json
import cv2
import numpy as np
import mss

with open("config_tablero.json", "r") as archivo:
    config = json.load(archivo)

with mss.mss() as captura:
    pantalla = np.array(captura.grab(captura.monitors[1]))
    pantalla = cv2.cvtColor(pantalla, cv2.COLOR_BGRA2BGR)

x = config["x"]
y = config["y"]
ancho = config["ancho"]
alto = config["alto"]

tablero = pantalla[y:y + alto, x:x + ancho]

if tablero.size == 0:
    raise ValueError("No se pudo capturar la region del tablero.")

cv2.imshow("Tablero calibrado", tablero)
cv2.waitKey(0)
cv2.destroyAllWindows()
