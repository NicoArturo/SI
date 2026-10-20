
import mss
import cv2
import numpy as np
import json

inicio = None
seleccion = None
arrastrando = False

def capturar_pantalla():
    with mss.mss() as captura:
        pantalla = captura.grab(captura.monitors[1])
        return cv2.cvtColor(np.array(pantalla), cv2.COLOR_BGRA2BGR)

def evento_raton(evento, x, y, flags, parametro):
    global inicio, seleccion, arrastrando

    if evento == cv2.EVENT_LBUTTONDOWN:
        inicio = (x, y)
        seleccion = None
        arrastrando = True

    elif evento == cv2.EVENT_MOUSEMOVE and arrastrando:
        seleccion = (inicio[0], inicio[1], x, y)

    elif evento == cv2.EVENT_LBUTTONUP:
        arrastrando = False
        seleccion = (inicio[0], inicio[1], x, y)

imagen = capturar_pantalla()
ventana = "Seleccionar tablero"

cv2.namedWindow(ventana, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(ventana, evento_raton)

print("Arrastra un rectangulo alrededor del tablero.")
print("ENTER: guardar | ESC: cancelar")

while True:
    vista = imagen.copy()

    if seleccion is not None:
        x1, y1, x2, y2 = seleccion
        cv2.rectangle(vista, (x1, y1), (x2, y2), (0, 255, 0), 2)

    cv2.imshow(ventana, vista)
    tecla = cv2.waitKey(20) & 0xFF

    if tecla == 13 and seleccion is not None:
        x1, y1, x2, y2 = seleccion

        datos = {
            "x": min(x1, x2),
            "y": min(y1, y2),
            "ancho": abs(x2 - x1),
            "alto": abs(y2 - y1)
        }

        if datos["ancho"] > 0 and datos["alto"] > 0:
            with open("config_tablero.json", "w") as archivo:
                json.dump(datos, archivo, indent=4)

            print("Tablero guardado:", datos)
            break

    elif tecla == 27:
        break

cv2.destroyAllWindows()
