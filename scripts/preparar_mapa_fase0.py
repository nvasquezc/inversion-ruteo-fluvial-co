"""Prepara la capa liviana del mapa de la Fase 0 (results/fase0/mapa_fase0.json).

Lee los datos crudos (no versionados) de CAMELS‑COL y GRanD, simplifica las
geometrías y guarda solo lo que dibuja ``graficos.figura_fase0``: los polígonos de
las cuencas de salida de cada subsistema anidado, la red de drenaje dentro de ellas,
las estaciones anidadas y las presas dentro de Colombia. Así el mapa se puede
regenerar sin descargar los datos.

Uso (desde la raíz del repo, con el extra ``geo``):
  uv run python scripts/preparar_mapa_fase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ruteo_inverso.graficos import FRAGMENTOS_FASE0, RECURSOS

BASE = Path("data/camels_col")
F0 = Path("results/fase0")
TOL_GRADOS = 0.01          # ≈ 1,1 km: suficiente para un mapa de país
LONG_MIN_KM = 1.5          # se omiten segmentos de cauce más cortos


def buscar(patron: str) -> Path:
    hallados = sorted(BASE.rglob(patron))
    if not hallados:
        raise FileNotFoundError(f"No se encontró {patron} dentro de {BASE}")
    return hallados[0]


def anillos(geom) -> list[list[list[float]]]:
    partes = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    return [[[round(x, 4), round(y, 4)] for x, y in p.exterior.coords]
            for p in partes if p.geom_type == "Polygon"]


def main():
    import geopandas as gpd

    sistemas = pd.read_csv(F0 / "sistemas_fase0.csv", dtype={"salida": str})
    embalses = pd.read_csv(F0 / "estaciones_embalses.csv", dtype={"estacion": str})
    anid = pd.read_csv(F0 / "estaciones_anidadas_poligonos.csv",
                       dtype={"estacion": str, "estacion_aguas_abajo": str})
    regulada = dict(zip(embalses["estacion"], embalses["regulada"], strict=True))

    cuencas = gpd.read_file(buscar("CAMELS_COL_catchments_boundaries.shp"))
    cuencas["IDEAM_CODE"] = cuencas["IDEAM_CODE"].astype(str)
    cuencas = cuencas.set_index("IDEAM_CODE")
    salidas = sistemas["salida"].tolist()
    sel = cuencas.loc[salidas].to_crs(4326)
    sel["geometry"] = sel.geometry.make_valid().simplify(TOL_GRADOS)

    def grupo(s):
        if s in FRAGMENTOS_FASE0:
            return "pieza"
        return "regulada" if regulada.get(s, False) else "natural"

    capa_cuencas = [{"salida": s, "grupo": grupo(s), "anillos": anillos(sel.loc[s, "geometry"])}
                    for s in salidas]

    # Red de drenaje solo dentro de las cuencas de salida que no son piezas de otra
    red = gpd.read_file(buscar("Drainage_network.shp"))
    red["IDEAM_CODE"] = red["IDEAM_CODE"].astype(str)
    red = red[red["IDEAM_CODE"].isin([s for s in salidas if s not in FRAGMENTOS_FASE0])]
    red = red.explode(index_parts=False)
    red = red[red.to_crs(9377).length / 1e3 >= LONG_MIN_KM].to_crs(4326)
    red["geometry"] = red.geometry.simplify(TOL_GRADOS)
    rios = [[[round(x, 4), round(y, 4)] for x, y in g.coords] for g in red.geometry if len(g.coords) > 1]

    # Estaciones anidadas (con otra aguas abajo o aguas arriba)
    info = pd.read_csv(buscar("02_CAMELS_COL_Catchment_information.csv"), sep=None, engine="python",
                       encoding="latin-1")
    info["gauge_id"] = info["gauge_id"].astype(str)
    anidadas = set(anid.loc[anid["estacion_aguas_abajo"].notna(), "estacion"]) | set(
        anid["estacion_aguas_abajo"].dropna())
    pts = gpd.GeoDataFrame(info[info["gauge_id"].isin(anidadas)],
                           geometry=gpd.points_from_xy(info.loc[info["gauge_id"].isin(anidadas), "gauge_lon"],
                                                       info.loc[info["gauge_id"].isin(anidadas), "gauge_lat"]),
                           crs="EPSG:3395").to_crs(4326)
    estaciones = [{"id": r.gauge_id, "lon": round(r.geometry.x, 4), "lat": round(r.geometry.y, 4)}
                  for r in pts.itertuples()]

    # Presas de GRanD dentro de Colombia (Natural Earth 10 m)
    presas = []
    rutas = sorted(Path("data").rglob("GRanD_dams_v1_3.shp"))
    if rutas:
        col = gpd.read_file(RECURSOS / "paises_ne10m.geojson")
        col = col[col["nombre"] == "Colombia"].set_crs(4326, allow_override=True)
        dams = gpd.read_file(rutas[0]).to_crs(4326)
        dams = dams[dams.within(col.geometry.iloc[0])]
        presas = [{"nombre": str(r.DAM_NAME), "lon": round(r.geometry.x, 4), "lat": round(r.geometry.y, 4)}
                  for r in dams.itertuples()]

    salida = {"fuente": "CAMELS-COL v3 (Zenodo 18794895); GRanD v1.3; Natural Earth 10 m",
              "cuencas": capa_cuencas, "rios": rios, "estaciones": estaciones, "presas": presas}
    destino = F0 / "mapa_fase0.json"
    destino.write_text(json.dumps(salida, separators=(",", ":")), encoding="utf-8")
    print(f"{destino}: {len(capa_cuencas)} cuencas, {len(rios)} tramos de río, "
          f"{len(estaciones)} estaciones, {len(presas)} presas, {destino.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
