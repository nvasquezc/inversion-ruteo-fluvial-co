"""Descarga CAMELS‑COL desde Zenodo y verifica sumas MD5.

Uso:  uv run python scripts/descargar_camels_col.py --destino data/camels_col

Registro: https://zenodo.org/records/18794895 (v3, CC BY 4.0).
Cite: Jiménez et al., "CAMELS‑COL: A Large‑Sample Hydrometeorological
Dataset for Colombia" (ESSD, preprint essd‑2025‑200).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

REGISTRO = "18794895"


def md5(ruta: Path) -> str:
    h = hashlib.md5()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", type=Path, default=Path("data/camels_col"))
    ap.add_argument("--registro", default=REGISTRO)
    args = ap.parse_args()
    args.destino.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(f"https://zenodo.org/api/records/{args.registro}") as r:
        meta = json.load(r)
    (args.destino / "zenodo_metadata.json").write_text(json.dumps(meta, indent=1))

    for archivo in meta["files"]:
        nombre = archivo["key"]
        url = archivo["links"]["self"]
        esperado = archivo["checksum"].split(":", 1)[1]
        ruta = args.destino / nombre
        if ruta.exists() and md5(ruta) == esperado:
            print(f"ok (ya existe)  {nombre}")
            continue
        print(f"descargando    {nombre} ({archivo['size'] / 1e6:.1f} MB)")
        urllib.request.urlretrieve(url, ruta)
        if md5(ruta) != esperado:
            raise RuntimeError(f"MD5 no coincide para {nombre}")
        print(f"ok             {nombre}")


if __name__ == "__main__":
    main()