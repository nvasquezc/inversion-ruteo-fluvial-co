# Datos (no versionados)

Los datos crudos no se suben al repositorio. Para reproducir los resultados, descárgalos así:

| Conjunto | Cómo obtenerlo | Dónde dejarlo | Licencia |
|---|---|---|---|
| CAMELS-COL v3 (Jiménez et al.) | `uv run python scripts/descargar_camels_col.py` y descomprimir cada `.zip` en una carpeta con su mismo nombre | `data/camels_col/` | CC BY 4.0 |
| GRanD v1.3 (Lehner et al., 2011) | Descarga manual en https://www.globaldamwatch.org/ | `data/GRanD_Version_1_3/` | CC BY 4.0 |
| HydroRIVERS v1.0, Sudamérica (opcional) | Descarga manual en https://www.hydrosheds.org/products/hydrorivers | `data/HydroRIVERS_v10_sa_shp/` | Licencia HydroSHEDS (uso no comercial y académico; revisar términos) |

Para descomprimir CAMELS-COL en PowerShell:

    Get-ChildItem data\camels_col -Filter *.zip | ForEach-Object { Expand-Archive $_.FullName -DestinationPath (Join-Path $_.DirectoryName $_.BaseName) -Force }

Formato verificado de CAMELS-COL v3: CSV separados por `;`, codificación Latin-1 en algunos
archivos, fechas dd/mm/aaaa y coordenadas de estación en metros World Mercator (EPSG:3395).
