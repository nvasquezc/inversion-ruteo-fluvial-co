"""Marca qué estaciones de CAMELS‑COL tienen embalses dentro de su cuenca.

Cruza los polígonos de cuenca de CAMELS‑COL con una base de presas (por defecto
GRanD v1.3, Lehner et al. 2011, disponible en https://www.globaldamwatch.org/).
Una estación queda "regulada" si al menos una presa cae dentro de su cuenca.

Limitación: GRanD v1.3 (2019) puede no incluir presas recientes (p. ej.
Hidroituango). Para una lista más completa se puede usar GDW v1 (2023) con
los mismos argumentos de columnas.

Uso:
  uv run python scripts/marcar_embalses.py --presas data/GRanD_Version_1_3/GRanD_dams_v1_3.shp
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--presas", type=Path, required=True, help="shapefile de puntos de presas")
    ap.add_argument("--col-nombre", default="DAM_NAME")
    ap.add_argument("--col-anio", default="YEAR")
    ap.add_argument("--col-capacidad", default="CAP_MCM", help="capacidad en millones de m³")
    ap.add_argument("--anidadas", type=Path,
                    default=Path("results/fase0/estaciones_anidadas_poligonos.csv"))
    ap.add_argument("--salida", type=Path, default=Path("results/fase0/estaciones_embalses.csv"))
    a = ap.parse_args()

    import geopandas as gpd

    cuencas = gpd.read_file(next(Path("data/camels_col").rglob("CAMELS_COL_catchments_boundaries.shp")))
    cuencas["IDEAM_CODE"] = cuencas["IDEAM_CODE"].astype(str)
    cuencas["geometry"] = cuencas.geometry.make_valid()
    presas = gpd.read_file(a.presas).to_crs(cuencas.crs)
    presas = presas.cx[cuencas.total_bounds[0]:cuencas.total_bounds[2],
                       cuencas.total_bounds[1]:cuencas.total_bounds[3]]
    print(f"presas dentro de la ventana de Colombia: {len(presas)}")

    cruce = gpd.sjoin(presas[[a.col_nombre, a.col_anio, a.col_capacidad, "geometry"]],
                      cuencas[["IDEAM_CODE", "geometry"]], predicate="within")
    cruce[a.col_capacidad] = pd.to_numeric(cruce[a.col_capacidad], errors="coerce")
    cruce[a.col_anio] = pd.to_numeric(cruce[a.col_anio], errors="coerce")
    por_estacion = cruce.groupby("IDEAM_CODE").agg(
        n_presas=(a.col_nombre, "size"),
        capacidad_total_mcm=(a.col_capacidad, "sum"),
        presa_mas_antigua=(a.col_anio, "min"),
        presas=(a.col_nombre, lambda s: "; ".join(sorted(map(str, s.dropna()))[:6])),
    )

    anid = pd.read_csv(a.anidadas, dtype={"estacion": str, "estacion_aguas_abajo": str})
    t = anid[["estacion", "gauge_department", "area_km2", "estacion_aguas_abajo"]].merge(
        por_estacion, left_on="estacion", right_index=True, how="left")
    t["n_presas"] = t["n_presas"].fillna(0).astype(int)
    t["regulada"] = t["n_presas"] > 0
    t.to_csv(a.salida, index=False)

    print(f"estaciones con al menos una presa en su cuenca: {int(t['regulada'].sum())} de {len(t)}")
    print("\nestaciones reguladas con más capacidad aguas arriba:")
    cols = ["estacion", "gauge_department", "area_km2", "n_presas", "capacidad_total_mcm",
            "presa_mas_antigua", "presas"]
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 60)
    print(t[t["regulada"]].sort_values("capacidad_total_mcm", ascending=False)[cols]
          .head(25).round(0).to_string(index=False))
    print(f"\ntabla completa en {a.salida}")


if __name__ == "__main__":
    main()
