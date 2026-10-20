
import os
import json
import cv2
import numpy as np
import mss

FILAS = 15
COLUMNAS = 10
CARPETA_EJEMPLOS = "ejemplos"
RADIO_DESPLAZAMIENTO = 3

with open("config_tablero.json", "r") as archivo:
    config = json.load(archivo)

def capturar_pantalla():
    with mss.mss() as captura:
        pantalla = np.array(captura.grab(captura.monitors[1]))
    return cv2.cvtColor(pantalla, cv2.COLOR_BGRA2BGR)

def cargar_ejemplos():
    ejemplos = {}

    for categoria in os.listdir(CARPETA_EJEMPLOS):
        ruta_categoria = os.path.join(CARPETA_EJEMPLOS, categoria)

        if not os.path.isdir(ruta_categoria):
            continue

        imagenes = []

        for nombre in os.listdir(ruta_categoria):
            ruta = os.path.join(ruta_categoria, nombre)
            imagen = cv2.imread(ruta)

            if imagen is not None:
                imagenes.append(cv2.resize(imagen, (64, 64)))

        if imagenes:
            ejemplos[categoria] = imagenes

    return ejemplos

def comparar(a, b):
    mejor_error = float("inf")

    for dy in range(-RADIO_DESPLAZAMIENTO, RADIO_DESPLAZAMIENTO + 1):
        for dx in range(-RADIO_DESPLAZAMIENTO, RADIO_DESPLAZAMIENTO + 1):
            desplazada = np.roll(b, (dy, dx), axis=(0, 1))
            diferencia = cv2.absdiff(a, desplazada)
            error = np.mean(diferencia)

            if error < mejor_error:
                mejor_error = error

    return mejor_error

def clasificar(casilla, ejemplos):
    imagen = cv2.resize(casilla, (64, 64))
    mejor_categoria = "desconocido"
    menor_error = float("inf")

    for categoria, muestras in ejemplos.items():
        for muestra in muestras:
            error = comparar(imagen, muestra)

            if error < menor_error:
                menor_error = error
                mejor_categoria = categoria

    return mejor_categoria, menor_error

ejemplos = cargar_ejemplos()

if not ejemplos:
    raise ValueError("No se encontraron imagenes dentro de ejemplos/.")

print("Categorias cargadas:", list(ejemplos.keys()))

pantalla = capturar_pantalla()

x = config["x"]
y = config["y"]
ancho = config["ancho"]
alto = config["alto"]

tablero = pantalla[y:y + alto, x:x + ancho]

if tablero.size == 0:
    raise ValueError("La region del tablero esta vacia.")

alto_real, ancho_real = tablero.shape[:2]
matriz = []
vista = tablero.copy()

for f in range(FILAS):
    fila = []

    for c in range(COLUMNAS):
        x1 = round(c * ancho_real / COLUMNAS)
        x2 = round((c + 1) * ancho_real / COLUMNAS)
        y1 = round(f * alto_real / FILAS)
        y2 = round((f + 1) * alto_real / FILAS)

        casilla = tablero[y1:y2, x1:x2]
        categoria, error = clasificar(casilla, ejemplos)
        fila.append(categoria)

        cv2.rectangle(vista, (x1, y1), (x2, y2), (0, 255, 0), 1)

        etiqueta = categoria[:9]
        cv2.putText(
            vista, etiqueta, (x1 + 2, y1 + 14),
            cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 255), 1
        )

    matriz.append(fila)


alto_real, ancho_real = tablero.shape[:2]
matriz = [["muro" for c in range(COLUMNAS)] for f in range(FILAS)]
vista = tablero.copy()

for f in range(FILAS):
    for c in range(COLUMNAS):

        # Omitir las casillas que siempre son muros
        if f in (0, 1, FILAS - 1) or c in (0, COLUMNAS - 1):
            categoria = "muro"
        else:
            x1 = round(c * ancho_real / COLUMNAS)
            x2 = round((c + 1) * ancho_real / COLUMNAS)
            y1 = round(f * alto_real / FILAS)
            y2 = round((f + 1) * alto_real / FILAS)

            casilla = tablero[y1:y2, x1:x2]
            categoria, error = clasificar(casilla, ejemplos)

        matriz[f][c] = categoria

        x1 = round(c * ancho_real / COLUMNAS)
        x2 = round((c + 1) * ancho_real / COLUMNAS)
        y1 = round(f * alto_real / FILAS)
        y2 = round((f + 1) * alto_real / FILAS)

        cv2.rectangle(vista, (x1, y1), (x2, y2), (0, 255, 0), 1)

        cv2.putText(
            vista, categoria[:9], (x1 + 2, y1 + 14),
            cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 255), 1
        )

with open("matriz_tablero.json", "w", encoding="utf-8") as archivo:
    json.dump(matriz, archivo, indent=2, ensure_ascii=False)

print("\nMatriz detectada:")
for fila in matriz:
    print(fila)

cv2.imshow("Reconocimiento del tablero", vista)
cv2.waitKey(0)
cv2.destroyAllWindows()

