"""
aprendizaje.py - Descubrimiento de conexiones pulsador -> rejas mediante observacion.

Solo se captura la pantalla cuando se activa un pulsador cuya conexion se desconoce.
Se vuelven a reconocer UNICAMENTE las casillas de reja (no todo el tablero) y se comparan con
el estado que predecia el modelo antes de conocer la conexion.
"""

from dataclasses import dataclass
from typing import Optional

from modelo import CATEGORIAS_REJA

# Error medio (0-255) por debajo del cual una clasificacion se considera fiable.
# Calibralo con los errores que imprime vision.py sobre tus propias capturas.
UMBRAL_ERROR = 25.0


@dataclass
class ResultadoObservacion:
    concluyente: bool
    rejas_nuevas: frozenset = frozenset()
    motivo: str = ""
    inconsistente: bool = False


def comparar_rejas(celdas, rejas_esperadas, observaciones, umbral_error=UMBRAL_ERROR):
    """
    celdas: casillas de reja que se han vuelto a reconocer.
    rejas_esperadas: rejas que el modelo da por abiertas ANTES de aplicar la nueva conexion.
    observaciones: {celda: (categoria, error)}.
    Solo atribuye cambios cerrada -> abierta si TODAS las celdas son fiables.
    """
    nuevas = set()
    hubo_cerrada = False
    for celda in celdas:
        categoria, error = observaciones.get(celda, ("desconocido", float("inf")))
        if categoria not in CATEGORIAS_REJA or error > umbral_error:
            return ResultadoObservacion(
                False, frozenset(),
                "casilla {} ambigua (categoria={}, error={:.1f})".format(celda, categoria, error))
        abierta = categoria == "reja_abierta"
        if celda in rejas_esperadas:
            if not abierta:
                return ResultadoObservacion(
                    False, frozenset(),
                    "la reja {} deberia estar abierta y se ve cerrada".format(celda),
                    inconsistente=True)
        else:
            hubo_cerrada = True
            if abierta:
                nuevas.add(celda)
    if not hubo_cerrada:
        return ResultadoObservacion(
            False, frozenset(), "observacion no informativa: todas las rejas ya estaban abiertas")
    return ResultadoObservacion(True, frozenset(nuevas))


class Aprendiz:
    def __init__(self, conexiones, observador, umbral_error=UMBRAL_ERROR, log=print):
        self.conexiones = conexiones
        self.observador = observador
        self.umbral_error = umbral_error
        self.log = log
        self.capturas = 0

    def observar(self, modelo, pulsador, rejas_esperadas) -> Optional[ResultadoObservacion]:
        """
        Se llama justo despues de activar `pulsador` (conexion desconocida), con el estado ya
        actualizado en `modelo`. Registra la conexion solo si la comparacion es concluyente.
        """
        tablero, estado = modelo.tablero, modelo.estado
        celdas = [r for r in tablero.rejas if r != estado.jugador]  # bajo el jugador no se ve
        self.conexiones.registrar_intento(pulsador)

        observaciones = self.observador.observar_celdas(celdas)
        self.capturas += 1
        res = comparar_rejas(celdas, rejas_esperadas, observaciones, self.umbral_error)

        if res.inconsistente:
            self.log("[aprendizaje] inconsistencia: {}".format(res.motivo))
        elif not res.concluyente:
            self.log("[aprendizaje] pulsador {} sigue DESCONOCIDO: {}".format(pulsador, res.motivo))
        elif res.rejas_nuevas:
            self.conexiones.registrar(pulsador, res.rejas_nuevas)
            self.log("[aprendizaje] pulsador {} abre las rejas {}".format(
                pulsador, sorted(res.rejas_nuevas)))
        else:
            self.conexiones.registrar_sin_efecto(pulsador)
            self.log("[aprendizaje] pulsador {} no abrio ninguna reja (observacion {}/{})".format(
                pulsador, self.conexiones._vacias.get(pulsador, 0), self.conexiones.UMBRAL_VACIAS))
        return res
