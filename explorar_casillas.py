
import cv2
import os
import glob

archivos = sorted(
    glob.glob("casillas/casilla_*.png"),
    key=lambda ruta: tuple(
        int(n) for n in os.path.basename(ruta)
        .replace("casilla_", "")
        .replace(".png", "")
        .split("_")
    )
)

if not archivos:
    raise ValueError("No se encontraron casillas. Ejecuta primero tablero.py.")

indice = 0

while True:
    imagen = cv2.imread(archivos[indice])
    ampliada = cv2.resize(
        imagen,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_NEAREST
    )

    nombre = os.path.basename(archivos[indice])
    cv2.imshow("Explorador de casillas", ampliada)

    print(f"Casilla {indice + 1}/{len(archivos)}: {nombre}")

    tecla = cv2.waitKey(0) & 0xFF

    if tecla == 27:
        break
    elif tecla == ord("d") or tecla == 83:
        indice = (indice + 1) % len(archivos)
    elif tecla == ord("a") or tecla == 81:
        indice = (indice - 1) % len(archivos)

cv2.destroyAllWindows()
