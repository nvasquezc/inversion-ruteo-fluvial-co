# Estado del arte (Fase 0, revisión **preliminar**)

> **Estado (oct. 2026):** búsqueda exploratoria en la web, **no** es una revisión
> sistemática. Ninguna afirmación de "vacío" de este repositorio es definitiva hasta
> completar la búsqueda en Scopus y Web of Science con el protocolo del final de este
> documento.

## 1. Matriz de trabajos relacionados

| # | Trabajo | Qué hace | Física / conservación | Región / datos | Qué deja abierto (según los autores o por lectura directa) |
|---|---|---|---|---|---|
| 1 | Bindas et al. (2024), *WRR* 60, e2023WR035337, [doi](https://doi.org/10.1029/2023WR035337) | Muskingum–Cunge diferenciable; una red neuronal estima *n* de Manning por tramo a partir de atributos, entrenada solo con hidrogramas aguas abajo | Operador físico (conservación por construcción) | EE. UU. (Juniata) | La geometría del cauce **no es identificable**; *n* solo "moderadamente". Los valores absolutos de *n* dependen del periodo de entrenamiento. Beneficio demostrado en subcuencas > 2000 km². Sin análisis formal de resolución ni de diseño de red |
| 2 | Mosaffa et al. (2026), *HESS* 30, 2079, [pdf](https://hess.copernicus.org/articles/30/2079/2026/hess-30-2079-2026.pdf) | LSTM por subcuenca + GNN de ruteo (GCN, GAT, GraphSAGE, ChebNet) | **No** impone conservación de masa | Alto Danubio, 530 subcuencas (LamaH‑CE) | Ruteo "físicamente consistente" sin restricción de masa |
| 3 | Farmani et al. (2026), RiverGraphNet, [EGUsphere](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-4157/) | GAT sobre una red dirigida (4118 nodos) para rutear escorrentía de Noah‑MP | Los autores dicen "*not strictly mass‑conserving*" | Salt–Verde, Arizona, 23 estaciones | Una sola cuenca; piden formulaciones con conservación |
| 4 | Acosta et al. (2026), DUALFloodGNN, [IJCAI](https://www.ijcai.org/proceedings/2026/0713.pdf) | GNN nodo + arista para inundación 2D | Pérdidas **suaves** de masa, global y local | Wollombi (Australia), 56 eventos simulados con HEC‑RAS | Datos simulados; una cuenca; la pérdida global + local no siempre supera a la local sola |
| 5 | Farmani et al. (2026), [arXiv 2603.25093](https://arxiv.org/abs/2603.25093) | *Mass‑Conserving Perceptron* con procesos hidrológicos | Conservación **dura** | 15 cuencas de EE. UU. | Modelo agregado, sin red |
| 6 | Sun et al. (2022), *HESS* 26, 5163, [enlace](https://hess.copernicus.org/articles/26/5163/2022/) | GNN guiada por física (preentrenada con el NWM) + ajuste fino | Indirecta (emula un modelo físico) | East–Taylor y Gunnison, Colorado | Sin conservación explícita |
| 7 | Poudel & Steinschneider (2026), [EGUsphere](https://egusphere.copernicus.org/preprints/2026/egusphere-2026-756/egusphere-2026-756.pdf) | Parsimonia en modelos diferenciables (HBV + MLP/LSTM) | HBV | 531 cuencas CAMELS‑US | Interpretan la variabilidad de parámetros como equifinalidad, **sin** análisis formal de identificabilidad |
| 8 | Halverson & Fleming (2015), *HESS* 19, 3301, [enlace](https://hess.copernicus.org/articles/19/3301/2015/hess-19-3301-2015.html) | Diseño de la red de aforo con teoría de redes complejas (comunidades, intermediación) | No usa un modelo físico | Canadá | El diseño no se basa en la información sobre parámetros de un modelo |
| 9 | Diseño por entropía ([Entropy 2019](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7514323/)) | Diseño de la red de aforo maximizando la información de Shannon de las series | Sin modelo físico | Corea | Ídem |
| 10 | Jiménez et al., CAMELS‑COL ([ESSD preprint](https://essd.copernicus.org/preprints/essd-2025-200/), [Zenodo v3](https://zenodo.org/records/18794895)) | 347 cuencas colombianas, caudal diario de IDEAM, CHIRPS v2, MSWX, 1981–2022 | — | Colombia | No publica la topología de red ni dice cómo maneja las cuencas anidadas. Señala que la Amazonía y la Orinoquía están poco instrumentadas |

## 2. Posición tentativa del aporte

De lo revisado se desprende un **candidato** a vacío, que todavía hay que confirmar:

> No se encontró trabajo que (a) cuantifique formalmente, por tramo, la **resolución**
> (diag R) y la incertidumbre posterior de parámetros de ruteo aprendidos con un operador
> diferenciable que conserva la masa, ni que (b) use esa información para el **diseño
> óptimo de redes hidrométricas**, ni que (c) haga cualquiera de las dos cosas en ríos
> andino‑tropicales con datos de IDEAM.

Los trabajos 8 y 9 diseñan redes de aforo sin un modelo físico. Los trabajos 1 y 7 aprenden
parámetros sin un análisis formal de resolución. La combinación es el aporte candidato.

**Riesgos de que el vacío no exista:**

- La literatura de *data assimilation* y de diseño de observaciones (OSSE, *observing system
  simulation experiments*) en hidrología operativa podría cubrir (b). Hay que buscarla
  explícitamente.
- El grupo de C. Shen (Penn State) publica rápido sobre ruteo diferenciable. Hay que revisar
  su producción 2025–2026 completa.

## 3. Protocolo de búsqueda sistemática (pendiente de ejecutar)

Bases: Scopus, Web of Science; complemento: Google Scholar (primeras 200), arXiv, EGUsphere.
Periodo: 2015–2026. Idiomas: inglés, español, portugués.

    B1 ("differentiable" OR "physics-informed" OR "hybrid") AND ("river routing" OR "Muskingum" OR "flow routing")
    B2 ("graph neural network" OR "GNN") AND ("streamflow" OR "river network" OR "discharge") AND ("mass conserv*" OR "water balance")
    B3 ("gauge network design" OR "hydrometric network" OR "observing system simulation experiment") AND ("Fisher information" OR "optimal experimental design" OR "Bayesian design" OR "resolution matrix")
    B4 ("identifiab*" OR "equifinality") AND ("Manning" OR "roughness") AND ("routing" OR "river")
    B5 ("Colombia" OR "Andes" OR "Magdalena" OR "IDEAM") AND ("deep learning" OR "LSTM" OR "neural network") AND ("streamflow" OR "caudal")

Criterios de inclusión: método aplicado a redes fluviales (no solo cuencas agregadas), y
estimación de parámetros o diseño de redes de observación. Se documenta con un diagrama
PRISMA en `docs/prisma.md`.