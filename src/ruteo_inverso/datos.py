"""Construcción de la red real: estaciones CAMELS‑COL sobre la topología HydroRIVERS.

Responde la pregunta crítica de la Fase 0: ¿cuántas estaciones de CAMELS‑COL
están ANIDADAS (una aguas arriba de otra)? Sin anidamiento, el problema de
ruteo en red no tiene datos internos con qué invertirse.

Fuentes (descargar manualmente o con scripts/):
* CAMELS‑COL (Jiménez et al.; Zenodo 10.5281/zenodo.18794895, CC BY 4.0):
  coordenadas WGS‑84 y área de cada estación.
* HydroRIVERS v1.0 (Lehner & Grill, 2013), región "sa" (Sudamérica):
  campos HYRIV_ID, NEXT_DOWN, UPLAND_SKM, LENGTH_KM.

Los nombres de columnas de CAMELS‑COL se pasan como argumentos porque no se
han verificado aún contra el archivo publicado.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def anidar_estaciones(rios: pd.DataFrame, estaciones: pd.DataFrame,
                      col_id_rio: str = "HYRIV_ID", col_siguiente: str = "NEXT_DOWN",
                      col_est: str = "estacion", col_tramo: str = "HYRIV_ID") -> pd.DataFrame:
    """Para cada estación (ya asignada a un tramo) encuentra la estación inmediatamente aguas abajo.

    rios: tabla con (col_id_rio, col_siguiente); NEXT_DOWN = 0 en la desembocadura.
    estaciones: tabla con (col_est, col_tramo).
    Devuelve estaciones + columnas ``estacion_aguas_abajo`` (NaN si no hay) y
    ``n_estaciones_aguas_arriba_directas``.
    """
    siguiente = dict(zip(rios[col_id_rio].to_numpy(), rios[col_siguiente].to_numpy()))
    tramo_a_est: dict = {}
    for e, t in zip(estaciones[col_est], estaciones[col_tramo]):
        tramo_a_est.setdefault(t, []).append(e)

    abajo = []
    for e, t in zip(estaciones[col_est], estaciones[col_tramo]):
        # otra estación en el mismo tramo cuenta como aguas abajo solo si es distinta
        otras = [x for x in tramo_a_est.get(t, []) if x != e]
        encontrado = otras[0] if otras else np.nan
        k = siguiente.get(t, 0)
        visitados = 0
        while pd.isna(encontrado) and k not in (0, None) and visitados < 1_000_000:
            if k in tramo_a_est:
                encontrado = tramo_a_est[k][0]
                break
            k = siguiente.get(k, 0)
            visitados += 1
        abajo.append(encontrado)

    out = estaciones.copy()
    out["estacion_aguas_abajo"] = abajo
    conteo = pd.Series(abajo).value_counts()
    out["n_estaciones_aguas_arriba_directas"] = out[col_est].map(conteo).fillna(0).astype(int)
    return out


def resumen_anidamiento(anidadas: pd.DataFrame, col_est: str = "estacion") -> dict:
    tiene_abajo = anidadas["estacion_aguas_abajo"].notna()
    tiene_arriba = anidadas["n_estaciones_aguas_arriba_directas"] > 0
    return {
        "estaciones": int(len(anidadas)),
        "con_estacion_aguas_abajo": int(tiene_abajo.sum()),
        "con_estaciones_aguas_arriba": int(tiene_arriba.sum()),
        "aisladas": int((~tiene_abajo & ~tiene_arriba).sum()),
        "sistemas_con_>=3_estaciones": int(_tamanos_sistemas(anidadas, col_est).ge(3).sum()),
    }


def _tamanos_sistemas(anidadas: pd.DataFrame, col_est: str) -> pd.Series:
    """Tamaño de cada sistema (componente conexa) de estaciones anidadas."""
    padre = {e: e for e in anidadas[col_est]}

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for e, a in zip(anidadas[col_est], anidadas["estacion_aguas_abajo"]):
        if pd.notna(a) and a in padre:
            padre[raiz(e)] = raiz(a)
    return pd.Series([raiz(e) for e in anidadas[col_est]]).value_counts()


def asignar_tramo(rios_gdf, estaciones_df, col_lon: str, col_lat: str, col_area: str,
                  radio_km: float = 5.0, tol_area: float = 0.3):
    """Asigna cada estación al tramo HydroRIVERS con área de drenaje más compatible
    dentro de ``radio_km``.

    Requiere geopandas. Selecciona el tramo cuya UPLAND_SKM minimiza
    |log(A_tramo / A_estación)| y marca como dudosas las asignaciones con error
    relativo de área > ``tol_area``.
    """
    import geopandas as gpd

    est = gpd.GeoDataFrame(
        estaciones_df.copy(),
        geometry=gpd.points_from_xy(estaciones_df[col_lon], estaciones_df[col_lat]),
        crs="EPSG:4326",
    ).to_crs("EPSG:9377")  # MAGNA‑SIRGAS / Origen Nacional (metros)
    rios = rios_gdf.to_crs("EPSG:9377")
    # Candidatos: todos los tramos a menos de radio_km; se elige por área, no por distancia
    buf = est.copy()
    buf["geometry"] = buf.buffer(radio_km * 1e3)
    multi = gpd.sjoin(buf, rios[["HYRIV_ID", "UPLAND_SKM", "geometry"]], how="left",
                      predicate="intersects")
    multi["err_log_area"] = np.abs(np.log(multi["UPLAND_SKM"] / multi[col_area]))
    mejor = multi.sort_values("err_log_area").groupby(level=0).head(1).sort_index()
    mejor["asignacion_dudosa"] = np.exp(mejor["err_log_area"]) - 1 > tol_area
    return pd.DataFrame(mejor.drop(columns="geometry"))