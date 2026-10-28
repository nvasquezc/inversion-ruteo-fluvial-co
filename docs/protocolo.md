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