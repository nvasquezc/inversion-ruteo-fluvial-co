"""Describe los sistemas de estaciones anidadas encontrados en la Fase 0.

Lee results/fase0/estaciones_anidadas_poligonos.csv y reporta, por sistema
(componente conexa de enlaces con >= min_anos de registro común):
número de estaciones, departamento principal, área de la estación de salida,
profundidad de la cadena y calidad de los enlaces.

Uso:  uv run python scripts/resumen_sistemas_fase0.py --min-anos 10
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", type=Path,
                    default=Path("results/fase0/estaciones_anidadas_poligonos.csv"))
    ap.add_argument("--min-anos", type=float, default=10.0)
    a = ap.parse_args()

    d = pd.read_csv(a.entrada, dtype={"estacion": str, "estacion_aguas_abajo": str})
    enlace = d["estacion_aguas_abajo"].notna() & (d["anos_comunes"] >= a.min_anos)
    abajo = dict(zip(d.loc[enlace, "estacion"], d.loc[enlace, "estacion_aguas_abajo"]))

    def salida(e):
        prof = 0
        while e in abajo:
            e, prof = abajo[e], prof + 1
        return e, prof

    res = [salida(e) for e in d["estacion"]]
    d["sistema"] = [r[0] for r in res]
    d["profundidad"] = [r[1] for r in res]

    area = d.set_index("estacion")["area_km2"]
    filas = []
    for s, g in d.groupby("sistema"):
        if len(g) < 3:
            continue
        hijos = g[g["estacion"] != s]
        razon = (hijos["area_km2"] / hijos["estacion_aguas_abajo"].map(area)).dropna()
        filas.append({
            "salida": s,
            "estaciones": len(g),
            "departamento_principal": g["gauge_department"].mode().iat[0],
            "area_salida_km2": round(float(area.get(s, float("nan")))),
            "profundidad_max": int(g["profundidad"].max()),
            "anos_comunes_mediana": round(float(hijos["anos_comunes"].median()), 1),
            "fraccion_contenida_min": round(float(hijos["fraccion_contenida"].min()), 3),
            "enlaces_area_hijo>95%_padre": int((razon > 0.95).sum()),
        })
    t = pd.DataFrame(filas).sort_values("estaciones", ascending=False)
    pd.set_option("display.width", 200)
    print(t.to_string(index=False))
    print(f"\nsistemas >= 3 estaciones: {len(t)}   estaciones en ellos: {int(t['estaciones'].sum())}")
    print(f"el sistema más grande reúne el {t['estaciones'].max() / len(d):.0%} de todas las estaciones")
    t.to_csv(a.entrada.parent / "sistemas_fase0.csv", index=False)


if __name__ == "__main__":
    main()
