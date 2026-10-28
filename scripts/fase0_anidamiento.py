"""Fase 0 — ¿Cuántas estaciones de CAMELS‑COL están anidadas?

Punto de decisión (go/no‑go) del proyecto (docs/protocolo.md, Fase 0): se sigue
con la inversión en red real si hay ≥ 5 sistemas con ≥ 3 estaciones anidadas
cuyos registros se solapen ≥ 10 años.

Método principal (no necesita datos externos): polígonos de cuenca publicados
por CAMELS‑COL. La cuenca A está anidada en B si ≥ 90 % de su área cae dentro
de B. Verificación opcional e independiente: ubicar las estaciones sobre la red
HydroRIVERS y seguir NEXT_DOWN (``--hydrorivers``).

Formato real de CAMELS‑COL v3 (verificado):
* 02_CAMELS_COL_Catchment_information.csv: separador ';', fechas dd/mm/aaaa,
  gauge_lat / gauge_lon en METROS World Mercator (EPSG:3395), no en grados.
* 10_CAMELS_COL_Physiograpic_characteristics.csv: columna ``area`` en km².
* 03_.../CAMELS_COL_catchments_boundaries.shp: polígonos, campo IDEAM_CODE, EPSG:3395.

Uso (desde la raíz del repo):
  uv run python scripts/fase0_anidamiento.py
  uv run python scripts/fase0_anidamiento.py --hydrorivers data/HydroRIVERS_v10_sa_shp/HydroRIVERS_v10_sa.shp
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ruteo_inverso.datos import (anidar_estaciones, anidar_por_poligonos, anos_solapados,
                                 asignar_tramo, resumen_anidamiento)

BASE = Path("data/camels_col")


def buscar(patron: str) -> Path:
    hallados = sorted(BASE.rglob(patron))
    if not hallados:
        raise FileNotFoundError(f"No se encontró {patron} dentro de {BASE}. "
                                "¿Descargaste y descomprimiste CAMELS-COL?")
    return hallados[0]


def leer_csv(ruta: Path) -> pd.DataFrame:
    """Lee un CSV de CAMELS‑COL detectando el separador y la codificación.

    Algunos archivos vienen en UTF‑8 y otros en Latin‑1 (Windows‑1252), por
    ejemplo con nombres de departamento acentuados como "Bolívar".
    """
    for codificacion in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(ruta, sep=None, engine="python", encoding=codificacion)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"No se pudo decodificar {ruta}")


def cargar_estaciones() -> pd.DataFrame:
    info = leer_csv(buscar("02_CAMELS_COL_Catchment_information.csv"))
    fisio = leer_csv(buscar("10_CAMELS_COL_Physiograpic_characteristics.csv"))
    est = info.merge(fisio[["gauge_id", "area"]], on="gauge_id", how="left")
    est["gauge_id"] = est["gauge_id"].astype(str)
    est["inicio"] = pd.to_datetime(est["gauge_star"], dayfirst=True)
    est["fin"] = pd.to_datetime(est["gauge_end"], dayfirst=True)
    return est


def sistemas_utiles(anid: pd.DataFrame, min_anos: float) -> int:
    """Sistemas con ≥ 3 estaciones contando solo enlaces con ≥ min_anos de registro común."""
    filtrado = anid.copy()
    filtrado.loc[filtrado["anos_comunes"] < min_anos, "estacion_aguas_abajo"] = pd.NA
    filtrado["n_estaciones_aguas_arriba_directas"] = filtrado["estacion"].map(
        filtrado["estacion_aguas_abajo"].value_counts()).fillna(0).astype(int)
    return resumen_anidamiento(filtrado)["sistemas_con_>=3_estaciones"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral", type=float, default=0.9,
                    help="fracción mínima de la cuenca que debe caer dentro de otra")
    ap.add_argument("--min-anos", type=float, default=10.0,
                    help="años mínimos de registro común para que un enlace cuente")
    ap.add_argument("--hydrorivers", type=Path, default=None,
                    help="shapefile HydroRIVERS (opcional, verificación independiente)")
    ap.add_argument("--salida", type=Path, default=Path("results/fase0"))
    a = ap.parse_args()

    import geopandas as gpd

    a.salida.mkdir(parents=True, exist_ok=True)
    est = cargar_estaciones()
    cuencas = gpd.read_file(buscar("CAMELS_COL_catchments_boundaries.shp"))
    cuencas["IDEAM_CODE"] = cuencas["IDEAM_CODE"].astype(str)
    print(f"estaciones (tabla 02): {len(est)}   cuencas (shapefile): {len(cuencas)}")

    # --- Método 1: polígonos de cuenca ------------------------------------
    anid = anidar_por_poligonos(cuencas, "IDEAM_CODE", umbral=a.umbral)
    anid = anid.merge(est[["gauge_id", "gauge_department", "area", "inicio", "fin"]],
                      left_on="estacion", right_on="gauge_id", how="left").drop(columns="gauge_id")
    fechas = est.set_index("gauge_id")[["inicio", "fin"]]
    anid["anos_comunes"] = [
        anos_solapados(r.inicio, r.fin, *fechas.loc[r.estacion_aguas_abajo])
        if pd.notna(r.estacion_aguas_abajo) and r.estacion_aguas_abajo in fechas.index else 0.0
        for r in anid.itertuples()]
    # control de calidad: área del polígono frente al área publicada en la tabla 10
    anid["error_area_rel"] = (anid["area_km2"] - anid["area"]).abs() / anid["area"]

    resumen = resumen_anidamiento(anid)
    resumen["sistemas_con_>=3_estaciones_y_>=%d_anos_comunes" % a.min_anos] = sistemas_utiles(
        anid, a.min_anos)
    resumen["mediana_error_area_poligono_vs_tabla"] = round(float(anid["error_area_rel"].median()), 4)
    utiles = resumen["sistemas_con_>=3_estaciones_y_>=%d_anos_comunes" % a.min_anos]
    resumen["decision_fase0"] = ("VIABLE: >= 5 sistemas utiles" if utiles >= 5
                                 else "NO VIABLE con este criterio: redefinir alcance (ver protocolo)")

    print("\n=== Anidamiento por polígonos de cuenca ===")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    anid.sort_values(["estacion_aguas_abajo", "area_km2"]).to_csv(
        a.salida / "estaciones_anidadas_poligonos.csv", index=False)

    # --- Método 2 (opcional): HydroRIVERS -----------------------------------
    if a.hydrorivers is not None:
        rios = gpd.read_file(a.hydrorivers, bbox=(-80.0, -5.0, -66.0, 13.5))
        print(f"\ntramos HydroRIVERS en la ventana: {len(rios):,}")
        asign = asignar_tramo(rios, est, "gauge_lon", "gauge_lat", "area",
                              crs_estaciones="EPSG:3395").rename(columns={"gauge_id": "estacion"})
        validas = asign[asign["HYRIV_ID"].notna() & ~asign["asignacion_dudosa"]].copy()
        anid_h = anidar_estaciones(rios[["HYRIV_ID", "NEXT_DOWN"]], validas)
        res_h = resumen_anidamiento(anid_h)
        res_h["dudosas_excluidas"] = int(asign["asignacion_dudosa"].sum())
        comun = anid.set_index("estacion")["estacion_aguas_abajo"].reindex(anid_h["estacion"])
        coincide = (comun.fillna("-").values == anid_h["estacion_aguas_abajo"].astype(object).fillna("-").values)
        res_h["coincidencia_con_poligonos"] = round(float(coincide.mean()), 3)
        print("\n=== Anidamiento por HydroRIVERS ===")
        print(json.dumps(res_h, indent=2, ensure_ascii=False))
        anid_h.to_csv(a.salida / "estaciones_anidadas_hydrorivers.csv", index=False)
        resumen["hydrorivers"] = res_h

    (a.salida / "resumen_anidamiento.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nresultados en {a.salida}/")


if __name__ == "__main__":
    main()