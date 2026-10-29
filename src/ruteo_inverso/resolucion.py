"""Sensibilidad, resolución e incertidumbre linealizada; diseño de la red de aforos.

Herramientas estándar de inversión geofísica trasladadas al ruteo fluvial:

* Jacobiano J = ∂d/∂m obtenido por diferenciación automática (modo forward,
  pocos parámetros y muchos datos).
* Matriz de resolución del modelo (Menke, 2012; Aster et al., 2018):
      H = Jᵀ W_d² J + β W_mᵀ W_m
      R = H⁻¹ Jᵀ W_d² J
  diag(R) ≈ 1 → el parámetro del tramo está resuelto por los datos;
  diag(R) ≈ 0 → lo determina la regularización (no identificable).
* Covarianza posterior linealizada C ≈ H⁻¹ (aproximación de Laplace /
  Gauss–Newton, válida solo localmente alrededor de m̂).
* Diseño experimental óptimo (bayesiano‑lineal) codicioso: qué tramo
  aforar a continuación para maximizar log det(H) (criterio D) o minimizar
  tr(H⁻¹) (criterio A). Es el análogo del diseño de adquisición en
  geofísica, aplicado a dónde instalar nuevas estaciones hidrométricas.

ADVERTENCIA: todo lo anterior es un análisis LINEALIZADO. Para afirmaciones
globales de identificabilidad se debe complementar con muestreo (p. ej.
MCMC/ensembles), según el protocolo de docs/protocolo.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.func import jacfwd

from .ruteo import MuskingumCunge, promedio_diario


def jacobiano_diario(modelo: MuskingumCunge, log_n: torch.Tensor, q_lat: torch.Tensor,
                     pasos_por_dia: int, dias_calentamiento: int = 3) -> torch.Tensor:
    """∂Q̄_diario/∂log(n) para TODOS los tramos como posibles estaciones.

    Devuelve tensor (dias, N_tramos_obs, N_parametros).
    """
    def f(m):
        O = modelo.rutear(m, q_lat)
        return promedio_diario(O, pasos_por_dia)[dias_calentamiento:]

    return jacfwd(f)(log_n)


def matriz_regularizacion(n: int, D: torch.Tensor, alpha_s: float, alpha_x: float) -> torch.Tensor:
    """W_mᵀ W_m = α_s I + α_x DᵀD."""
    return alpha_s * torch.eye(n, dtype=D.dtype) + alpha_x * D.T @ D


@dataclass
class Resolucion:
    R: torch.Tensor
    diag_R: torch.Tensor
    sd_posterior: torch.Tensor
    H: torch.Tensor


def resolucion(J_est: torch.Tensor, sigma: torch.Tensor, Wm2: torch.Tensor,
               beta: float) -> Resolucion:
    """J_est: (dias, G, P) Jacobiano en estaciones; sigma: (dias, G)."""
    Jw = (J_est / sigma[..., None]).reshape(-1, J_est.shape[-1])
    JtJ = Jw.T @ Jw
    H = JtJ + beta * Wm2
    H_inv = torch.linalg.inv(H)
    R = H_inv @ JtJ
    return Resolucion(R=R, diag_R=torch.diagonal(R), sd_posterior=torch.sqrt(torch.diagonal(H_inv)), H=H)


def informacion_por_candidato(J_todos: torch.Tensor, sigma_todos: torch.Tensor) -> torch.Tensor:
    """Matriz de información de Fisher F_c = J_cᵀ W J_c para cada tramo candidato c.

    J_todos: (dias, N, P); sigma_todos: (dias, N). Devuelve (N, P, P).
    """
    Jw = J_todos / sigma_todos[..., None]
    return torch.einsum("dcp,dcq->cpq", Jw, Jw)


def diseno_codicioso(F: torch.Tensor, H_base: torch.Tensor, k: int,
                     excluir: list[int] | None = None, criterio: str = "D") -> tuple[list[int], list[float]]:
    """Agrega k estaciones una a una maximizando la ganancia de información.

    criterio "D": maximiza log det(H). criterio "A": minimiza tr(H⁻¹).
    Devuelve (estaciones elegidas, valor del criterio después de cada adición).
    """
    elegidas: list[int] = []
    excluidas = set(excluir or [])
    H = H_base.clone()
    valores = []
    for _ in range(k):
        mejor, mejor_val = None, None
        for c in range(F.shape[0]):
            if c in excluidas or c in elegidas:
                continue
            Hc = H + F[c]
            if criterio == "D":
                val = torch.linalg.slogdet(Hc)[1]
                mejora = mejor_val is None or val > mejor_val
            elif criterio == "A":
                val = torch.trace(torch.linalg.inv(Hc))
                mejora = mejor_val is None or val < mejor_val
            else:
                raise ValueError("criterio debe ser 'D' o 'A'")
            if mejora:
                mejor, mejor_val = c, val
        if mejor is None:
            break
        elegidas.append(mejor)
        H = H + F[mejor]
        valores.append(float(mejor_val))
    return elegidas, valores
