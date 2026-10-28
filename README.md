# inversion-ruteo-fluvial-co

**¿Qué parte de la red de ríos de Colombia pueden "ver" las estaciones hidrométricas, y dónde
conviene instalar la próxima?**

Este repositorio aplica el flujo de trabajo de la **inversión geofísica** (operador directo,
regularización, matriz de resolución, diseño de adquisición) al **ruteo de caudales** en redes
fluviales. Usa un operador Muskingum–Cunge diferenciable que **conserva la masa por
construcción**.

> **Estado (oct. 2026).** Metodología verificada en datos sintéticos (Fase 1) y viabilidad con
> datos reales confirmada (Fase 0). La inversión con datos reales (Fase 2) aún no se ha hecho.
> La revisión de literatura es preliminar (ver [`docs/estado_del_arte.md`](docs/estado_del_arte.md)):
> ninguna afirmación de novedad es definitiva.
>
> **Fase 0 (datos reales): viable.** Con los polígonos de cuenca de CAMELS‑COL, 306 de 346
> estaciones forman 18 cuencas independientes con ≥ 3 estaciones anidadas (error de área
> polígono vs. tabla: 0,76 %); 15 no tienen presas según GRanD v1.3. Detalle en
> [`docs/protocolo.md`](docs/protocolo.md) y [`results/fase0/`](results/fase0/).

---

## Empieza aquí

**[`notebooks/01_analisis_paso_a_paso.ipynb`](notebooks/01_analisis_paso_a_paso.ipynb)** explica
todo el trabajo en 12 pasos ejecutados, con ecuaciones, figuras y la interpretación de cada
resultado:

| Paso | Qué se hace | Pregunta que responde |
|---|---|---|
| 1 | Red fluvial como grafo dirigido | ¿Cómo se representa un río para calcular rápido? |
| 2 | Aporte lateral sintético | ¿Qué entra a cada tramo? |
| 3 | Operador Muskingum–Cunge diferenciable | ¿Cómo viaja el agua y qué papel juega *n*? |
| 4 | Verificación de conservación de masa | ¿La física se cumple exactamente? |
| 5 | Observaciones sintéticas (3 estaciones, media diaria) | ¿Qué datos tendríamos en Colombia? |
| 6 | Sensibilidad y Jacobiano | ¿Los datos "ven" la rugosidad? |
| 7 | Inversión de Tikhonov (estilo SimPEG) | ¿Qué *n* explica los datos? |
| 8 | Matriz de resolución | ¿Qué viene de los datos y qué del supuesto? |
| 9 | Diseño D‑óptimo de la red | ¿Dónde poner la próxima estación? |
| 10 | Inversión neuronal no supervisada | ¿Funciona el enfoque del reto MT‑1D? |
| 11 | Resultados agregados de E01 (12 redes) | ¿Se sostienen las hipótesis? |
| 12 | Siguiente paso con datos reales | ¿Qué falta para usar IDEAM/CAMELS‑COL? |

## Motivación

