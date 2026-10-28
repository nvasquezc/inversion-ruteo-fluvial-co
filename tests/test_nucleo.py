"""Pruebas del núcleo: conservación de masa, estructura de la red, gradientes y resolución."""

import numpy as np
import pytest
import torch

from ruteo_inverso import (
    MuskingumCunge,
    ProblemaInverso,
    aporte_lateral_sintetico,
    caudal_referencia,
    diseno_codicioso,
    informacion_por_candidato,
    invertir_neuronal,
    jacobiano_diario,
    matriz_regularizacion,
    promedio_diario,
    red_sintetica,
    resolucion,
    rugosidad_verdadera,
    sintetizar_observaciones,
)
from ruteo_inverso.red import RedFluvial


@pytest.fixture(scope="module")
def caso():
    red = red_sintetica(25, semilla=3, longitud_media_km=12.0)
    q = aporte_lateral_sintetico(red, dias=12, pasos_por_dia=24, semilla=3)
    modelo = MuskingumCunge(red, caudal_referencia(red, q), dt_s=3600.0)
    ln = rugosidad_verdadera(red, 3)
    return red, q, modelo, ln


# ---------------------------------------------------------------- red
def test_orden_topologico_invalido():
    with pytest.raises(ValueError):
        RedFluvial(aguas_abajo=[-1, 0], longitud_m=[1, 1], pendiente=[1, 1],
                   ancho_m=[1, 1], area_local_km2=[1, 1])


def test_adyacencia_triangular_inferior(caso):
    red, *_ = caso
    A = red.adyacencia()
    assert torch.all(torch.triu(A) == 0)
    assert int(A.sum()) == red.n - 1  # árbol con una salida


def test_area_drenaje_salida_es_total(caso):
    red, *_ = caso
    salida = int(np.where(red.aguas_abajo < 0)[0][0])
    assert np.isclose(red.area_drenaje_km2()[salida], red.area_local_km2.sum())


def test_aguas_arriba(caso):
    red, *_ = caso
    salida = int(np.where(red.aguas_abajo < 0)[0][0])
    assert red.aguas_arriba_de(salida).all()


# ---------------------------------------------------- conservación de masa
def test_conservacion_masa_por_tramo(caso):
    """Continuidad discreta exacta: Δt·½Σ[(I_t+I_{t+1})−(O_t+O_{t+1})] = S_T − S_0."""
    red, q, modelo, ln = caso
    O, I, S = modelo.rutear(ln, q, devolver_estado=True)
    lhs = modelo.dt * 0.5 * ((I[:-1] + I[1:]) - (O[:-1] + O[1:])).sum(0)
    rhs = S[-1] - S[0]
    volumen = modelo.dt * I.sum(0)
    assert torch.max(torch.abs(lhs - rhs) / volumen) < 1e-10


def test_conservacion_masa_red(caso):
    """Lo que entra lateralmente = lo que sale por la salida + cambio de almacenamiento total."""
    red, q, modelo, ln = caso
    O, I, S = modelo.rutear(ln, q, devolver_estado=True)
    salida = int(np.where(red.aguas_abajo < 0)[0][0])
    entra = modelo.dt * 0.5 * (q[:-1] + q[1:]).sum()
    sale = modelo.dt * 0.5 * (O[:-1, salida] + O[1:, salida]).sum()
    dS = (S[-1] - S[0]).sum()
    assert abs(float(entra - sale - dS)) / float(entra) < 1e-10


def test_estado_estacionario(caso):
    red, q, modelo, ln = caso
    q_cte = q[:1].repeat(48, 1)
    O = modelo.rutear(ln, q_cte)
    assert torch.allclose(O[0], O[-1], rtol=1e-10)


def test_caudales_no_negativos(caso):
    red, q, modelo, ln = caso
    assert modelo.diagnostico_courant(ln)["frac_c2_negativo"] == 0.0
    assert float(modelo.rutear(ln, q).min()) >= 0.0


# ------------------------------------------------------------- gradientes
def test_gradiente_vs_diferencias_finitas(caso):
    red, q, modelo, ln = caso
    est = [red.n - 1]
    d, s = sintetizar_observaciones(modelo, ln, q, est, 24)
    P = ProblemaInverso(modelo, q, est, 24, d, s)
    m = ln + 0.1
    m.requires_grad_(True)
    P.phi_d(m).backward()
    g = m.grad.clone()
    v = torch.randn(red.n, dtype=torch.float64, generator=torch.Generator().manual_seed(0))
    h = 1e-6
    with torch.no_grad():
        fd = (P.phi_d(m + h * v) - P.phi_d(m - h * v)) / (2 * h)
    assert torch.isclose(fd, g @ v, rtol=1e-5)


def test_jacobiano_forma_y_causalidad(caso):
    """Un tramo solo puede ser sensible a los parámetros de sí mismo y de su red aguas arriba."""
    red, q, modelo, ln = caso
    J = jacobiano_diario(modelo, ln, q, 24, 2)
    assert J.shape == (10, red.n, red.n)
    for j in range(red.n):
        fuera = ~torch.as_tensor(red.aguas_arriba_de(j))
        assert torch.all(J[:, j, fuera] == 0)


# ------------------------------------------------------------- resolución
def test_resolucion_acotada(caso):
    red, q, modelo, ln = caso
    J = jacobiano_diario(modelo, ln, q, 24, 2)
    Qd = promedio_diario(modelo.rutear(ln, q), 24)[2:]
    sigma = 0.05 * Qd + 0.5
    Wm2 = matriz_regularizacion(red.n, red.laplaciano(), 1.0, 1.0)
    est = [red.n - 1]
    r = resolucion(J[:, est], sigma[:, est], Wm2, beta=1.0)
    assert torch.all(r.diag_R > -1e-10) and torch.all(r.diag_R < 1 + 1e-10)
    # más estaciones → más resolución total
    r_todas = resolucion(J, sigma, Wm2, beta=1.0)
    assert r_todas.diag_R.sum() > r.diag_R.sum()


def test_diseno_d_monotono(caso):
    red, q, modelo, ln = caso
    J = jacobiano_diario(modelo, ln, q, 24, 2)
    Qd = promedio_diario(modelo.rutear(ln, q), 24)[2:]
    F = informacion_por_candidato(J, 0.05 * Qd + 0.5)
    H0 = matriz_regularizacion(red.n, red.laplaciano(), 1.0, 1.0)
    elegidas, valores = diseno_codicioso(F, H0, 3, excluir=[red.n - 1])
    assert len(set(elegidas)) == 3 and red.n - 1 not in elegidas
    assert all(b >= a for a, b in zip(valores, valores[1:]))


def test_inversion_neuronal_reduce_desajuste(caso):
    red, q, modelo, ln = caso
    est = [red.n - 1, int(np.argsort(-red.area_drenaje_km2())[1])]
    d, s = sintetizar_observaciones(modelo, ln, q, est, 24)
    P = ProblemaInverso(modelo, q, est, 24, d, s)
    X = torch.as_tensor(red.atributos(), dtype=torch.float64)
    f, hist = invertir_neuronal(P, X, epocas=40, lr=2e-2)
    assert hist[-1] < hist[0]
