
import json
import cv2
import numpy as np
import mss

with open("config_tablero.json", "r") as archivo:
    config = json.load(archivo)

filas = 15
columnas = 10

fila = int(input("Fila de la casilla (0 a {}): ".format(filas - 1)))
columna = int(input("Columna de la casilla (0 a {}): ".format(columnas - 1)))

if not (0 <= fila < filas and 0 <= columna < columnas):
    raise ValueError("Las coordenadas estan fuera del tablero.")

with mss.mss() as captura:
    pantalla = np.array(captura.grab(captura.monitors[1]))
    pantalla = cv2.cvtColor(pantalla, cv2.COLOR_BGRA2BGR)

x = config["x"]
y = config["y"]
ancho = config["ancho"]
alto = config["alto"]

tablero = pantalla[y:y + alto, x:x + ancho]

if tablero.size == 0:
    raise ValueError("No se pudo capturar el tablero.")

alto_real, ancho_real = tablero.shape[:2]

x1 = round(columna * ancho_real / columnas)
x2 = round((columna + 1) * ancho_real / columnas)
y1 = round(fila * alto_real / filas)
y2 = round((fila + 1) * alto_real / filas)

casilla = tablero[y1:y2, x1:x2]

ampliada = cv2.resize(
    casilla,
    None,
    fx=5,
    fy=5,
    interpolation=cv2.INTER_NEAREST
)

cv2.imshow("Casilla seleccionada", ampliada)
cv2.imwrite("casilla_seleccionada.png", casilla)

print("Casilla guardada en casilla_seleccionada.png")
print("Coordenadas: fila {}, columna {}".format(fila, columna))

cv2.waitKey(0)
cv2.destroyAllWindows()
