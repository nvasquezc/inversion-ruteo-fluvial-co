import pandas as pd
import pytest

from ruteo_inverso.datos import anidar_estaciones, resumen_anidamiento


def test_anidamiento_red_de_juguete():
    #   1 → 3 → 5 → 0(mar)      2 → 3       4 → 5       9 → 0 (cuenca aparte)
    rios = pd.DataFrame({"HYRIV_ID": [1, 2, 3, 4, 5, 9],
                         "NEXT_DOWN": [3, 3, 5, 5, 0, 0]})
    est = pd.DataFrame({"estacion": ["A", "B", "C", "D", "E"],
                        "HYRIV_ID": [1, 2, 5, 9, 4]})
    out = anidar_estaciones(rios, est).set_index("estacion")
    assert out.loc["A", "estacion_aguas_abajo"] == "C"
    assert out.loc["B", "estacion_aguas_abajo"] == "C"
    assert out.loc["E", "estacion_aguas_abajo"] == "C"
    assert pd.isna(out.loc["C", "estacion_aguas_abajo"])
    assert pd.isna(out.loc["D", "estacion_aguas_abajo"])
    assert out.loc["C", "n_estaciones_aguas_arriba_directas"] == 3
    r = resumen_anidamiento(out.reset_index())
    assert r == {"estaciones": 5, "con_estacion_aguas_abajo": 3,
                 "con_estaciones_aguas_arriba": 1, "aisladas": 1,
                 "sistemas_con_>=3_estaciones": 1}


def test_anidamiento_por_poligonos():
    gpd = pytest.importorskip("geopandas")
    from shapely.geometry import box

    from ruteo_inverso.datos import anidar_por_poligonos

    # Cuencas en EPSG:3395 (metros), como en CAMELS-COL:
    #   GRANDE contiene a MEDIA, MEDIA contiene a PEQ; AISLADA no toca a nadie
    x0, y0 = -8_500_000, 600_000
    cuencas = gpd.GeoDataFrame(
        {"IDEAM_CODE": ["GRANDE", "MEDIA", "PEQ", "AISLADA"]},
        geometry=[box(x0, y0, x0 + 100_000, y0 + 100_000),
                  box(x0 + 10_000, y0 + 10_000, x0 + 60_000, y0 + 60_000),
                  box(x0 + 20_000, y0 + 20_000, x0 + 30_000, y0 + 30_000),
                  box(x0 + 300_000, y0, x0 + 320_000, y0 + 20_000)],
        crs="EPSG:3395")
    out = anidar_por_poligonos(cuencas, "IDEAM_CODE").set_index("estacion")
    assert out.loc["PEQ", "estacion_aguas_abajo"] == "MEDIA"      # la menor que la contiene
    assert out.loc["MEDIA", "estacion_aguas_abajo"] == "GRANDE"
    assert pd.isna(out.loc["GRANDE", "estacion_aguas_abajo"])
    assert pd.isna(out.loc["AISLADA", "estacion_aguas_abajo"])
    r = resumen_anidamiento(out.reset_index())
    assert r["sistemas_con_>=3_estaciones"] == 1 and r["aisladas"] == 1


def test_anos_solapados():
    from ruteo_inverso.datos import anos_solapados
    assert abs(anos_solapados("1990-01-01", "2010-01-01", "2000-01-01", "2020-01-01") - 10) < 0.01
    assert anos_solapados("1990-01-01", "1995-01-01", "2000-01-01", "2020-01-01") == 0
