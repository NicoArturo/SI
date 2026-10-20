"""
planificador.py - Busqueda de rutas sobre el ESTADO COMPLETO del juego.

* Plan "objetivo": A* hasta la salida (abierta) usando solo conexiones conocidas.
  - Heuristica admisible: cada movimiento entra en una casilla; hay que entrar en una casilla
    distinta por cada diamante restante y en la salida (>= diamantes + 1), y ademas
    max_d [dist(jugador,d) + dist(d,salida)] (Manhattan). El coste de pinchos solo suma, por
    lo que la heuristica sigue siendo un limite inferior.
  - Si se supera el limite de nodos se reintenta con A* ponderado (rapido, no optimo).
* Plan "exploracion": si no hay ruta con lo que se sabe, busca la forma mas barata de activar un
  pulsador de conexion desconocida (con el jugador o con una piedra), comprobando que sea seguro.
  Empujar una piedra se penaliza (penalizacion_empuje): se prefiere un rodeo largo antes que
  desacomodar piedras. Entre varios pulsadores candidatos, el A* elige el de menor coste total,
  es decir, el que menos piedras mueve.
"""

import copy
import heapq
import itertools
from collections import deque
from dataclasses import dataclass, replace
from typing import List, Optional

from modelo import Estado
from reglas import acciones_legales, pulsadores_activos


@dataclass
class Plan:
    acciones: List[str]
    tipo: str = "objetivo"            # "objetivo" | "exploracion"
    costo: int = 0
    nodos: int = 0
    optimo: bool = True
    pulsador: Optional[tuple] = None  # pulsador a descubrir (plan de exploracion)
    estado_final: Optional[Estado] = None


