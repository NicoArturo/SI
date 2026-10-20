
import time
from control import mover

print("Selecciona la ventana del juego. Tienes 2 segundos.")
time.sleep(2)

mover("derecha")
mover("abajo")
mover("izquierda")
mover("arriba")

print("Prueba terminada.")
