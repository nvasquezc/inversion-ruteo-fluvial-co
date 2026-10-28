# Protocolo de investigación

## Pregunta

¿Qué parte de la red fluvial colombiana pueden "ver" las estaciones hidrométricas actuales
cuando se invierten parámetros de ruteo con un operador que conserva la masa?
¿Dónde debería instalarse la próxima estación para maximizar lo que se aprende de la red?

## Hipótesis (todas falsables)

| ID | Hipótesis | Prueba | Se rechaza si |
|---|---|---|---|
| H1 | La resolución linealizada diag(R), calculada **sin conocer la verdad**, predice qué tramos se recuperan bien | Spearman entre diag(R) y \|m̂ − m\| en redes sintéticas | ρ ≥ 0, o p > 0.05 sobre todas las redes |
| H2 | Agregar estaciones con diseño D‑óptimo mejora la recuperación de *n* más que (i) aforar los ríos de mayor área y (ii) ubicarlas al azar | Wilcoxon pareado entre redes (≥ 10 redes), efecto = diferencia media de RMSE | p > 0.05 o diferencia media ≥ 0 |
| H3 | Con datos reales (CAMELS‑COL), el ruteo con conservación de masa por construcción supera a una GNN sin física y a una GNN con penalización suave **en estaciones internas no usadas en el entrenamiento** y en eventos extremos (La Niña 2010–11) | KGE y error de pico en las estaciones retenidas; Wilcoxon entre estaciones | Sin diferencia significativa o peor desempeño |
| H4 | La desviación posterior linealizada está calibrada | Cobertura de intervalos al 90 % frente a ensembles o MCMC (sintético) | Cobertura fuera de [0.8, 0.97] |
| H5 | La resolución por tramo crece con el área de drenaje y la longitud del registro | Regresión de diag(R) contra área y años de datos | Pendiente no significativa |

## Fases y puntos de decisión

**Fase 0 — Viabilidad.**

*Decisión de datos: CERRADA (28 oct. 2026) — VIABLE.* Script `scripts/fase0_anidamiento.py`
sobre los polígonos de cuenca de CAMELS‑COL v3 (umbral de contención 0,9; error de área
polígono vs. tabla: mediana 0,76 %):

- 306 de 346 estaciones forman **18 cuencas independientes** con ≥ 3 estaciones anidadas
  (21 subsistemas si se exige ≥ 10 años de registro común entre estaciones conectadas).
- Cruce con GRanD v1.3 (`scripts/marcar_embalses.py`): 36 de 346 estaciones tienen al menos
  una presa en su cuenca.
- **Grupo A (natural, 15 cuencas, 89 estaciones).** Para la Fase 2 se usan las de ≥ 7
  estaciones: 52017010 (14), 11077010 (12), 31097010 (11; 138 309 km²), 16067010 (8),
  47030010 (7). Las de 3–5 estaciones quedan para validación y H5.
- **Grupo B (regulada, 3 cuencas).** Magdalena‑Cauca (29037020; 176 estaciones, 25 reguladas),
  35257040 (40 estaciones, 4 reguladas: Chivor, Guavio, Golillas) y Sinú (13067020; Urrá I
  desde 2000). Tratamiento: (i) subcuencas sin presas aguas arriba como naturales;
  (ii) caudal observado aguas abajo de presa como condición de frontera; (iii) periodos
  previos a la presa (Sinú antes de 2000, Sogamoso antes de 2015).
- **Limitaciones registradas:** GRanD v1.3 (2019) no incluye Hidroituango; en el Cauca aguas
  abajo de Ituango se excluye 2019–2022. Falta el grado de regulación (DOR = capacidad /
  volumen anual) para decidir si 35257040 puede tratarse como natural.

*Decisión de literatura: PENDIENTE.* Revisión sistemática según `docs/estado_del_arte.md` §3.
Si encuentra un trabajo que ya hace H1 + H2 con un operador diferenciable, el aporte pasa a
ser la aplicación a Colombia y la validación (H3, H5).

**Piloto de la Fase 2:** cuenca 31097010 (natural, 11 estaciones, 138 309 km², mediana de 36
años de registro común). Se elige por escala: E01 mostró que la resolución con datos
diarios se concentra en los tramos de mayor área.

**Fase 1 — Sintético (en curso).** Experimento E01: H1 y H2 con un modelo lineal en el
tiempo. Siguientes:

- E02: celeridad no lineal (dependiente del caudal) y aporte lateral con error.
- E03: H4 con ensembles o MCMC.

**Fase 2 — Datos reales.**

- Aporte lateral: un LSTM lluvia‑escorrentía entrenado en CAMELS‑COL (CHIRPS v2, MSWX).
- Inversión de *n* con el operador diferenciable.
- Validación en estaciones internas retenidas (H3).
- Periodos:
  - Calibración 1990–2005.
  - Validación 2006–2009.
  - Prueba: 2010–2011 (La Niña) y 2012–2022.

**Fase 3 — Producto y artículo.**

- Mapa de resolubilidad de la red de aforo y ranking de sitios candidatos para nuevas
  estaciones.
- Preprint en EGUsphere/ESSOAr. Revistas objetivo: *HESS*, *WRR*, *Environmental
  Modelling & Software*, *J. Hydrology: Regional Studies*.

## Métricas y estadística

- Parámetros (sintético): RMSE de log *n*, diag(R) y cobertura de los intervalos.
- Caudal: KGE, NSE, error de pico (%), error de tiempo al pico (días), FHV y FLV.
- Comparaciones: Wilcoxon pareado entre redes o estaciones, con tamaño de efecto y
  bootstrap de la diferencia media. No se reportan p‑valores con menos de 6 unidades
  pareadas.
- Semillas: se repite todo con ≥ 5 semillas de inicialización.

## Amenazas a la validez

1. **Linealización.** diag(R) y la covarianza son locales. H4 las verifica.
2. **Modelo lineal en el tiempo.** La celeridad fija subestima la no linealidad en
   crecientes. Se aborda en E02.
3. **Error en el aporte lateral.** En datos reales, CHIRPS subestima la lluvia en algunas
   cuencas (lo señalan los autores de CAMELS‑COL). Ese error se confunde con *n*. Hay que
   invertirlo conjuntamente o propagarlo.
4. **Embalses y extracciones.** Los caudales regulados (p. ej. Betania, Hidroituango,
   Guavio) violan el supuesto de ruteo natural. Esas estaciones se excluyen o se marcan.
5. **Curvas de gasto.** El error de IDEAM puede ser > 5 % en crecientes. Se hace un
   análisis de sensibilidad al ruido de 5, 10 y 20 %.
6. **Sesgo de ubicación.** Las estaciones están en ríos grandes y accesibles. Es justamente
   lo que H2 cuestiona.
