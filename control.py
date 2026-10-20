
import pyautogui
import time

DURACION_PULSACION = 0.03

def mover(direccion):
    direcciones = {
        "arriba": "up",
        "abajo": "down",
        "izquierda": "left",
        "derecha": "right"
    }

    if direccion not in direcciones:
        print("Direccion no valida.")
        return

    tecla = direcciones[direccion]

    pyautogui.keyDown(tecla)
    time.sleep(DURACION_PULSACION)
    pyautogui.keyUp(tecla)

    time.sleep(0.07)
