"""E01 — Identificabilidad de la rugosidad y diseño de la red de aforos (sintético).

Preguntas (falsables)
---------------------
H-a  La diagonal de la matriz de resolución linealizada, calculada en el
     modelo de referencia (sin conocer la verdad), predice qué tramos se
     recuperan bien: correlación de Spearman NEGATIVA entre diag(R) y el
     error absoluto |m̂ − m_true|.
H-b  Agregar k estaciones con diseño D‑óptimo (calculado en el modelo de
     referencia) reduce el RMSE de log(n) más que (i) la heurística
     tradicional de aforar los ríos de mayor área de drenaje y (ii) ubicaciones
     aleatorias.

Ambas hipótesis pueden fallar; el script reporta lo que salga.

Uso:  uv run python experiments/e01_identificabilidad_sintetica.py --redes 12 --aleatorios 5
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from scipy import stats

from ruteo_inverso import (
    MuskingumCunge,
    ProblemaInverso,
    aporte_lateral_sintetico,
    caudal_referencia,
    diseno_codicioso,
    informacion_por_candidato,
    invertir_tikhonov,
    jacobiano_diario,
    matriz_regularizacion,
    promedio_diario,
    red_sintetica,
    resolucion,
    rugosidad_verdadera,
    sintetizar_observaciones,
)

PASOS_DIA = 24
DIAS = 40
CAL = 3
RUIDO_REL = 0.05
PISO = 0.5
ALPHA_S, ALPHA_X = 1.0, 1.0


def estaciones_base(red) -> list[int]:
    """Salida + 2 tramos internos de mayor área (imita una red escasa sobre ríos grandes)."""
    A = red.area_drenaje_km2()
    salida = int(np.where(red.aguas_abajo < 0)[0][0])
    internos = [int(i) for i in np.argsort(-A) if i != salida][:2]
    return [salida] + internos


def correr_inversion(modelo, q, estaciones, ln_true, m_ref, D, semilla):
    d, s = sintetizar_observaciones(modelo, ln_true, q, estaciones, PASOS_DIA,
                                    RUIDO_REL, PISO, semilla)
    P = ProblemaInverso(modelo, q, estaciones, PASOS_DIA, d, s, CAL)
    r = invertir_tikhonov(P, m_ref, D, ALPHA_S, ALPHA_X)
    rmse = float(((r.log_n - ln_true) ** 2).mean().sqrt())
    return r, rmse


def una_red(semilla: int, k: int, n_aleatorios: int) -> dict:
    red = red_sintetica(60, semilla)
    q = aporte_lateral_sintetico(red, DIAS, PASOS_DIA, semilla)
    modelo = MuskingumCunge(red, caudal_referencia(red, q), 3600.0)
    ln_true = rugosidad_verdadera(red, semilla)
    m_ref = torch.full((red.n,), float(np.log(0.035)), dtype=torch.float64)
    D = red.laplaciano()
    Wm2 = matriz_regularizacion(red.n, D, ALPHA_S, ALPHA_X)
    A = red.area_drenaje_km2()

    base = estaciones_base(red)

    # --- Jacobiano en el modelo de REFERENCIA (no en la verdad) -------------
    J = jacobiano_diario(modelo, m_ref, q, PASOS_DIA, CAL)          # (dias, N, P)
    with torch.no_grad():
        Q_ref = promedio_diario(modelo.rutear(m_ref, q), PASOS_DIA)[CAL:]
    sigma_todos = RUIDO_REL * Q_ref.abs() + PISO

    # --- Inversión con la red base + resolución -----------------------------
    r_base, rmse_base = correr_inversion(modelo, q, base, ln_true, m_ref, D, semilla)
    res = resolucion(J[:, base, :], sigma_todos[:, base], Wm2, r_base.beta)
    err = (r_base.log_n - ln_true).abs().numpy()
    rho, p_rho = stats.spearmanr(res.diag_R.numpy(), err)

    # --- Diseño -------------------------------------------------------------
    F = informacion_por_candidato(J, sigma_todos)
    H_base = res.H
    d_opt, _ = diseno_codicioso(F, H_base, k, excluir=base, criterio="D")
    por_area = [int(i) for i in np.argsort(-A) if i not in base][:k]
    rng = np.random.default_rng(1000 + semilla)
    candidatos = [i for i in range(red.n) if i not in base]

    filas = []
    for nombre, extra in [("D-optimo", d_opt), ("mayor-area", por_area)] + [
        (f"aleatorio-{j}", list(rng.choice(candidatos, k, replace=False).astype(int)))
        for j in range(n_aleatorios)
    ]:
        est = base + [int(e) for e in extra]
        _, rmse = correr_inversion(modelo, q, est, ln_true, m_ref, D, semilla)
        Hn = H_base + F[extra].sum(0)
        filas.append({
            "estrategia": nombre.split("-")[0] if nombre.startswith("aleatorio") else nombre,
            "estaciones_extra": [int(e) for e in extra],
            "rmse_log_n": rmse,
            "tr_cov_post": float(torch.trace(torch.linalg.inv(Hn))),
        })

    return {
        "semilla": semilla,
        "area_salida_km2": float(A.max()),
        "estaciones_base": base,
        "rmse_prior": float(((m_ref - ln_true) ** 2).mean().sqrt()),
        "rmse_base": rmse_base,
        "beta_final": r_base.beta,
        "spearman_diagR_vs_error": {"rho": float(rho), "p": float(p_rho)},
        "diag_R": res.diag_R.tolist(),
        "error_abs": err.tolist(),
        "diseno": filas,
        "historial_base": r_base.historial,
    }


def figuras(e01: dict, salida: Path) -> None:
    """Figura de E01 con el estilo de publicación (Plotly): HTML interactivo + PNG."""
    from ruteo_inverso.graficos import figura_e01, guardar

    guardar(figura_e01(e01), "e01_identificabilidad", salida)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redes", type=int, default=5)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--aleatorios", type=int, default=5)
    ap.add_argument("--salida", type=Path, default=Path("results"))
    args = ap.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)

    resultados = []
    for s in range(args.redes):
        t = time.time()
        r = una_red(s, args.k, args.aleatorios)
        resultados.append(r)
        resumen = {f["estrategia"]: [] for f in r["diseno"]}
        for f in r["diseno"]:
            resumen[f["estrategia"]].append(f["rmse_log_n"])
        print(f"red {s}: prior={r['rmse_prior']:.3f} base={r['rmse_base']:.3f} "
              + " ".join(f"{k}={np.mean(v):.3f}" for k, v in resumen.items())
              + f" ρ={r['spearman_diagR_vs_error']['rho']:.2f} ({time.time()-t:.0f}s)", flush=True)

    # --- Pruebas pareadas entre redes ---------------------------------------
    def media(r, e):
        return np.mean([f["rmse_log_n"] for f in r["diseno"] if f["estrategia"] == e])

    dopt = np.array([media(r, "D-optimo") for r in resultados])
    area = np.array([media(r, "mayor-area") for r in resultados])
    alea = np.array([media(r, "aleatorio") for r in resultados])
    x = np.concatenate([r["diag_R"] for r in resultados])
    y = np.concatenate([r["error_abs"] for r in resultados])
    rho, p = stats.spearmanr(x, y)

    def wil(a, b):
        if len(a) < 6:
            return {"nota": "n < 6 redes: Wilcoxon sin poder; reportar solo efecto"}
        w = stats.wilcoxon(a, b, alternative="less")
        return {"estadistico": float(w.statistic), "p": float(w.pvalue)}

    global_ = {
        "n_redes": len(resultados),
        "rmse_prior_media": float(np.mean([r["rmse_prior"] for r in resultados])),
        "rmse_base_media": float(np.mean([r["rmse_base"] for r in resultados])),
        "rmse_D_optimo_media": float(dopt.mean()),
        "rmse_mayor_area_media": float(area.mean()),
        "rmse_aleatorio_media": float(alea.mean()),
        "D_vs_area_diferencia_media": float((dopt - area).mean()),
        "D_vs_aleatorio_diferencia_media": float((dopt - alea).mean()),
        "wilcoxon_D_menor_que_area": wil(dopt, area),
        "wilcoxon_D_menor_que_aleatorio": wil(dopt, alea),
        "spearman_diagR_vs_error_global": {"rho": float(rho), "p": float(p)},
        "configuracion": {"dias": DIAS, "pasos_dia": PASOS_DIA, "ruido_rel": RUIDO_REL,
                          "piso_m3s": PISO, "alpha_s": ALPHA_S, "alpha_x": ALPHA_X,
                          "k_estaciones_extra": args.k},
    }
    print(json.dumps(global_, indent=2, ensure_ascii=False))
    (args.salida / "e01_resultados.json").write_text(
        json.dumps({"global": global_, "por_red": resultados}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    figuras({"global": global_, "por_red": resultados}, args.salida)


if __name__ == "__main__":
    main()
