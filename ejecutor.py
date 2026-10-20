"""
ejecutor.py - Envia las acciones al teclado usando el modulo existente control.py.
"""

DIRECCIONES_VALIDAS = ("arriba", "abajo", "izquierda", "derecha")


class Ejecutor:
    def __init__(self, mover_fn=None):
        """mover_fn: por defecto control.mover (se importa al primer uso)."""
        self._mover = mover_fn
        self.enviadas = []

    def enviar(self, direccion):
        if direccion not in DIRECCIONES_VALIDAS:
            raise ValueError("Direccion no valida: {}".format(direccion))
        if self._mover is None:
            from control import mover
            self._mover = mover
        self._mover(direccion)
        self.enviadas.append(direccion)
