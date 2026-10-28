# Puente conceptual: de la inversión geofísica al ruteo fluvial

Este proyecto toma prestado el **marco** del curso
[`inversion-geofisica-python`](https://github.com/nvasquezc/inversion-geofisica-python)
(fork del curso original de Anagabrielamantilla et al., vinculado a MINCIENCIAS, ANH y UIS).
El curso **no declara licencia abierta**, por eso aquí **no se reutiliza su código**.
Solo se toman los conceptos, que son estándar en inversión, y se cita la fuente.

La idea central del curso, "los datos observados se relacionan con un modelo físico a
través de un operador directo, más ruido", se aplica tal cual a una red de ríos:

| Sesión del curso | Concepto | Equivalente en este proyecto | Dónde está en el código |
|---|---|---|---|
| 01 Fundamentos | No unicidad, sensibilidad, incertidumbre, regularización | Equifinalidad de la rugosidad de Manning; varios campos de *n* explican los mismos hidrogramas diarios | `inversion.py`, `resolucion.py` |
| 01 Fundamentos | Regularización de Tikhonov (*smallness* + suavidad) | φ_m = α_s‖m − m_ref‖² + α_x‖D(m − m_ref)‖², con D = diferencias entre tramos conectados | `RedFluvial.laplaciano`, `invertir_tikhonov` |
| 02–03 Gravimetría y magnetometría (SimPEG) | Enfriamiento de β, estimación de β₀, misfit objetivo (*BetaSchedule*, *BetaEstimate*, *TargetMisfit*) | Las mismas directivas, implementadas sobre el grafo | `estimar_beta0`, `invertir_tikhonov` |
| 02–03 | Profundidad de investigación, celdas activas | **Resolubilidad por tramo**: diag(R) dice qué tramos "ven" las estaciones | `resolucion()` |
| 04 MT‑1D guiado por física | Operador directo diferenciable (impedancia Zxy → resistividad por capas) | Operador directo diferenciable Muskingum–Cunge (aporte lateral → caudal en estaciones) | `ruteo.py` |
| 07 Reto MT‑1D | Inversión profunda **no supervisada**: la red se entrena solo con el desajuste de datos a través del operador | f_θ(atributos del tramo) → log *n*, entrenada solo con los hidrogramas observados; permite predecir *n* en tramos sin aforo | `invertir_neuronal` |
| 05–06 FWI | Geometría de adquisición; la cobertura de fuentes y receptores controla qué se resuelve | **Diseño de la red de aforos**: dónde instalar la próxima estación para maximizar la información (criterios D y A) | `diseno_codicioso` |

## Lo que la geofísica aporta y la hidrología diferenciable aún no usa de forma sistemática

La hidrología diferenciable ya invierte *n* con una red neuronal y un operador
Muskingum–Cunge diferenciable (Bindas et al., 2024, *WRR*). Encontraron que la geometría
del cauce no es identificable y que *n* lo es solo "con precisión moderada". Lo hicieron
con experimentos sintéticos puntuales, sin un análisis formal de resolución.

Lo que el flujo geofísico agrega:

1. **Matriz de resolución y covarianza posterior.** No basta con decir "es identificable o
   no": se puede cuantificar por tramo cuánto viene de los datos y cuánto de la
   regularización.
2. **Diseño de experimentos.** En geofísica se diseña la adquisición antes de adquirir.
   El equivalente es decidir dónde poner estaciones hidrométricas. En Colombia esa decisión
   tiene costo y consecuencias reales: CAMELS‑COL conservó 347 de 921 estaciones de IDEAM,
   y las regiones de la Amazonía y la Orinoquía están poco instrumentadas.
3. **Disciplina con el ruido.** El principio de discrepancia (φ_d ≈ N) evita sobreajustar
   errores de la curva de gasto.

**Advertencia.** El análisis de resolución es **lineal y local** alrededor de m̂.
Para hacer afirmaciones globales hay que complementarlo con muestreo (ensembles o MCMC),
como se plantea en la Fase 3 de `docs/protocolo.md`.