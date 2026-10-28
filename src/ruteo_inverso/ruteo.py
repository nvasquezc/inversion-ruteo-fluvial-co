"""Operador directo: ruteo Muskingum–Cunge diferenciable sobre una red fluvial.

Este es el "operador directo" G(m) del problema inverso, en el mismo sentido
que el operador de impedancia en MT‑1D o la ecuación de onda en FWI:

    d = P · G(m; q) + ε

donde m = log(n) es el coeficiente de rugosidad de Manning por tramo, q es
el aporte lateral de cada subcuenca, P selecciona las estaciones de aforo y
promedia a escala diaria, y ε es el error de observación.

Conservación de masa
--------------------
Con coeficientes constantes en el tiempo (modo lineal alrededor de un
caudal de referencia), el esquema de Muskingum satisface EXACTAMENTE la
ecuación de continuidad discreta

    Δt · ½[(I_t + I_{t+1}) − (O_t + O_{t+1})] = S_{t+1} − S_t,
    S = K [X I + (1 − X) O],

porque c0 + c1 + c2 = 1. Es decir, la conservación de masa es una propiedad
de la arquitectura (restricción dura), no un término de penalización. La
prueba ``tests/test_nucleo.py`` lo verifica a precisión de máquina.

Referencias: Cunge (1969); Bindas et al. (2024, WRR, doi:10.1029/2023WR035337)
para la versión diferenciable con n aprendido por red neuronal.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from .red import RedFluvial


@dataclass
class Coeficientes:
    c0: torch.Tensor
    c1: torch.Tensor
    c2: torch.Tensor
    K: torch.Tensor
    X: torch.Tensor
    celeridad: torch.Tensor


class MuskingumCunge:
    """Ruteo Muskingum–Cunge lineal (coeficientes fijos en el tiempo).

    Parámetros
    ----------
    red : RedFluvial
    q_ref : caudal de referencia por tramo [m³/s] usado para linealizar la
        celeridad (típicamente el caudal medio). Tensor (N,).
    dt_s : paso de tiempo interno [s].
    """

    def __init__(self, red: RedFluvial, q_ref: torch.Tensor, dt_s: float = 3600.0,
                 dtype=torch.float64):
        self.red = red
        self.dtype = dtype
        self.dt = float(dt_s)
        self.A = red.adyacencia(dtype)
        self.I_N = torch.eye(red.n, dtype=dtype)
        self.L = torch.as_tensor(red.longitud_m, dtype=dtype)
        self.S0 = torch.as_tensor(red.pendiente, dtype=dtype)
        self.B = torch.as_tensor(red.ancho_m, dtype=dtype)
        self.q_ref = torch.as_tensor(q_ref, dtype=dtype).clamp_min(1e-3)

    # ------------------------------------------------------------------
    def coeficientes(self, log_n: torch.Tensor) -> Coeficientes:
        n = torch.exp(log_n)
        Q = self.q_ref
        # Canal rectangular ancho: Q = (1/n) B h^{5/3} S^{1/2}
        h = (n * Q / (self.B * torch.sqrt(self.S0))) ** 0.6
        v = Q / (self.B * h)
        c = (5.0 / 3.0) * v  # celeridad cinemática
        K = self.L / c
        X = 0.5 * (1.0 - Q / (self.B * self.S0 * c * self.L))
        # 0 <= X <= 0.5 y c0 >= 0 (evita respuestas negativas inmediatas)
        X = torch.clamp(X, min=0.0, max=0.5)
        X = torch.minimum(X, self.dt / (2.0 * K))
        D = 2.0 * K * (1.0 - X) + self.dt
        c0 = (self.dt - 2.0 * K * X) / D
        c1 = (self.dt + 2.0 * K * X) / D
        c2 = (2.0 * K * (1.0 - X) - self.dt) / D
        return Coeficientes(c0, c1, c2, K, X, c)

    def diagnostico_courant(self, log_n: torch.Tensor) -> dict:
        """Fracción de tramos donde c2 < 0 (Δt > 2K(1−X)).

        La masa se conserva igual, pero la solución puede oscilar; si la
        fracción es alta conviene reducir ``dt_s``.
        """
        co = self.coeficientes(log_n)
        return {
            "frac_c2_negativo": float((co.c2 < 0).double().mean()),
            "K_min_h": float(co.K.min() / 3600),
            "K_max_h": float(co.K.max() / 3600),
        }

    # ------------------------------------------------------------------
    def rutear(self, log_n: torch.Tensor, q_lat: torch.Tensor,
               devolver_estado: bool = False):
        """Rutea el aporte lateral ``q_lat`` (T, N) [m³/s].

        Devuelve el caudal de salida O (T, N). Con ``devolver_estado=True``
        devuelve también la entrada I y el almacenamiento S.
        El estado inicial es el estacionario correspondiente a q_lat[0].
        """
        q_lat = q_lat.to(self.dtype)
        co = self.coeficientes(log_n)
        A, I_N = self.A, self.I_N
        M = I_N - co.c0[:, None] * A  # triangular inferior con diagonal unitaria
        M_inv = torch.linalg.solve_triangular(M, I_N, upper=False, unitriangular=True)
        acum = torch.linalg.solve_triangular(I_N - A, I_N, upper=False, unitriangular=True)

        O_prev = acum @ q_lat[0]
        I_prev = A @ O_prev + q_lat[0]
        salidas, entradas = [O_prev], [I_prev]
        for t in range(1, q_lat.shape[0]):
            rhs = co.c0 * q_lat[t] + co.c1 * I_prev + co.c2 * O_prev
            O_t = M_inv @ rhs
            I_t = A @ O_t + q_lat[t]
            salidas.append(O_t)
            entradas.append(I_t)
            O_prev, I_prev = O_t, I_t
        O = torch.stack(salidas)
        if not devolver_estado:
            return O
        I = torch.stack(entradas)
        S = co.K * (co.X * I + (1.0 - co.X) * O)
        return O, I, S


def promedio_diario(Q: torch.Tensor, pasos_por_dia: int) -> torch.Tensor:
    """Agrega (T, ...) a medias diarias (T // pasos_por_dia, ...).

    Simula que las estaciones (p. ej. IDEAM / CAMELS‑COL) reportan caudal
    medio diario aunque el ruteo se resuelva a escala horaria.
    """
    T = (Q.shape[0] // pasos_por_dia) * pasos_por_dia
    return Q[:T].reshape(T // pasos_por_dia, pasos_por_dia, *Q.shape[1:]).mean(dim=1)


def caudal_referencia(red: RedFluvial, q_lat: torch.Tensor) -> torch.Tensor:
    """Caudal medio acumulado por tramo, usado para linealizar la celeridad."""
    A = red.adyacencia(torch.float64)
    I_N = torch.eye(red.n, dtype=torch.float64)
    acum = torch.linalg.solve_triangular(I_N - A, I_N, upper=False, unitriangular=True)
    return acum @ q_lat.to(torch.float64).mean(dim=0)