def distancia(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def heuristica_salida(tablero, estado):
    salida = tablero.salida
    if salida is None:
        return 0
    base = distancia(estado.jugador, salida)
    n = tablero.reglas.diamantes_para_salida
    if n is None:
        if estado.diamantes:
            lejano = max(distancia(estado.jugador, d) + distancia(d, salida)
                         for d in estado.diamantes)
            return max(base, lejano, len(estado.diamantes) + 1)
        return base
    faltan = max(0, n - estado.diamantes_recogidos)
    return max(base, faltan + 1 if faltan else 0)


def _camino(padre, clave):
    acciones = []
    while padre[clave] is not None:
        previo, accion = padre[clave]
        acciones.append(accion)
        clave = previo
    acciones.reverse()
    return acciones


@dataclass
class _Resultado:
    acciones: Optional[List[str]] = None
    costo: int = 0
    nodos: int = 0
    agotado: bool = False
    estado_final: Optional[Estado] = None


def _astar(tablero, inicio, conexiones, heuristica, es_meta=None, meta_trans=None,
           peso=1.0, max_nodos=300000):
    """
    A* generico. Meta por estado (es_meta) o por transicion (meta_trans(prev, nuevo)).
    Las metas por transicion se encolan como nodos (estado, "meta") con h = 0.
    """
    inf = float("inf")
    contador = itertools.count()
    g = {inicio: 0}
    padre = {inicio: None}
    cerrados = set()
    abiertos = [(peso * heuristica(inicio), next(contador), inicio)]
    nodos = 0

    while abiertos:
        _, _, clave = heapq.heappop(abiertos)

        if isinstance(clave, tuple):  # meta por transicion
            return _Resultado(_camino(padre, clave), g[clave], nodos, False, clave[0])

        estado = clave
        if estado in cerrados:
            continue
        if estado != inicio and es_meta is not None and es_meta(estado):
            return _Resultado(_camino(padre, estado), g[estado], nodos, False, estado)

        cerrados.add(estado)
        nodos += 1
        if nodos > max_nodos:
            return _Resultado(None, 0, nodos, True)

        gc = g[estado]
        for accion, nuevo, coste in acciones_legales(tablero, estado, conexiones):
            ng = gc + coste
            if meta_trans is not None and meta_trans(estado, nuevo):
                clave_meta = (nuevo, "meta")
                if ng < g.get(clave_meta, inf):
                    g[clave_meta] = ng
                    padre[clave_meta] = (estado, accion)
                    heapq.heappush(abiertos, (ng, next(contador), clave_meta))
                continue
            if ng < g.get(nuevo, inf):
                g[nuevo] = ng
                padre[nuevo] = (estado, accion)
                heapq.heappush(abiertos, (ng + peso * heuristica(nuevo), next(contador), nuevo))

    return _Resultado(None, 0, nodos, False)


class Planificador:
    def __init__(self, max_nodos=3000000, peso_fallback=3.0, max_nodos_fallback=4000000,
                 pesos_escalera=(6.0, 12.0, 30.0),
                 nodos_seguridad=20000, penalizacion_empuje=40, log=print):
        self.penalizacion_empuje = penalizacion_empuje
        self.max_nodos = max_nodos
        self.peso_fallback = peso_fallback
        # Si el A* ponderado inicial no llega, se reintenta con pesos cada vez mas voraces.
        self.pesos_escalera = tuple(pesos_escalera)
        self.max_nodos_fallback = max_nodos_fallback
        self.nodos_seguridad = nodos_seguridad
        self.log = log
        self.ultimo_motivo = ""

    # ------------------------------------------------------------------
    def planificar(self, modelo):
        t, e, c = modelo.tablero, modelo.estado, modelo.conexiones
        self.ultimo_motivo = ""
        if t.salida is None:
            self.ultimo_motivo = "El tablero no tiene casilla de salida reconocida."
            return None

        plan = self._plan_objetivo(t, e, c)
        if plan is not None:
            return plan
        plan = self._plan_exploracion(t, e, c)
        if plan is not None:
            return plan
        if not self.ultimo_motivo:
            self.ultimo_motivo = ("No existe ruta a la salida con la informacion actual y no hay "
                                  "ningun pulsador desconocido que se pueda explorar con seguridad.")
        return None

    # ------------------------------------------------------------------
    def _plan_objetivo(self, t, e, c):
        def h(estado):
            return heuristica_salida(t, estado)

        def meta(estado):
            return estado.jugador == t.salida

        res = _astar(t, e, c, h, es_meta=meta, peso=1.0, max_nodos=self.max_nodos)
        if res.acciones is not None:
            return Plan(res.acciones, "objetivo", res.costo, res.nodos, True,
                        estado_final=res.estado_final)
        if res.agotado:
            self.log("[planificador] A* supero {} nodos; reintento con A* ponderado "
                     "(ruta valida, quiza no optima).".format(self.max_nodos))
            # Escalera de pesos: cada escalon tiene un presupuesto acotado (un cuarto del
            # limite de respaldo) y, si se agota, se prueba un peso mas voraz. Los niveles con
            # muchos diamantes y piedras necesitan pesos altos para encontrar una ruta valida.
            presupuesto = max(1, self.max_nodos_fallback // 4)
            total = res.nodos
            for peso in (self.peso_fallback,) + self.pesos_escalera:
                res2 = _astar(t, e, c, h, es_meta=meta, peso=peso, max_nodos=presupuesto)
                total += res2.nodos
                if res2.acciones is not None:
                    return Plan(res2.acciones, "objetivo", res2.costo, total, False,
                                estado_final=res2.estado_final)
                if not res2.agotado:
                    break   # espacio de estados completo sin meta: no hay ruta
                self.log("[planificador] peso {} sin ruta en {} nodos; pruebo uno mayor.".format(
                    peso, presupuesto))
            self.ultimo_motivo = "Se alcanzo el limite de nodos sin encontrar ruta."
        return None

    # ------------------------------------------------------------------
    def _capacidad(self, t, estado, c):
        """
        Exploracion acotada (BFS) desde `estado`:
        devuelve (minimo de diamantes+llaves que quedan en alguna rama, salida_alcanzable).
        Sirve para comprobar que una accion de exploracion no cierra posibilidades.
        """
        minimo = len(estado.diamantes) + len(estado.llaves_tablero)
        meta = False
        vistos = {estado}
        cola = deque([estado])
        while cola and len(vistos) < self.nodos_seguridad:
            actual = cola.popleft()
            minimo = min(minimo, len(actual.diamantes) + len(actual.llaves_tablero))
            if actual.jugador == t.salida:
                meta = True
                continue
            for _, nuevo, _ in acciones_legales(t, actual, c):
                if nuevo not in vistos:
                    vistos.add(nuevo)
                    cola.append(nuevo)
        return minimo, meta

    @staticmethod
    def _contar_empujes(t, estado, c, acciones):
        """Acciones del plan que empujan una piedra (reproduce el plan sobre el tablero real)."""
        empujes = 0
        for accion in acciones:
            for a, nuevo, _ in acciones_legales(t, estado, c):
                if a == accion:
                    if nuevo.piedras != estado.piedras:
                        empujes += 1
                    estado = nuevo
                    break
        return empujes

    def _plan_exploracion(self, t, e, c):
        candidatos = frozenset(p for p in t.pulsadores if c.puede_explorar(p))
        if not candidatos or not t.rejas:
            return None

        # Tablero de exploracion: igual que el real pero penalizando empujar piedras
        # (copia superficial: el terreno es inmutable y no se toca).
        t_real = t
        t = copy.copy(t_real)
        t.reglas = replace(t_real.reglas, coste_extra_empuje=self.penalizacion_empuje)

        pre = {}
        cache = {}

        def seguro(estado):
            if estado in cache:
                return cache[estado]
            if "valor" not in pre:
                pre["valor"] = self._capacidad(t, e, c)
            post = self._capacidad(t, estado, c)
            minimo_pre, meta_pre = pre["valor"]
            ok = post[0] <= minimo_pre and (post[1] or not meta_pre)
            cache[estado] = ok
            return ok

        def meta_trans(previo, nuevo):
            antes = pulsadores_activos(t, previo)
            despues = pulsadores_activos(t, nuevo)
            if len((despues - antes) & candidatos) != 1:
                return False
            # solo un pulsador desconocido activo: si no, la observacion seria ambigua
            if sum(1 for p in despues if not c.conoce(p)) != 1:
                return False
            return seguro(nuevo)

        def h(estado):
            mejor = None
            for p in candidatos:
                d = distancia(estado.jugador, p)
                for s in estado.piedras:
                    d = min(d, distancia(s, p))
                mejor = d if mejor is None else min(mejor, d)
            return mejor or 0

        res = _astar(t, e, c, h, meta_trans=meta_trans, peso=1.0, max_nodos=self.max_nodos)
        if res.acciones is None:
            return None
        activados = pulsadores_activos(t, res.estado_final) & candidatos
        empujes = self._contar_empujes(t_real, e, c, res.acciones)
        costo_real = res.costo - self.penalizacion_empuje * empujes
        if empujes:
            self.log("[planificador] la exploracion requiere mover piedras ({} empujes); "
                     "no hay alternativa sin empujar.".format(empujes))
        return Plan(res.acciones, "exploracion", costo_real, res.nodos, True,
                    pulsador=next(iter(activados)) if activados else None,
                    estado_final=res.estado_final)
