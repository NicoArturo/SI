"""
conexiones.py - Registro de conexiones pulsador -> rejas (aprendidas por observacion).

Un pulsador puede estar en tres situaciones:
  * conocido con rejas        -> _rejas[p] = {rejas}
  * conocido sin efecto       -> observado UMBRAL_VACIAS veces sin cambios concluyentes
  * desconocido               -> todavia no se sabe (se puede planificar una observacion
                                 hasta MAX_INTENTOS veces)
"""

import json
import os

_VACIO = frozenset()


class Conexiones:
    UMBRAL_VACIAS = 2
    MAX_INTENTOS = 3

    def __init__(self, ruta=None, firma=None):
        self._rejas = {}
        self._vacias = {}
        self._intentos = {}
        self.ruta = ruta
        self.firma = firma

    # ---------------- consulta ----------------
    def rejas_de(self, pulsador):
        return self._rejas.get(pulsador, _VACIO)

    def conoce(self, pulsador):
        return pulsador in self._rejas or self._vacias.get(pulsador, 0) >= self.UMBRAL_VACIAS

    def puede_explorar(self, pulsador):
        return (not self.conoce(pulsador)
                and self._intentos.get(pulsador, 0) < self.MAX_INTENTOS)

    def intentos(self, pulsador):
        return self._intentos.get(pulsador, 0)

    def rejas_controladas(self):
        todas = set()
        for rejas in self._rejas.values():
            todas |= rejas
        return frozenset(todas)

    def resumen(self, pulsadores):
        conocidas, desconocidas = {}, []
        for p in pulsadores:
            if self.conoce(p):
                conocidas[p] = sorted(self.rejas_de(p))
            else:
                desconocidas.append(p)
        return conocidas, desconocidas

    # ---------------- escritura ----------------
    def registrar_intento(self, pulsador):
        self._intentos[pulsador] = self._intentos.get(pulsador, 0) + 1
        self.guardar()

    def registrar(self, pulsador, rejas):
        self._rejas[pulsador] = self._rejas.get(pulsador, _VACIO) | frozenset(rejas)
        self.guardar()

    def registrar_sin_efecto(self, pulsador):
        self._vacias[pulsador] = self._vacias.get(pulsador, 0) + 1
        self.guardar()

    # ---------------- persistencia ----------------
    def guardar(self):
        if not self.ruta:
            return
        datos = {
            "firma": self.firma,
            "conexiones": [
                {"pulsador": list(p), "rejas": [list(r) for r in sorted(rs)]}
                for p, rs in sorted(self._rejas.items())
            ],
            "sin_efecto": [{"pulsador": list(p), "veces": n}
                           for p, n in sorted(self._vacias.items())],
            "intentos": [{"pulsador": list(p), "veces": n}
                         for p, n in sorted(self._intentos.items())],
        }
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=2)

    @classmethod
    def cargar(cls, ruta, firma):
        """Carga conexiones guardadas solo si pertenecen al mismo nivel (misma firma)."""
        nueva = cls(ruta=ruta, firma=firma)
        if not ruta or not os.path.exists(ruta):
            return nueva
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, ValueError):
            return nueva
        if datos.get("firma") != firma:
            return nueva
        for item in datos.get("conexiones", []):
            nueva._rejas[tuple(item["pulsador"])] = frozenset(tuple(r) for r in item["rejas"])
        for item in datos.get("sin_efecto", []):
            nueva._vacias[tuple(item["pulsador"])] = item["veces"]
        for item in datos.get("intentos", []):
            nueva._intentos[tuple(item["pulsador"])] = item["veces"]
        return nueva
