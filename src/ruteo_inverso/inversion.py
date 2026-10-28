"""Problema inverso: estimar log(n) por tramo a partir de caudales en estaciones.

Dos estrategias, ambas tomadas del flujo de trabajo de inversión geofísica:

1. ``invertir_tikhonov`` — inversión determinística regularizada
       φ(m) = φ_d(m) + β φ_m(m)
       φ_d = || W_d (P G(m) − d_obs) ||²,   W_d = diag(1/σ)
       φ_m = α_s ||m − m_ref||² + α_x ||D (m − m_ref)||²
   con enfriamiento de β y criterio de parada por discrepancia
   (φ_d ≤ N + 2√(2N)), igual que las directivas BetaSchedule / TargetMisfit
   de SimPEG.

2. ``invertir_neuronal`` — inversión profunda no supervisada: una red
   f_θ(atributos) → log(n) se entrena SOLO con el desajuste de datos a
   través del operador directo diferenciable (análogo al MT‑1D guiado por
   física con operador directo diferenciable). Es la estrategia de
   Bindas et al. (2024) y permite predecir n en tramos sin aforo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch
import torch.nn as nn

from .ruteo import MuskingumCunge, promedio_diario

LOG_N_MIN = float(torch.log(torch.tensor(0.015)))
LOG_N_MAX = float(torch.log(torch.tensor(0.20)))


@dataclass
class ProblemaInverso:
    modelo: MuskingumCunge
    q_lat: torch.Tensor          # (T, N) aporte lateral
    estaciones: list[int]        # índices de tramos aforados
    pasos_por_dia: int
    d_obs: torch.Tensor          # (dias, G) caudal medio diario observado
    sigma: torch.Tensor          # (dias, G) desviación estándar del error
    dias_calentamiento: int = 3  # se excluyen del desajuste (estado inicial)

    def predecir(self, log_n: torch.Tensor) -> torch.Tensor:
        O = self.modelo.rutear(log_n, self.q_lat)
        return promedio_diario(O, self.pasos_por_dia)[:, self.estaciones]

    def residuo_ponderado(self, log_n: torch.Tensor) -> torch.Tensor:
        r = (self.predecir(log_n) - self.d_obs) / self.sigma
        return r[self.dias_calentamiento:].reshape(-1)

    @property
    def n_datos(self) -> int:
        return (self.d_obs.shape[0] - self.dias_calentamiento) * self.d_obs.shape[1]

    def phi_d(self, log_n: torch.Tensor) -> torch.Tensor:
        return (self.residuo_ponderado(log_n) ** 2).sum()


def sintetizar_observaciones(modelo: MuskingumCunge, log_n_true: torch.Tensor,
                             q_lat: torch.Tensor, estaciones: list[int],
                             pasos_por_dia: int, ruido_rel: float = 0.05,
                             piso_m3s: float = 0.5, semilla: int = 0):
    """Datos sintéticos con error multiplicativo + piso absoluto."""
    g = torch.Generator().manual_seed(semilla)
    with torch.no_grad():
        O = modelo.rutear(log_n_true, q_lat)
        d = promedio_diario(O, pasos_por_dia)[:, estaciones]
        sigma = ruido_rel * d.abs() + piso_m3s
        d_obs = d + sigma * torch.randn(d.shape, generator=g, dtype=d.dtype)
    return d_obs, sigma


# ----------------------------------------------------------------------
@dataclass
class ResultadoInversion:
    log_n: torch.Tensor
    beta: float
    phi_d: float
    phi_m: float
    historial: list[dict] = field(default_factory=list)


def _phi_m(log_n, m_ref, D, alpha_s, alpha_x):
    dm = log_n - m_ref
    return alpha_s * (dm ** 2).sum() + alpha_x * ((D @ dm) ** 2).sum()


def estimar_beta0(problema: ProblemaInverso, m_ref: torch.Tensor, D: torch.Tensor,
                  alpha_s: float, alpha_x: float, razon: float = 10.0,
                  semilla: int = 0) -> float:
    """β₀ = razón · ||J v||² / (vᵀ W_mᵀW_m v) para una dirección aleatoria v.

    Equivalente a la directiva BetaEstimate_ByEig de SimPEG con una sola
    iteración de potencia: equilibra la curvatura del término de datos y la
    del regularizador al inicio de la inversión.
    """
    g = torch.Generator().manual_seed(semilla)
    v = torch.randn(m_ref.shape, generator=g, dtype=m_ref.dtype)
    v = v / v.norm()
    _, Jv = torch.func.jvp(problema.residuo_ponderado, (m_ref,), (v,))
    Wm2 = alpha_s * torch.eye(len(v), dtype=v.dtype) + alpha_x * D.T @ D
    return razon * float((Jv ** 2).sum() / (v @ Wm2 @ v))


def invertir_tikhonov(
    problema: ProblemaInverso,
    m_ref: torch.Tensor,
    D: torch.Tensor,
    alpha_s: float = 1.0,
    alpha_x: float = 1.0,
    beta0: float | None = None,
    razon_beta0: float = 10.0,
    factor_enfriamiento: float = 4.0,
    chi_objetivo: float = 1.0,
    max_etapas: int = 8,
    iter_por_etapa: int = 25,
    tol_estancamiento: float = 0.05,
    tolerancia_sd: float = 2.0,
) -> ResultadoInversion:
    """Inversión de Tikhonov con enfriamiento de β y principio de discrepancia.

    Se optimiza en la variable acotada log(n) ∈ [log 0.015, log 0.20] mediante
    una reparametrización sigmoide, para que el operador directo siempre sea
    físicamente válido.
    """
    m_ref = m_ref.detach().clone()

    def a_log_n(u):
        return LOG_N_MIN + (LOG_N_MAX - LOG_N_MIN) * torch.sigmoid(u)

    p = ((m_ref - LOG_N_MIN) / (LOG_N_MAX - LOG_N_MIN)).clamp(1e-4, 1 - 1e-4)
    u = torch.log(p / (1 - p)).clone().requires_grad_(True)

    if beta0 is None:
        beta0 = estimar_beta0(problema, m_ref, D, alpha_s, alpha_x, razon=razon_beta0)
    beta = beta0
    # φ_d ~ χ²(N): media N, desviación √(2N). Exigir φ_d ≤ N sin tolerancia
    # sobreajusta el ruido la mitad de las veces.
    objetivo = chi_objetivo * problema.n_datos + tolerancia_sd * (2 * problema.n_datos) ** 0.5
    historial = []

    for etapa in range(max_etapas):
        opt = torch.optim.LBFGS([u], lr=1.0, max_iter=iter_por_etapa,
                                line_search_fn="strong_wolfe")

        def cierre(opt=opt, beta=beta):
            opt.zero_grad()
            ln = a_log_n(u)
            f = problema.phi_d(ln) + beta * _phi_m(ln, m_ref, D, alpha_s, alpha_x)
            f.backward()
            return f

        opt.step(cierre)
        with torch.no_grad():
            ln = a_log_n(u)
            pd = float(problema.phi_d(ln))
            pm = float(_phi_m(ln, m_ref, D, alpha_s, alpha_x))
        historial.append({"etapa": etapa, "beta": beta, "phi_d": pd, "phi_m": pm,
                          "objetivo": objetivo})
        if pd <= objetivo:
            break
        # estancamiento: bajar β ya no mejora el ajuste (el ruido o el modelo lo limitan)
        if etapa > 0 and historial[-2]["phi_d"] - pd < tol_estancamiento * historial[-2]["phi_d"]:
            historial[-1]["parada"] = "estancamiento"
            break
        beta /= factor_enfriamiento

    return ResultadoInversion(a_log_n(u).detach(), beta, pd, pm, historial)


# ----------------------------------------------------------------------
class ParametrizacionNeuronal(nn.Module):
    """f_θ: atributos del tramo → log(n) acotado."""

    def __init__(self, n_atributos: int, oculto: int = 32):
        super().__init__()
        self.red = nn.Sequential(
            nn.Linear(n_atributos, oculto), nn.Tanh(),
            nn.Linear(oculto, oculto), nn.Tanh(),
            nn.Linear(oculto, 1),
        ).double()
        self.register_buffer("media", torch.zeros(n_atributos, dtype=torch.float64))
        self.register_buffer("escala", torch.ones(n_atributos, dtype=torch.float64))

    def ajustar_normalizacion(self, X: torch.Tensor) -> None:
        self.media.copy_(X.mean(0))
        self.escala.copy_(X.std(0).clamp_min(1e-8))

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        z = self.red((X - self.media) / self.escala).squeeze(-1)
        return LOG_N_MIN + (LOG_N_MAX - LOG_N_MIN) * torch.sigmoid(z)


def invertir_neuronal(problema: ProblemaInverso, atributos: torch.Tensor,
                      epocas: int = 300, lr: float = 1e-2, semilla: int = 0,
                      peso_l2: float = 1e-4) -> tuple[ParametrizacionNeuronal, list[float]]:
    """Inversión profunda no supervisada (sin etiquetas de n)."""
    torch.manual_seed(semilla)
    f = ParametrizacionNeuronal(atributos.shape[1])
    f.ajustar_normalizacion(atributos)
    opt = torch.optim.Adam(f.parameters(), lr=lr, weight_decay=peso_l2)
    historial = []
    for _ in range(epocas):
        opt.zero_grad()
        perdida = problema.phi_d(f(atributos)) / problema.n_datos
        perdida.backward()
        opt.step()
        historial.append(perdida.item())
    return f, historial
