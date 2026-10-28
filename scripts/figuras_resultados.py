"""Regenera las figuras de resultados (HTML interactivo + PNG a ~300 ppp) sin recalcular nada.

Lee results/e01_resultados.json y results/fase0/ (incluida la capa del mapa
mapa_fase0.json, que produce scripts/preparar_mapa_fase0.py). Uso:

    uv run python scripts/figuras_resultados.py

El PNG necesita Chrome (kaleido). Si falta: ``uv run plotly_get_chrome``.
"""

import json
from pathlib import Path

import pandas as pd

from ruteo_inverso.graficos import figura_e01, figura_fase0, figura_sintesis, guardar

RES = Path("results")


def main():
    e01 = json.loads((RES / "e01_resultados.json").read_text(encoding="utf-8"))
    guardar(figura_sintesis(e01), "e01_sintesis", RES)          # figura 2 del README
    guardar(figura_e01(e01), "e01_identificabilidad", RES)
    f0 = RES / "fase0"
    if (f0 / "mapa_fase0.json").exists():
        mapa = json.loads((f0 / "mapa_fase0.json").read_text(encoding="utf-8"))
        sistemas = pd.read_csv(f0 / "sistemas_fase0.csv", dtype={"salida": str})
        guardar(figura_fase0(mapa, sistemas), "fase0_cuencas_anidadas", f0)
    print("figuras en", RES)


if __name__ == "__main__":
    main()
