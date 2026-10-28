# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
versiones según [SemVer](https://semver.org/lang/es/).

## [Sin publicar]

### Pendiente
- Grado de regulación (DOR) para la cuenca 35257040 (Chivor, Guavio, Golillas).
- Lector de las series diarias de CAMELS‑COL para el piloto 31097010 (Fase 2).
- Revisión sistemática de literatura (decisión de novedad, `docs/estado_del_arte.md` §3).

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
- Notebook `01_analisis_paso_a_paso.ipynb` con 12 pasos ejecutados.
- CI con uv, ruff y pytest; metadatos de cita (`CITATION.cff`, `.zenodo.json`).

[Sin publicar]: https://github.com/nvasquezc/inversion-ruteo-fluvial-co/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/nvasquezc/inversion-ruteo-fluvial-co/releases/tag/v0.1.0