- **Pocas series útiles.** CAMELS‑COL conservó **347 de 921** estaciones de IDEAM con registros
  aprovechables. La Amazonía y la Orinoquía están poco instrumentadas
  ([Jiménez et al., ESSD preprint](https://essd.copernicus.org/preprints/essd-2025-200/)).
- **El aprendizaje diferenciable ya invierte parámetros de ruteo**
  ([Bindas et al., 2024, *WRR*](https://doi.org/10.1029/2023WR035337)). Pero no se ha medido,
  tramo por tramo, **cuánto de lo aprendido viene de los datos y cuánto de los supuestos**.
- **Instalar una estación cuesta.** Hoy esa decisión se apoya en criterios de entropía, de redes
  complejas o en criterios administrativos, no en la información que aporta a un modelo físico.

## Enfoque

    aporte lateral q ─► [ Muskingum–Cunge diferenciable G(m) ] ─► caudal diario en estaciones d
                             m = log n (rugosidad de Manning por tramo)

    Inversión:   min  ‖W_d (P·G(m) − d_obs)‖² + β (α_s‖m − m_ref‖² + α_x‖D(m − m_ref)‖²)
    Resolución:  R = (JᵀW_d²J + βW_mᵀW_m)⁻¹ JᵀW_d²J        diag(R) ∈ [0, 1] por tramo
    Diseño:      siguiente estación = argmax_c  log det(H + F_c)         (criterio D)

La correspondencia con cada sesión del curso
[`inversion-geofisica-python`](https://github.com/nvasquezc/inversion-geofisica-python) está en
[`docs/puente_inversion_geofisica.md`](docs/puente_inversion_geofisica.md).

## Resultado preliminar — E01 (sintético, 12 redes × 60 tramos)

Configuración: 40 días, paso horario, observaciones como **media diaria** (igual que IDEAM y
CAMELS‑COL), error del 5 % + 0,5 m³/s. Red base: 3 estaciones (la salida y las 2 mayores
subcuencas). A esa red se le agregan 4 estaciones con distintas estrategias.

| Configuración | RMSE de log *n* (media de 12 redes) |
|---|---|
| Solo el valor de referencia (sin datos) | 0,307 |
| Red base (3 estaciones) | 0,255 |
| + 4 estaciones aleatorias (5 sorteos por red) | 0,247 |
| + 4 estaciones en los ríos de mayor área | 0,248 |
| **+ 4 estaciones con diseño D‑óptimo** | **0,226** |

- **H2 (diseño) — apoyada.** El diseño D‑óptimo, calculado en el modelo de referencia (**sin
  conocer la verdad**), gana en **11 de 12 redes** frente a la heurística de mayor área y frente
  a la ubicación aleatoria.
  - Wilcoxon pareado unilateral: p = 7×10⁻⁴.
  - Diferencia media frente a mayor área: −0,021, con IC bootstrap al 95 % de [−0,031; −0,012].
    Es una reducción de ~8 % en el error.
- **H1 (resolución predice el error) — apoyo débil.** ρ de Spearman negativa en **12 de 12
  redes**, pero pequeña (mediana −0,15). El p = 5×10⁻⁵ de la figura agrupa los tramos de todas
  las redes, que no son independientes; no debe leerse como evidencia fuerte.
- **Hallazgo principal: identificabilidad baja.** Con caudal medio diario, solo el **13 %** de
  los tramos tiene diag(R) > 0,1 y menos del **1 %** supera 0,5. La mayor parte del campo de
  rugosidad lo determina la regularización, no los datos. Concuerda con Bindas et al. (2024):
  *n* "moderadamente" identificable. Los mapas de *n* aprendidos sin análisis de resolución
  deben interpretarse con cautela.

<p align="center">
<img src="results/e01_rmse_por_estrategia.png" width="46%">
<img src="results/e01_resolucion_vs_error.png" width="46%">
</p>

### Limitaciones de E01

- Celeridad lineal en el tiempo (fija alrededor de un caudal de referencia).
- Aporte lateral **sin error**.
- Redes sintéticas con geometría hidráulica ilustrativa, no calibrada para Colombia.
- Resolución linealizada.
- Una sola realización de ruido por red.

Cada limitación tiene un experimento previsto en [`docs/protocolo.md`](docs/protocolo.md).

## Reproducir

Requiere [uv](https://docs.astral.sh/uv/). Todo corre en CPU.

    uv sync --all-extras                                    # entorno y dependencias
    uv run pytest                                           # 14 pruebas, incluida la conservación de masa
    uv run python experiments/e00_inversion_una_red.py      # una inversión, ~15 s
    uv run python experiments/e01_identificabilidad_sintetica.py --redes 12 --aleatorios 5   # ~5 min
    uv run python scripts/construir_notebook.py             # genera el notebook
    uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_analisis_paso_a_paso.ipynb

## Garantía física verificada

`tests/test_nucleo.py` comprueba la continuidad discreta por tramo y en toda la red:

    Δt·½Σ[(I_t + I_{t+1}) − (O_t + O_{t+1})] = S_T − S_0

El error relativo es < 10⁻¹⁰. La conservación es una propiedad de la arquitectura, no un término
de penalización. Las pruebas también verifican el gradiente frente a diferencias finitas, la
causalidad del Jacobiano (un tramo no es sensible a parámetros aguas abajo), que diag(R) quede
en [0, 1] y que el criterio D del diseño sea monótono.

## Fase 0 con datos reales (reproducir)

Requiere el extra `geo` (`uv sync --all-extras`) y los datos descritos en
[`data/README.md`](data/README.md).

    uv run python scripts/descargar_camels_col.py            # Zenodo 18794895, verifica MD5
    uv run python scripts/fase0_anidamiento.py               # anidamiento por polígonos de cuenca
    uv run python scripts/resumen_sistemas_fase0.py          # sistemas de estaciones anidadas
    uv run python scripts/marcar_embalses.py --presas data/GRanD_Version_1_3/GRanD_dams_v1_3.shp

| Resultado | Valor |
|---|---|
| Estaciones con otra estación aguas abajo | 300 de 346 |
| Cuencas independientes con ≥ 3 estaciones anidadas | 18 (21 subsistemas con ≥ 10 años de registro común) |
| Error de área polígono vs. tabla (mediana) | 0,76 % |
| Estaciones con al menos una presa en su cuenca (GRanD v1.3) | 36 de 346 |
| Cuencas sin presas (grupo A) | 15, con 89 estaciones |
| Cuenca piloto para la Fase 2 | 31097010 (natural, 11 estaciones, 138 309 km²) |

Limitación: GRanD v1.3 (2019) no incluye Hidroituango; en el Cauca aguas abajo de Ituango se
excluye 2019–2022.

## Estructura

    src/ruteo_inverso/
      red.py          red fluvial como DAG; orden topológico; regularizador en el grafo
      ruteo.py        operador directo Muskingum–Cunge diferenciable (conserva masa)
      forzamiento.py  aporte lateral y rugosidad "verdadera" sintéticos
      inversion.py    Tikhonov con β‑cooling y discrepancia; inversión neuronal no supervisada
      resolucion.py   Jacobiano (autodiff), matriz de resolución, covarianza, diseño D/A‑óptimo
      datos.py        estaciones CAMELS‑COL sobre HydroRIVERS; detección de anidamiento
      graficos.py     dibujo de la red y estilo de figuras
    tests/            14 pruebas
    experiments/      E00 (una red) y E01 (12 redes); E02 y E03 planeados
    notebooks/        01_analisis_paso_a_paso.ipynb (empieza aquí)
    scripts/          construcción del notebook, descarga de datos y análisis de la Fase 0
    docs/             estado del arte, protocolo, puente con la inversión geofísica
    results/          figuras y JSON de E01; results/fase0/ con las tablas de anidamiento y embalses

## Utilidad para Colombia

El producto final previsto tiene dos partes:

1. Un **mapa de resolubilidad** de la red de aforo de IDEAM.
2. Un **ranking cuantitativo de sitios** donde una nueva estación aportaría más información al
   modelo de ruteo usado para pronóstico y alerta.

Ese ranking sirve para priorizar inversión en monitoreo hídrico (IDEAM, CAR, gestión del riesgo)
con un criterio reproducible.

## Origen y créditos

- El marco de inversión (operador directo, regularización, β‑cooling, inversión no supervisada
  con operador diferenciable) proviene del curso *Inversión geofísica en Python* (original de
  Anagabrielamantilla et al.; MINCIENCIAS–ANH–UIS). **No se reutiliza su código**, porque el
  curso no declara licencia abierta.
- Este proyecto nace de un cuaderno exploratorio previo de GNN "informadas por la física" sobre
  la red vial de Chapinero. Ese cuaderno usaba datos sintéticos derivados del grado de los nodos
  y una restricción de atenuación que no actúa a escala urbana. De ahí salió la pregunta que este
  repositorio aborda con un problema físico real: **¿cuándo la física impuesta por construcción
  aporta información que los datos por sí solos no dan?**

## Cita

Ver [`CITATION.cff`](CITATION.cff). Código bajo licencia MIT. Los datos conservan sus licencias
de origen (ver [`data/README.md`](data/README.md)).
