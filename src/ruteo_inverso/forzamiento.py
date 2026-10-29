"""Forzamientos sintéticos (aporte lateral) y campos "verdaderos" de rugosidad.

Solo para experimentos sintéticos controlados. En datos reales el aporte
lateral vendrá de un modelo lluvia–escorrentía (p. ej. LSTM entrenado en
CAMELS‑COL) forzado con CHIRPS/MSWX.
"""

from __future__ import annotations

import numpy as np
import torch

from .red import RedFluvial


def aporte_lateral_sintetico(
    red: RedFluvial,
    dias: int = 40,
    pasos_por_dia: int = 24,
    semilla: int = 0,
    prob_tormenta: float = 0.25,
    coef_escorrentia: float = 0.35,
    k_embalse_dias: float = 1.5,
    caudal_base_mm_dia: float = 1.0,
) -> torch.Tensor:
    """Aporte lateral horario (T, N) en m³/s.

    Tormentas a escala de cuenca con cobertura espacial parcial, convertidas a
    escorrentía por un embalse lineal en cada subcuenca. La variabilidad
    espacio‑temporal es necesaria para que los parámetros de ruteo sean, en
    principio, identificables.
    """
    rng = np.random.default_rng(semilla)
    T = dias * pasos_por_dia
    N = red.n
    lluvia = np.zeros((T, N))  # mm por paso
    for d in range(dias):
        if rng.random() < prob_tormenta:
            cobertura = rng.random(N) < rng.uniform(0.3, 1.0)
            total_mm = rng.gamma(shape=2.0, scale=12.0)
            inicio = d * pasos_por_dia + rng.integers(0, pasos_por_dia // 2)
            dur = int(rng.integers(3, 10))
            perfil = np.hanning(dur + 2)[1:-1]
            perfil = perfil / perfil.sum()
            fin = min(inicio + dur, T)
            lluvia[inicio:fin, cobertura] += (total_mm * perfil[: fin - inicio])[:, None] * \
                rng.lognormal(0, 0.3, cobertura.sum())[None, :]

    k = k_embalse_dias * pasos_por_dia
    alpha = 1.0 / k
    almacen = np.zeros(N)
    escorrentia_mm = np.zeros((T, N))
    base_mm_paso = caudal_base_mm_dia / pasos_por_dia
    for t in range(T):
        almacen = almacen + coef_escorrentia * lluvia[t]
        salida = alpha * almacen
        almacen = almacen - salida
        escorrentia_mm[t] = salida + base_mm_paso

    dt_s = 86400.0 / pasos_por_dia
    area_m2 = red.area_local_km2 * 1e6
    q = escorrentia_mm * 1e-3 * area_m2[None, :] / dt_s
    return torch.as_tensor(q, dtype=torch.float64)


def rugosidad_verdadera(red: RedFluvial, semilla: int = 0) -> torch.Tensor:
    """Campo log(n) "verdadero" dependiente de atributos + ruido correlacionado en la red.

    n crece con la pendiente (cauces de montaña más rugosos) y tiene un
    componente aleatorio suavizado a lo largo de la red. Valores dentro del
    rango típico 0.02–0.12 (Chow, 1959).
    """
    rng = np.random.default_rng(semilla + 1000)
    z = rng.normal(0, 1, red.n)
    # suavizado: promedio con vecinos aguas abajo (dos pasadas)
    for _ in range(2):
        z_s = z.copy()
        for i, j in enumerate(red.aguas_abajo):
            if j >= 0:
                z_s[i] = 0.5 * z[i] + 0.5 * z[j]
        z = z_s / z_s.std()
    log_n = np.log(0.035) + 0.25 * np.log(red.pendiente / 2e-3) + 0.25 * z
    log_n = np.clip(log_n, np.log(0.02), np.log(0.12))
    return torch.as_tensor(log_n, dtype=torch.float64)
