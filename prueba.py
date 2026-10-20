
import mss
import cv2
import numpy as np

with mss.mss() as captura:
    pantalla = captura.grab(captura.monitors[1])
    imagen = np.array(pantalla)
    imagen = cv2.cvtColor(imagen, cv2.COLOR_BGRA2BGR)

    cv2.imwrite("captura.png", imagen)

print("Captura guardada correctamente.")
