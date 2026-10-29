# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
versiones según [SemVer](https://semver.org/lang/es/).

## [Sin publicar]

### Pendiente
- Grado de regulación (DOR) para la cuenca 35257040 (Chivor, Guavio, Golillas).
- Lector de las series diarias de CAMELS‑COL para el piloto 31097010 (Fase 2).
- Revisión sistemática de literatura (decisión de novedad, `docs/estado_del_arte.md` §3).

## [0.1.1] — 2026-10-29

### Corregido
- Metadatos de Zenodo (`.zenodo.json`): identificadores relacionados como DOI con su esquema
  explícito y sin autorreferencia al repositorio (Zenodo la agrega solo); licencia con el
  identificador `mit`. Primera versión archivada en Zenodo.

## [0.1.0] — 2026-10-28

Primera versión pública.

### Añadido
- Operador Muskingum–Cunge diferenciable en PyTorch que conserva la masa por construcción
  (error relativo < 10⁻¹⁰ en las pruebas).
- Inversión de Tikhonov con β‑cooling y criterio de discrepancia χ² (estilo SimPEG) e
  inversión neuronal no supervisada.
- Jacobiano por autodiferenciación, matriz de resolución, covarianza posterior linealizada y
  diseño D/A‑óptimo codicioso de la red de estaciones.
- **E01 (sintético, 12 redes × 60 tramos):** el diseño D‑óptimo reduce el RMSE de log *n*
  de 0,248 (mayor área) a 0,226 (Wilcoxon p = 7×10⁻⁴); solo el 13 % de los tramos tiene
  diag(R) > 0,1.
- **Fase 0 (CAMELS‑COL v3 + GRanD v1.3):** anidamiento por polígonos de cuenca; 18 cuencas
  independientes con ≥ 3 estaciones, 15 sin presas. Decisión: VIABLE. Piloto 31097010.
- Notebook `01_analisis_paso_a_paso.ipynb` con 12 secciones ejecutadas, resumen, tablas de
  tres filetes y 14 figuras numeradas con su pie, como en un artículo.
- Módulo `graficos.py`: figuras de publicación con Plotly (`graph_objects`): ejes en caja,
  paneles (a), (b), paleta de Okabe e Ito, escalas secuenciales de un tono, red sintética en
  planta con barra de escala y mapa de Colombia (Natural Earth 10 m) con las cuencas anidadas
  de CAMELS‑COL, su red de drenaje y las presas de GRanD.
- `scripts/preparar_mapa_fase0.py` y `scripts/figuras_resultados.py` para regenerar las figuras.
- README con mapa de Colombia (Fase 0) y figura de síntesis de E01: la resolución crece con el
  área de drenaje (ρ = 0,81) y el diseño D‑óptimo gana en 11 de 12 redes.
- CI con uv, ruff y pytest; metadatos de cita (`CITATION.cff`, `.zenodo.json`).

[Sin publicar]: https://github.com/nvasquezc/inversion-ruteo-fluvial-co/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/nvasquezc/inversion-ruteo-fluvial-co/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/nvasquezc/inversion-ruteo-fluvial-co/releases/tag/v0.1.0
