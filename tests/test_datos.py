import pandas as pd

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