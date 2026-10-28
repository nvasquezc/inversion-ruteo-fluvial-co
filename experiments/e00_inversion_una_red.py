"""E00 — Inversión de Tikhonov en una sola red sintética (verificación rápida)."""

import numpy as np
import torch

from ruteo_inverso.forzamiento import aporte_lateral_sintetico, rugosidad_verdadera
from ruteo_inverso.inversion import ProblemaInverso, invertir_tikhonov, sintetizar_observaciones
from ruteo_inverso.red import red_sintetica
from ruteo_inverso.ruteo import MuskingumCunge, caudal_referencia

red = red_sintetica(60, semilla=0)
q = aporte_lateral_sintetico(red, dias=40, pasos_por_dia=24, semilla=0)
modelo = MuskingumCunge(red, caudal_referencia(red, q), dt_s=3600.0)
log_n_verdadero = rugosidad_verdadera(red, semilla=0)

A = red.area_drenaje_km2()
estaciones = [59] + [int(i) for i in np.argsort(-A) if i != 59][:2]
d_obs, sigma = sintetizar_observaciones(modelo, log_n_verdadero, q, estaciones, 24, semilla=0)
problema = ProblemaInverso(modelo, q, estaciones, 24, d_obs, sigma, dias_calentamiento=3)

m_ref = torch.full((60,), float(np.log(0.035)), dtype=torch.float64)
res = invertir_tikhonov(problema, m_ref, red.laplaciano())
rmse = lambda m: float(((m - log_n_verdadero) ** 2).mean().sqrt())
print("estaciones:", estaciones, " N datos:", problema.n_datos)
print("etapas (beta, phi_d):", [(round(h["beta"], 2), round(h["phi_d"], 1)) for h in res.historial])
print(f"RMSE referencia {rmse(m_ref):.3f} -> invertido {rmse(res.log_n):.3f}")


# --- Fase 7: resolución y diseño ---------------------------------------
from ruteo_inverso.resolucion import (diseno_codicioso, informacion_por_candidato,
                                      jacobiano_diario, matriz_regularizacion, resolucion)
from ruteo_inverso.ruteo import promedio_diario

Wm2 = matriz_regularizacion(red.n, red.laplaciano(), 1.0, 1.0)
J = jacobiano_diario(modelo, res.log_n, q, 24, dias_calentamiento=3)
with torch.no_grad():
    Qd = promedio_diario(modelo.rutear(res.log_n, q), 24)[3:]
sig = 0.05 * Qd.abs() + 0.5
R = resolucion(J[:, estaciones], sig[:, estaciones], Wm2, res.beta)
print(f"suma diag(R) = {float(R.diag_R.sum()):.1f} de {red.n};  tramos con diag(R) > 0.1: {int((R.diag_R > 0.1).sum())}")

F = informacion_por_candidato(J, sig)
nuevas, _ = diseno_codicioso(F, R.H, 4, excluir=estaciones, criterio="D")
print("4 estaciones D-óptimas:", nuevas)