"""Representación de una red fluvial como grafo dirigido acíclico (árbol).

Convención: los tramos están ordenados topológicamente, de modo que todo
tramo aguas arriba tiene un índice MENOR que el tramo al que drena. Con esa
convención la matriz de adyacencia ``A[j, i] = 1`` (i drena en j) es
estrictamente triangular inferior, lo que permite resolver el ruteo de cada
paso de tiempo con una sustitución hacia adelante.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch


@dataclass
class RedFluvial:
    """Red fluvial con atributos físicos por tramo.

    Atributos
    ---------
    aguas_abajo : índice del tramo receptor (-1 en la salida).
    longitud_m : longitud del tramo [m].
    pendiente : pendiente del lecho [m/m].
    ancho_m : ancho de cauce (geometría hidráulica) [m].
    area_local_km2 : área de la subcuenca que aporta lateralmente [km²].
    """

    aguas_abajo: np.ndarray
    longitud_m: np.ndarray
    pendiente: np.ndarray
    ancho_m: np.ndarray
    area_local_km2: np.ndarray
    nombres: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.aguas_abajo = np.asarray(self.aguas_abajo, dtype=int)
        n = len(self.aguas_abajo)
        for nombre in ("longitud_m", "pendiente", "ancho_m", "area_local_km2"):
            arr = np.asarray(getattr(self, nombre), dtype=float)
            if arr.shape != (n,):
                raise ValueError(f"{nombre} debe tener forma ({n},)")
            if np.any(arr <= 0):
                raise ValueError(f"{nombre} debe ser estrictamente positivo")
            setattr(self, nombre, arr)
        self.validar_orden_topologico()
        if not self.nombres:
            self.nombres = [f"T{i:03d}" for i in range(n)]

    # ------------------------------------------------------------------
    @property
    def n(self) -> int:
        return len(self.aguas_abajo)

    def validar_orden_topologico(self) -> None:
        idx = np.arange(self.n)
        dn = self.aguas_abajo
        internos = dn >= 0
        if np.any(dn[internos] <= idx[internos]):
            raise ValueError(
                "Orden topológico inválido: cada tramo debe drenar a un índice mayor"
            )
        if np.any(dn >= self.n) or np.any(dn < -1):
            raise ValueError("Índices aguas abajo fuera de rango")

    def adyacencia(self, dtype=torch.float64) -> torch.Tensor:
        """A[j, i] = 1 si el tramo i drena en el tramo j."""
        A = torch.zeros(self.n, self.n, dtype=dtype)
        for i, j in enumerate(self.aguas_abajo):
            if j >= 0:
                A[j, i] = 1.0
        return A

    def area_drenaje_km2(self) -> np.ndarray:
        """Área acumulada aguas arriba de la salida de cada tramo."""
        acum = self.area_local_km2.copy()
        for i in range(self.n):  # orden topológico: aguas arriba primero
            j = self.aguas_abajo[i]
            if j >= 0:
                acum[j] += acum[i]
        return acum

    def aguas_arriba_de(self, j: int) -> np.ndarray:
        """Máscara booleana de los tramos que drenan (directa o indirectamente) a j, incluido j."""
        mask = np.zeros(self.n, dtype=bool)
        mask[j] = True
        for i in range(j):
            k = i
            # los índices crecen aguas abajo: si k supera j ya no puede llegar a j
            while 0 <= k < j:
                k = self.aguas_abajo[k]
            mask[i] = k == j
        return mask

    def laplaciano(self, dtype=torch.float64) -> torch.Tensor:
        """Operador de diferencias sobre aristas (D) tal que ||D m||² penaliza
        cambios bruscos del parámetro entre tramos conectados.

        Es el análogo, sobre el grafo, de la regularización de suavidad de
        primer orden usada en inversión geofísica (p. ej. SimPEG Smallness +
        SmoothDeriv).
        """
        filas = []
        for i, j in enumerate(self.aguas_abajo):
            if j >= 0:
                fila = torch.zeros(self.n, dtype=dtype)
                fila[i], fila[j] = -1.0, 1.0
                filas.append(fila)
        if not filas:
            return torch.zeros(0, self.n, dtype=dtype)
        return torch.stack(filas)

    def atributos(self) -> np.ndarray:
        """Matriz de atributos estáticos por tramo para parametrizaciones neuronales."""
        A = self.area_drenaje_km2()
        return np.column_stack(
            [
                np.log(self.pendiente),
                np.log(A),
                np.log(self.ancho_m),
                np.log(self.longitud_m),
            ]
        )


# ----------------------------------------------------------------------
def red_sintetica(
    n_tramos: int = 60,
    semilla: int = 0,
    longitud_media_km: float = 18.0,
) -> RedFluvial:
    """Genera un árbol fluvial binario aleatorio con geometría hidráulica plausible.

    El árbol crece desde la salida agregando tributarios a tramos que aún
    tienen menos de dos afluentes. Luego se reordena para cumplir el orden
    topológico (aguas arriba → índice menor).

    Las relaciones ancho–área y pendiente–área siguen leyes de potencia de
    geometría hidráulica (Leopold & Maddock, 1953) con coeficientes
    ilustrativos; NO están calibradas para Colombia.
    """
    rng = np.random.default_rng(semilla)
    padre = [-1]
    n_hijos = [0]
    for k in range(1, n_tramos):
        candidatos = [i for i in range(k) if n_hijos[i] < 2]
        p = int(rng.choice(candidatos))
        padre.append(p)
        n_hijos.append(0)
        n_hijos[p] += 1

    # Profundidad desde la salida; ordenar de mayor a menor profundidad.
    prof = np.zeros(n_tramos, dtype=int)
    for k in range(1, n_tramos):
        prof[k] = prof[padre[k]] + 1
    orden = np.lexsort((np.arange(n_tramos), -prof))  # más profundo primero
    nuevo = np.empty(n_tramos, dtype=int)
    nuevo[orden] = np.arange(n_tramos)
    aguas_abajo = np.full(n_tramos, -1)
    for viejo in range(n_tramos):
        if padre[viejo] >= 0:
            aguas_abajo[nuevo[viejo]] = nuevo[padre[viejo]]

    area_local = rng.lognormal(mean=np.log(250.0), sigma=0.5, size=n_tramos)
    longitud = rng.lognormal(mean=np.log(longitud_media_km * 1e3), sigma=0.35, size=n_tramos)

    red_tmp = RedFluvial(
        aguas_abajo=aguas_abajo,
        longitud_m=longitud,
        pendiente=np.full(n_tramos, 1e-3),
        ancho_m=np.full(n_tramos, 10.0),
        area_local_km2=area_local,
    )
    A = red_tmp.area_drenaje_km2()
    ancho = 2.5 * A**0.45
    pendiente = np.clip(0.03 * A ** (-0.45) * rng.lognormal(0, 0.25, n_tramos), 2e-4, 2e-2)
    return RedFluvial(
        aguas_abajo=aguas_abajo,
        longitud_m=longitud,
        pendiente=pendiente,
        ancho_m=ancho,
        area_local_km2=area_local,
    )
