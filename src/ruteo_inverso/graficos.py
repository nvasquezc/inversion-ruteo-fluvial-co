"""Figuras del proyecto con calidad de publicación (Plotly ``graph_objects``).

Criterios, tomados de las guías de figuras de Copernicus (HESS) y AGU (WRR):

* sin título dentro de la figura: el título y la explicación van en la leyenda
  de la figura (pie de figura), fuera de la imagen;
* paneles rotulados (a), (b), ... con ejes en caja, marcas hacia afuera y sin rejilla;
* una sola familia tipográfica, tamaños de 11–13 pt, tinta casi negra;
* colores categóricos de Okabe e Ito (2008), seguros para daltonismo;
* mapas de color secuenciales perceptualmente uniformes, de un tono, en el
  espíritu de los *scientific colour maps* de Crameri (2018): claro = poco;
* mapas con barra de escala; la red sintética se dibuja en planta, como un río.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from plotly.subplots import make_subplots

from .red import RedFluvial

# ============================================================================ estilo
FUENTE = "Arial, Helvetica, sans-serif"
TINTA = "#1a1a1a"
TINTA_2 = "#555555"
GRIS = "#9a9a9a"
GRIS_CLARO = "#d9d9d9"
BLANCO = "#ffffff"

# Okabe & Ito (2008). Universal design: colour-blind-safe categorical palette.
OI_NEGRO, OI_NARANJA, OI_CELESTE, OI_VERDE = "#000000", "#E69F00", "#56B4E9", "#009E73"
OI_AMARILLO, OI_AZUL, OI_BERMELLON, OI_PURPURA = "#F0E442", "#0072B2", "#D55E00", "#CC79A7"

COLOR_ESTRATEGIA = {"D-óptimo": OI_AZUL, "Mayor área": OI_BERMELLON, "Aleatorio": GRIS}
COLOR_METODO = {"Tikhonov": OI_AZUL, "Neuronal": OI_BERMELLON, "Referencia": GRIS}
COLOR_ESTACION = [OI_AZUL, OI_BERMELLON, OI_VERDE]

# Secuenciales de un tono (blanco → color), perceptualmente ordenadas.
AGUA = [[0.0, "#f4f7fb"], [0.15, "#d7e3f1"], [0.35, "#a9c3e1"], [0.55, "#6f9bcb"],
        [0.75, "#3a6faa"], [0.9, "#1d4b80"], [1.0, "#0b2a50"]]
ERROR = [[0.0, "#fdf6ec"], [0.15, "#f9e2c2"], [0.35, "#f2bd85"], [0.55, "#e48c4f"],
         [0.75, "#c65a2e"], [0.9, "#913519"], [1.0, "#5a1d0b"]]
GRISES = [[0.0, "#f2f2f2"], [1.0, "#5e5e5e"]]

RECURSOS = Path(__file__).parent / "recursos"


def recortar(escala, desde: float = 0.12, pasos: int = 11):
    """Sub-escala [desde, 1] de una escala de color (evita el blanco puro sobre fondo blanco)."""
    t = np.linspace(0, 1, pasos)
    return [[float(a), c] for a, c in zip(t, sample_colorscale(escala, list(desde + (1 - desde) * t)), strict=True)]


def rgba(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def km2(x: float) -> str:
    """Área con separador de miles en espacio (convención SI): 138 309 km²."""
    return f"{x:,.0f}".replace(",", " ") + " km²"


def lienzo(filas: int = 1, columnas: int = 1, **kw) -> go.Figure:
    if filas == 1 and columnas == 1:
        return go.Figure()
    kw.setdefault("horizontal_spacing", 0.1)
    kw.setdefault("vertical_spacing", 0.12)
    return make_subplots(rows=filas, cols=columnas, **kw)


def _caja(eje, tipo: str = "x"):
    eje.update(showline=True, linecolor=TINTA, linewidth=0.8, mirror="ticks", ticks="outside",
               ticklen=4, tickwidth=0.8, tickcolor=TINTA, showgrid=False, zeroline=False,
               tickfont=dict(size=11.5, color=TINTA, family=FUENTE),
               title=dict(font=dict(size=12.5, color=TINTA, family=FUENTE), standoff=6))


def publicar(fig: go.Figure, ancho: int = 760, alto: int = 420, margen: dict | None = None,
             leyenda: dict | None = None) -> go.Figure:
    """Estilo de publicación: fondo blanco, ejes en caja, sin rejilla ni título."""
    m = dict(l=62, r=18, t=30, b=50)
    if margen:
        m.update(margen)
    ley = dict(x=0.99, y=0.98, xanchor="right", yanchor="top", bgcolor="rgba(255,255,255,0.92)",
               bordercolor=TINTA, borderwidth=0.6, font=dict(size=11, color=TINTA, family=FUENTE),
               itemsizing="constant", tracegroupgap=2)
    if leyenda:
        ley.update(leyenda)
    fig.update_layout(template="simple_white", width=ancho, height=alto, paper_bgcolor=BLANCO,
                      plot_bgcolor=BLANCO, margin=m, separators=". ", legend=ley,
                      font=dict(family=FUENTE, size=12, color=TINTA),
                      hoverlabel=dict(bgcolor=BLANCO, bordercolor=GRIS,
                                      font=dict(family=FUENTE, size=12, color=TINTA)))
    for e in fig.select_xaxes():
        if e.visible is not False:
            _caja(e)
    for e in fig.select_yaxes():
        if e.visible is not False:
            _caja(e)
    return fig


def rotular(fig: go.Figure, textos: Sequence[str], ejes: Sequence[str] | None = None) -> None:
    """Rótulos de panel «(a) descripción» sobre la esquina superior izquierda de cada panel."""
    ejes = ejes or [("x" if i == 0 else f"x{i + 1}") for i in range(len(textos))]
    letras = "abcdefghij"
    for i, (t, ex) in enumerate(zip(textos, ejes, strict=True)):
        ey = ex.replace("x", "y")
        fig.add_annotation(text=f"<b>({letras[i]})</b> {t}" if t else f"<b>({letras[i]})</b>",
                           xref=f"{ex} domain", yref=f"{ey} domain", x=0, y=1, xanchor="left",
                           yanchor="bottom", yshift=5, showarrow=False, align="left",
                           font=dict(size=12.5, color=TINTA, family=FUENTE))


def barra_color(titulo: str, x: float = 1.01, y: float = 0.5, largo: float = 0.75, **kw) -> dict:
    d = dict(title=dict(text=titulo, side="right", font=dict(size=11.5, color=TINTA, family=FUENTE)),
             thickness=10, len=largo, x=x, y=y, yanchor="middle", outlinewidth=0.8, outlinecolor=TINTA,
             ticks="outside", ticklen=3, tickwidth=0.8, tickcolor=TINTA,
             tickfont=dict(size=11, color=TINTA, family=FUENTE))
    d.update(kw)
    return d


# ============================================================================ red en planta
def trazado_planta(red: RedFluvial, semilla: int = 7) -> list[np.ndarray]:
    """Dibuja la red en planta, como una cuenca: cada tramo es una polilínea (km) que
    va de su confluencia aguas abajo hacia aguas arriba, con meandros suaves.

    Disposición radial: cada tramo recibe un sector angular proporcional a sus
    cabeceras, de modo que los tributarios no se cruzan. La longitud de cada tramo
    es la real; la orientación es solo una elección de dibujo."""
    n = red.n
    hijos: list[list[int]] = [[] for _ in range(n)]
    for i, j in enumerate(red.aguas_abajo):
        if j >= 0:
            hijos[j].append(i)
    hojas = np.ones(n)
    for i in range(n):  # orden topológico: los afluentes tienen índice menor
        if hijos[i]:
            hojas[i] = sum(hojas[h] for h in hijos[i])
    L = red.longitud_m / 1e3
    rng = np.random.default_rng(semilla)
    base = np.zeros((n, 2))
    sector = np.zeros((n, 2))
    ang = np.zeros(n)
    salida = int(np.where(red.aguas_abajo < 0)[0][0])
    sector[salida] = (np.deg2rad(8), np.deg2rad(172))
    ang[salida] = np.pi / 2
    trazos: list[np.ndarray] = [np.zeros((2, 2))] * n
    for i in range(n - 1, -1, -1):
        p0 = base[i]
        th = ang[i]
        p1 = p0 + L[i] * np.array([np.cos(th), np.sin(th)])
        t = np.linspace(0, 1, 24)
        normal = np.array([-np.sin(th), np.cos(th)])
        amp = 0.035 * L[i] * rng.uniform(0.6, 1.2)
        f, fase = rng.uniform(0.8, 1.6), rng.uniform(0, 2 * np.pi)
        desv = amp * np.sin(np.pi * t) * np.sin(2 * np.pi * f * t + fase)
        trazos[i] = p0[None, :] + t[:, None] * (p1 - p0)[None, :] + desv[:, None] * normal[None, :]
        a0, a1 = sector[i]
        tot = sum(hojas[h] for h in hijos[i])
        acum = a0
        orden = sorted(hijos[i], key=lambda h: -hojas[h])
        orden = orden[1::2][::-1] + orden[0::2]  # el más grande al centro
        for h in orden:
            ancho = (a1 - a0) * hojas[h] / tot
            sector[h] = (acum, acum + ancho)
            medio = acum + ancho / 2
            ang[h] = 0.8 * medio + 0.2 * th
            if len(hijos[i]) > 1 and h != max(hijos[i], key=lambda c: hojas[c]):
                # afluente: al menos 28° respecto al cauce que lo recibe, hacia su sector
                d = ang[h] - th
                ang[h] = th + np.sign(d if d != 0 else 1) * max(abs(d), np.deg2rad(28))
            base[h] = p1
            acum += ancho
    return trazos


def _contorno_cuenca(trazos, red: RedFluvial):
    try:
        from shapely.geometry import LineString
        from shapely.ops import unary_union
    except ImportError:
        return None
    A = red.area_drenaje_km2()
    w = 3.5 + 6 * np.sqrt(A / A.max())
    forma = unary_union([LineString(t).buffer(wi) for t, wi in zip(trazos, w, strict=True)])
    forma = forma.buffer(12, join_style=1).buffer(-7, join_style=1).simplify(0.4)
    return np.asarray(forma.exterior.coords) if forma.geom_type == "Polygon" else None


def agregar_red(fig: go.Figure, red: RedFluvial, valores=None, *, fila=None, col=None,
                escala=AGUA, cmin=None, cmax=None, etiqueta="", formato=".2f",
                estaciones: Iterable[int] = (), nuevas: Iterable[int] = (),
                color_nuevas: str = OI_AZUL, nombre_nuevas: str = "Estación propuesta",
                barra: dict | None = None, leyenda: bool = True, escala_km: float | None = 50,
                trazos=None) -> None:
    """Red en planta: contorno de cuenca, cauces con grosor ∝ √área y color ∝ ``valores``."""
    trazos = trazos if trazos is not None else trazado_planta(red)
    A = red.area_drenaje_km2()
    ancho = 0.9 + 6.2 * np.sqrt(A / A.max())
    pos = dict(row=fila, col=col) if fila is not None else {}

    borde = _contorno_cuenca(trazos, red)
    if borde is not None:
        fig.add_trace(go.Scatter(x=borde[:, 0], y=borde[:, 1], mode="lines", fill="toself",
                                 fillcolor="#f5f5f3", line=dict(color="#b8b8b5", width=0.8),
                                 hoverinfo="skip", showlegend=False), **pos)

    if valores is not None:
        v = np.asarray(valores, dtype=float)
        lo = float(np.nanmin(v)) if cmin is None else cmin
        hi = float(np.nanmax(v)) if cmax is None else cmax
        tt = np.clip((v - lo) / (hi - lo if hi > lo else 1.0), 0, 1)
        escala = recortar(escala)
        colores = sample_colorscale(escala, list(tt))
    else:
        v, colores = None, ["#3a6faa"] * red.n

    # de menor a mayor área: los cauces grandes quedan encima
    for i in np.argsort(A):
        tr = trazos[i]
        dato = f"<br>{etiqueta}: %{{customdata:{formato}}}" if v is not None else ""
        fig.add_trace(go.Scatter(
            x=tr[:, 0], y=tr[:, 1], mode="lines", line=dict(color=colores[i], width=ancho[i]),
            customdata=np.full(len(tr), v[i]) if v is not None else None, showlegend=False,
            hovertemplate=f"<b>Tramo {i}</b><br>Área de drenaje: {km2(A[i])}{dato}<extra></extra>"), **pos)

    def marcar(lista, color, nombre, simbolo, tam):
        lista = list(lista)
        if not lista:
            return
        xy = np.array([trazos[e][0] for e in lista])  # extremo aguas abajo del tramo
        fig.add_trace(go.Scatter(
            x=xy[:, 0], y=xy[:, 1], mode="markers", name=nombre, showlegend=leyenda,
            legendgroup=nombre, marker=dict(symbol=simbolo, size=tam, color=color,
                                            line=dict(color=BLANCO, width=1.2)),
            customdata=lista, hovertemplate=f"{nombre}: tramo %{{customdata}}<extra></extra>"), **pos)

    marcar(estaciones, OI_NEGRO, "Estación existente", "triangle-up", 11)
    marcar(nuevas, color_nuevas, nombre_nuevas, "triangle-up", 12)

    if v is not None and barra is not None:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", showlegend=False, hoverinfo="skip",
                                 marker=dict(colorscale=escala, cmin=lo, cmax=hi, color=[lo],
                                             showscale=True, colorbar=barra)), **pos)

    todos = np.vstack(trazos)
    if borde is not None:
        todos = np.vstack([todos, borde])
    x0, x1 = todos[:, 0].min(), todos[:, 0].max()
    y0, y1 = todos[:, 1].min(), todos[:, 1].max()
    pad = 0.04 * max(x1 - x0, y1 - y0)
    if escala_km:
        xs, ys = x0 + pad * 0.3, y0 - pad * 0.2
        fig.add_trace(go.Scatter(x=[xs, xs, xs, xs + escala_km, xs + escala_km, xs + escala_km],
                                 y=[ys + pad * 0.25, ys, ys, ys, ys, ys + pad * 0.25], mode="lines",
                                 line=dict(color=TINTA, width=1.2), hoverinfo="skip", showlegend=False), **pos)
        fig.add_trace(go.Scatter(x=[xs + escala_km / 2], y=[ys + pad * 0.35], mode="text",
                                 text=[f"{escala_km:g} km"], textposition="top center",
                                 textfont=dict(size=11, color=TINTA, family=FUENTE),
                                 hoverinfo="skip", showlegend=False), **pos)
        y0 = ys - pad * 0.2
    fig.update_xaxes(visible=False, range=[x0 - pad, x1 + pad], **pos)
    fig.update_yaxes(visible=False, range=[y0 - pad, y1 + pad], **pos)
    # misma escala en x e y (mapa sin deformar)
    ejes_x = [e for e in fig.select_xaxes(**({"row": fila, "col": col} if fila else {}))]
    if ejes_x:
        nombre_x = ejes_x[0].plotly_name.replace("axis", "")
        fig.update_yaxes(scaleanchor=nombre_x, scaleratio=1, **pos)


def dominio(fig: go.Figure, eje: str = "x"):
    """Dominio [inicio, fin] en coordenadas paper de un eje («x», «x2», «y3», ...)."""
    nombre = eje.replace("x", "xaxis").replace("y", "yaxis")
    return fig.layout[nombre].domain


# ============================================================================ figuras del cuaderno
def figura_red(red: RedFluvial, salida: int) -> go.Figure:
    A = red.area_drenaje_km2()
    fig = lienzo()
    ticks = [v for v in (100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000) if A.min() <= v <= A.max()]
    agregar_red(fig, red, np.log10(A), escala=AGUA, etiqueta="log₁₀ área [km²]", formato=".2f",
                estaciones=[salida], leyenda=False,
                barra=barra_color("Área de drenaje [km²]", x=0.98, largo=0.7, tickvals=list(np.log10(ticks)),
                                  ticktext=[f"{v:,}".replace(",", " ") for v in ticks]))
    fig.add_annotation(x=0, y=0, text="Salida", showarrow=True, ax=34, ay=18, arrowwidth=0.8,
                       arrowhead=0, font=dict(size=11.5, color=TINTA))
    return publicar(fig, ancho=720, alto=540, margen=dict(l=10, r=80, t=10, b=10))


def figura_aporte(t_dias, q, cabeceras, A) -> go.Figure:
    fig = lienzo()
    for k, i in enumerate(cabeceras):
        fig.add_trace(go.Scatter(x=t_dias, y=np.asarray(q[:, i]), mode="lines", name=f"Tramo {i} ({km2(A[i])})",
                                 line=dict(color=COLOR_ESTACION[k], width=1.5),
                                 hovertemplate=f"Tramo {i}<br>día %{{x:.2f}}: %{{y:.2f}} m³/s<extra></extra>"))
    publicar(fig, ancho=760, alto=330)
    fig.update_xaxes(title_text="Tiempo [d]", range=[0, float(t_dias[-1])])
    fig.update_yaxes(title_text="Aporte lateral q [m³ s⁻¹]", rangemode="tozero")
    return fig


def figura_ruteo(t10, exceso, mostrar, A, t_dias, salidas: dict) -> go.Figure:
    fig = lienzo(1, 2, horizontal_spacing=0.11)
    for k, i in enumerate(mostrar):
        fig.add_trace(go.Scatter(x=t10, y=exceso[:, i], mode="lines", line=dict(color=COLOR_ESTACION[k], width=1.6),
                                 name=f"Tramo {i} ({km2(A[i])})", legend="legend",
                                 hovertemplate=f"Tramo {i}<br>día %{{x:.2f}}: %{{y:.1f}} m³/s<extra></extra>"), 1, 1)
    estilos = {0.5: ("dash", TINTA), 1.0: ("solid", TINTA), 2.0: ("dot", TINTA)}
    for f, y in salidas.items():
        d, c = estilos[f]
        fig.add_trace(go.Scatter(x=t_dias, y=y, mode="lines", line=dict(color=c, width=1.4, dash=d),
                                 name=f"n × {f:g}", legend="legend2",
                                 hovertemplate=f"n × {f:g}<br>día %{{x:.2f}}: %{{y:.0f}} m³/s<extra></extra>"), 1, 2)
    publicar(fig, ancho=980, alto=380, margen=dict(t=34))
    fig.update_layout(legend2=fig.layout.legend.to_plotly_json() | dict(x=0.99, y=0.98, xanchor="right"))
    fig.update_layout(legend=dict(x=dominio(fig, "x")[1] - 0.01, xanchor="right"))
    fig.update_xaxes(title_text="Tiempo [d]", range=[0.8, 4], row=1, col=1)
    fig.update_xaxes(title_text="Tiempo [d]", range=[5, 25], row=1, col=2)
    fig.update_yaxes(title_text="Respuesta al pulso [m³ s⁻¹]", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title_text="Caudal en la salida [m³ s⁻¹]", row=1, col=2)
    rotular(fig, ["Pulso de 6 h en la cabecera", "Rugosidad escalada en toda la red"])
    return fig


def figura_masa(t, entra, sale, dS, err_tramo) -> go.Figure:
    fig = lienzo(1, 2, column_widths=[0.62, 0.38], horizontal_spacing=0.12)
    fig.add_trace(go.Scatter(x=t, y=entra, mode="lines", name="Entra (aporte lateral)",
                             line=dict(color=TINTA, width=2.2)), 1, 1)
    fig.add_trace(go.Scatter(x=t, y=sale + dS, mode="lines", name="Sale + ΔS",
                             line=dict(color=OI_NARANJA, width=1.4, dash="dash")), 1, 1)
    fig.add_trace(go.Scatter(x=t, y=sale, mode="lines", name="Sale por la salida",
                             line=dict(color=OI_AZUL, width=1.3)), 1, 1)
    fig.add_trace(go.Scatter(x=t, y=dS, mode="lines", name="Almacenamiento ΔS",
                             line=dict(color=OI_VERDE, width=1.3)), 1, 1)
    e = np.asarray(err_tramo, dtype=float)
    e = np.where(e > 0, e, 1e-18)
    rng = np.random.default_rng(0)
    fig.add_trace(go.Scatter(x=rng.uniform(-0.25, 0.25, len(e)), y=e, mode="markers", showlegend=False,
                             marker=dict(size=5, color=OI_AZUL, opacity=0.75, line=dict(width=0)),
                             hovertemplate="error relativo %{y:.1e}<extra></extra>"), 1, 2)
    eps = float(np.finfo(float).eps)
    fig.add_trace(go.Scatter(x=[-0.5, 0.5], y=[eps, eps], mode="lines", showlegend=False,
                             line=dict(color=TINTA, width=0.9, dash="dot"), hoverinfo="skip"), 1, 2)
    fig.add_annotation(x=0.48, y=np.log10(eps), xref="x2", yref="y2", text="ε de máquina",
                       showarrow=False, xanchor="right", yanchor="bottom", font=dict(size=11, color=TINTA_2))
    publicar(fig, ancho=980, alto=380, margen=dict(t=34),
             leyenda=dict(x=0.02, xanchor="left", y=0.98))
    fig.update_xaxes(title_text="Tiempo [d]", range=[0, float(t[-1])], row=1, col=1)
    fig.update_yaxes(title_text="Volumen acumulado [km³]", rangemode="tozero", row=1, col=1)
    fig.update_xaxes(range=[-0.5, 0.5], showticklabels=False, ticks="", title_text="60 tramos", row=1, col=2)
    fig.update_yaxes(type="log", title_text="Error relativo de continuidad", exponentformat="power",
                     range=[-18, -10], dtick=2, row=1, col=2)
    rotular(fig, ["Balance de la red completa", "Cierre por tramo"])
    return fig


def figura_observaciones(t_dias, O, dias, d_obs, sigma, estaciones, A) -> go.Figure:
    k_ = len(estaciones)
    fig = lienzo(k_, 1, shared_xaxes=True, vertical_spacing=0.07)
    for k, e in enumerate(estaciones):
        fig.add_trace(go.Scatter(x=t_dias, y=np.asarray(O[:, e]), mode="lines", name="Caudal horario (verdad)",
                                 line=dict(color=GRIS, width=1.1), showlegend=(k == 0), legendgroup="v",
                                 hoverinfo="skip"), k + 1, 1)
        fig.add_trace(go.Scatter(
            x=dias, y=np.asarray(d_obs[:, k]), mode="markers", name="Media diaria observada ± 1σ",
            showlegend=(k == 0), legendgroup="o",
            marker=dict(size=4.5, color=TINTA),
            error_y=dict(type="data", array=np.asarray(sigma[:, k]), color=TINTA, thickness=0.8, width=0),
            hovertemplate=f"Tramo {e}<br>día %{{x:.1f}}: %{{y:.0f}} m³/s<extra></extra>"), k + 1, 1)
    publicar(fig, ancho=900, alto=170 * k_ + 90, margen=dict(t=34),
             leyenda=dict(orientation="h", x=1, xanchor="right", y=1.0, yanchor="bottom", yref="paper",
                          borderwidth=0, bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(range=[0, float(t_dias[-1])])
    fig.update_xaxes(title_text="Tiempo [d]", row=k_, col=1)
    for k in range(k_):
        fig.update_yaxes(title_text="Q [m³ s⁻¹]", rangemode="tozero", row=k + 1, col=1)
    rotular(fig, [f"Estación en el tramo {e} ({km2(A[e])})" for e in estaciones],
            ["x"] + [f"x{k + 1}" for k in range(1, k_)])
    return fig


def figura_barrido(factores, phis, N) -> go.Figure:
    banda = (N - 2 * np.sqrt(2 * N), N + 2 * np.sqrt(2 * N))
    fig = lienzo()
    xb = [0.38, 2.65]
    fig.add_trace(go.Scatter(x=xb + xb[::-1], y=[banda[0]] * 2 + [banda[1]] * 2, fill="toself", mode="lines",
                             line=dict(width=0), fillcolor="rgba(0,0,0,0.08)", hoverinfo="skip",
                             name="N ± 2√(2N)"))
    fig.add_trace(go.Scatter(x=factores, y=phis, mode="lines+markers", name="φ<sub>d</sub>",
                             line=dict(color=OI_AZUL, width=1.6),
                             marker=dict(size=5.5, color=OI_AZUL, line=dict(color=BLANCO, width=0.8)),
                             hovertemplate="factor %{x:.2f}<br>φ_d = %{y:,.0f}<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=TINTA, width=0.8, dash="dot"))
    publicar(fig, ancho=640, alto=380, leyenda=dict(x=0.5, xanchor="center", y=0.98))
    fig.update_xaxes(type="log", title_text="Factor aplicado a n en todos los tramos",
                     tickvals=[0.4, 0.5, 0.7, 1, 1.4, 2, 2.5], range=[np.log10(0.38), np.log10(2.65)])
    fig.update_yaxes(type="log", title_text="Desajuste φ<sub>d</sub>",
                     tickvals=[50, 100, 200, 500, 1000, 2000], ticktext=["50", "100", "200", "500", "1000", "2000"],
                     range=[np.log10(min(phis.min(), banda[0]) * 0.75), np.log10(phis.max() * 1.3)])
    return fig


def figura_sensibilidad(red, sens, estaciones) -> go.Figure:
    trazos = trazado_planta(red)
    k_ = len(estaciones)
    fig = lienzo(1, k_, horizontal_spacing=0.02)
    for k, e in enumerate(estaciones):
        s = np.asarray(sens[k], dtype=float)
        agregar_red(fig, red, s / s.max(), fila=1, col=k + 1, escala=AGUA, cmin=0, cmax=1,
                    etiqueta="sensibilidad relativa", estaciones=[e], leyenda=False, trazos=trazos,
                    barra=barra_color("Sensibilidad relativa", x=1.0, largo=0.8) if k == k_ - 1 else None,
                    escala_km=50 if k == 0 else None)
    publicar(fig, ancho=1120, alto=360, margen=dict(l=6, r=80, t=30, b=6))
    rotular(fig, [f"Estación en el tramo {e}" for e in estaciones], ["x"] + [f"x{k + 1}" for k in range(1, k_)])
    return fig


def figura_tikhonov(red, verdad, estimado, m_ref, error, estaciones) -> go.Figure:
    fig = lienzo(1, 2, column_widths=[0.42, 0.58], horizontal_spacing=0.09)
    lim = [float(np.log(0.018)), float(np.log(0.07))]
    fig.add_trace(go.Scatter(x=lim, y=lim, mode="lines", name="1:1", line=dict(color=TINTA, width=0.8),
                             hoverinfo="skip"), 1, 1)
    fig.add_trace(go.Scatter(x=lim, y=[m_ref] * 2, mode="lines", name="Referencia m<sub>ref</sub>",
                             line=dict(color=TINTA, width=0.9, dash="dash"), hoverinfo="skip"), 1, 1)
    fig.add_trace(go.Scatter(x=verdad, y=estimado, mode="markers", name="Tikhonov",
                             marker=dict(size=6.5, color=OI_AZUL, line=dict(color=BLANCO, width=0.7)),
                             customdata=np.arange(len(verdad)),
                             hovertemplate="Tramo %{customdata}<br>verdadero %{x:.3f}<br>estimado %{y:.3f}<extra></extra>"),
                  1, 1)
    agregar_red(fig, red, error, fila=1, col=2, escala=ERROR, cmin=0, etiqueta="|error|", formato=".3f",
                estaciones=estaciones, leyenda=False,
                barra=barra_color("|log n̂ − log n|", x=1.0, largo=0.8))
    publicar(fig, ancho=1040, alto=430, margen=dict(r=80, t=34),
             leyenda=dict(x=dominio(fig, "x")[0] + 0.01, xanchor="left", y=0.98))
    fig.update_xaxes(title_text="log n verdadero", range=lim, row=1, col=1)
    fig.update_yaxes(title_text="log n estimado", range=lim, row=1, col=1)
    rotular(fig, ["Recuperación tramo a tramo", "Error absoluto (▲ estación)"])
    return fig


def figura_resolucion(red, dR, A, estaciones) -> go.Figure:
    fig = lienzo(1, 2, column_widths=[0.58, 0.42], horizontal_spacing=0.16)
    agregar_red(fig, red, dR, fila=1, col=1, escala=AGUA, cmin=0, etiqueta="diag(R)", formato=".3f",
                estaciones=estaciones, leyenda=False)
    fig.update_layout()  # la barra se coloca tras conocer el dominio
    d = dominio(fig, "x")
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", showlegend=False, hoverinfo="skip",
                             marker=dict(colorscale=recortar(AGUA), cmin=0, cmax=float(np.max(dR)), color=[0],
                                         showscale=True,
                                         colorbar=barra_color("diag(R)", x=d[1] + 0.01, largo=0.75,
                                                             title=dict(text="diag(R)", side="top",
                                                                        font=dict(size=11.5, color=TINTA))))), 1, 1)
    con = np.isin(np.arange(red.n), estaciones)
    for mask, nombre, color in [(~con, "Tramo sin estación", OI_AZUL), (con, "Tramo con estación", OI_NEGRO)]:
        fig.add_trace(go.Scatter(x=A[mask], y=dR[mask], mode="markers", name=nombre,
                                 marker=dict(size=6.5, color=color, line=dict(color=BLANCO, width=0.7)),
                                 customdata=np.arange(red.n)[mask],
                                 hovertemplate="Tramo %{customdata}<br>%{x:,.0f} km²<br>diag(R) %{y:.3f}<extra></extra>"),
                      1, 2)
    publicar(fig, ancho=1040, alto=430, margen=dict(t=34),
             leyenda=dict(x=dominio(fig, "x2")[0] + 0.01, xanchor="left", y=0.98))
    fig.update_xaxes(type="log", title_text="Área de drenaje [km²]", row=1, col=2,
                     tickvals=[100, 300, 1000, 3000, 10000, 30000],
                     ticktext=["10²", "3×10²", "10³", "3×10³", "10⁴", "3×10⁴"])
    fig.update_yaxes(title_text="diag(R)", rangemode="tozero", row=1, col=2)
    rotular(fig, ["Resolución por tramo (▲ estación)", "Resolución frente al área"])
    return fig


def figura_diseno(red, A, estaciones, estrategias: dict, rmse: dict) -> go.Figure:
    trazos = trazado_planta(red)
    fig = lienzo(1, 2, horizontal_spacing=0.02)
    for k, nombre in enumerate(estrategias):
        agregar_red(fig, red, np.log10(A), fila=1, col=k + 1, escala=GRISES, estaciones=estaciones,
                    nuevas=estrategias[nombre], color_nuevas=COLOR_ESTRATEGIA[nombre],
                    nombre_nuevas=f"Nueva ({nombre})", trazos=trazos, etiqueta="log₁₀ área",
                    escala_km=50 if k == 0 else None, leyenda=True)
    vistos = set()
    for tr in fig.data:
        if tr.name in vistos:
            tr.showlegend = False
        vistos.add(tr.name)
    publicar(fig, ancho=1040, alto=440, margen=dict(l=6, r=6, t=34, b=6),
             leyenda=dict(x=0.5, xanchor="center", y=0.02, yanchor="bottom"))
    rotular(fig, [f"{n}: RMSE de log n = {rmse[n]:.3f}" for n in estrategias], ["x", "x2"])
    return fig


def figura_neuronal(hist, verdad, tik, nn) -> go.Figure:
    fig = lienzo(1, 2, column_widths=[0.46, 0.54], horizontal_spacing=0.1)
    fig.add_trace(go.Scatter(y=hist, mode="lines", line=dict(color=OI_BERMELLON, width=1.4), showlegend=False,
                             hovertemplate="época %{x}<br>φ_d/N = %{y:.2f}<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=[0, len(hist)], y=[1, 1], mode="lines", line=dict(color=TINTA, width=0.8, dash="dot"),
                             showlegend=False, hoverinfo="skip"), 1, 1)
    lim = [float(np.log(0.018)), float(np.log(0.07))]
    lo = min(lim[0], float(np.min(nn)) - 0.1)
    hi = max(lim[1], float(np.max(nn)) + 0.1)
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="1:1", line=dict(color=TINTA, width=0.8),
                             hoverinfo="skip"), 1, 2)
    for nombre, est, simb in [("Tikhonov", tik, "circle"), ("Neuronal", nn, "diamond")]:
        fig.add_trace(go.Scatter(x=verdad, y=est, mode="markers", name=nombre,
                                 marker=dict(size=6.5, symbol=simb, color=COLOR_METODO[nombre],
                                             line=dict(color=BLANCO, width=0.7)),
                                 hovertemplate=f"{nombre}<br>verdadero %{{x:.3f}} · estimado %{{y:.3f}}<extra></extra>"),
                      1, 2)
    publicar(fig, ancho=1040, alto=400, margen=dict(t=34),
             leyenda=dict(x=dominio(fig, "x2")[0] + 0.01, xanchor="left", y=0.98))
    fig.update_xaxes(title_text="Época", range=[0, len(hist)], row=1, col=1)
    fig.update_yaxes(type="log", title_text="φ<sub>d</sub> / N", tickvals=[1, 2, 5, 10], row=1, col=1)
    fig.update_xaxes(title_text="log n verdadero", range=[lo, hi], row=1, col=2)
    fig.update_yaxes(title_text="log n estimado", range=[lo, hi], row=1, col=2)
    rotular(fig, ["Entrenamiento solo con caudal", "Recuperación de log n"])
    return fig


# ============================================================================ E01
def _media_estrategia(r: dict, e: str) -> float:
    return float(np.mean([f["rmse_log_n"] for f in r["diseno"] if f["estrategia"] == e]))


def _ic_bootstrap(x, n=10000, semilla=0):
    rng = np.random.default_rng(semilla)
    m = rng.choice(x, (n, len(x))).mean(1)
    return np.percentile(m, [2.5, 97.5])


def figura_e01(e01: dict) -> go.Figure:
    """(a) RMSE de log n por estrategia (pareado por red, media e IC 95 % bootstrap);
    (b) diag(R) frente al error, con mediana y rango intercuartil por clase."""
    from scipy import stats

    redes = e01["por_red"]
    claves = [("Red base", None), ("D-óptimo", "D-optimo"), ("Mayor área", "mayor-area"), ("Aleatorio", "aleatorio")]
    vals = {}
    for k, c in claves:
        vals[k] = np.array([r["rmse_base"] if c is None else _media_estrategia(r, c) for r in redes])
    nombres = [k for k, _ in claves]
    xpos = np.arange(len(nombres))
    fig = lienzo(1, 2, column_widths=[0.46, 0.54], horizontal_spacing=0.1)

    rng = np.random.default_rng(1)
    jit = rng.uniform(-0.09, 0.09, len(redes))
    for i in range(len(redes)):
        fig.add_trace(go.Scatter(x=xpos + jit[i], y=[vals[k][i] for k in nombres], mode="lines",
                                 line=dict(color="rgba(0,0,0,0.13)", width=0.8), hoverinfo="skip",
                                 showlegend=False), 1, 1)
    for j, k in enumerate(nombres):
        color = COLOR_ESTRATEGIA.get(k, TINTA_2)
        fig.add_trace(go.Scatter(x=xpos[j] + jit, y=vals[k], mode="markers", showlegend=False,
                                 marker=dict(size=6, color=color, opacity=0.9, line=dict(color=BLANCO, width=0.6)),
                                 customdata=np.arange(len(redes)),
                                 hovertemplate=f"{k}<br>red %{{customdata}}: %{{y:.3f}}<extra></extra>"), 1, 1)
        lo, hi = _ic_bootstrap(vals[k])
        m = vals[k].mean()
        fig.add_trace(go.Scatter(x=[xpos[j] + 0.28], y=[m], mode="markers", showlegend=False,
                                 marker=dict(symbol="diamond", size=8, color=TINTA),
                                 error_y=dict(type="data", symmetric=False, array=[hi - m], arrayminus=[m - lo],
                                              color=TINTA, thickness=1.1, width=3),
                                 hovertemplate=f"{k}: media %{{y:.3f}} (IC 95 % {lo:.3f}–{hi:.3f})<extra></extra>"),
                      1, 1)
    prior = float(np.mean([r["rmse_prior"] for r in redes]))
    fig.add_trace(go.Scatter(x=[-0.45, len(nombres) - 0.45], y=[prior, prior], mode="lines", hoverinfo="skip",
                             line=dict(color=TINTA, width=0.8, dash="dot"), showlegend=False), 1, 1)
    fig.add_annotation(x=len(nombres) - 0.5, y=prior, xref="x", yref="y", text="sin datos", showarrow=False,
                       xanchor="right", yanchor="bottom", font=dict(size=11, color=TINTA_2))

    x = np.concatenate([r["diag_R"] for r in redes])
    yv = np.concatenate([r["error_abs"] for r in redes])
    fig.add_trace(go.Scatter(x=x, y=yv, mode="markers", name=f"Tramo ({len(redes)} redes × 60)",
                             marker=dict(size=4, color="rgba(0,114,178,0.35)", line=dict(width=0)),
                             hovertemplate="diag(R) %{x:.3f}<br>|error| %{y:.3f}<extra></extra>"), 1, 2)
    bordes = np.quantile(x, np.linspace(0, 1, 9))
    c, med, q1, q3 = [], [], [], []
    for a, b in zip(bordes[:-1], bordes[1:], strict=True):
        s = (x >= a) & (x <= b)
        c.append(np.exp(np.mean(np.log(x[s]))))
        med.append(np.median(yv[s]))
        q1.append(np.quantile(yv[s], 0.25))
        q3.append(np.quantile(yv[s], 0.75))
    c, med, q1, q3 = map(np.array, (c, med, q1, q3))
    fig.add_trace(go.Scatter(x=c, y=med, mode="lines+markers", name="Mediana y RIC por octil",
                             line=dict(color=TINTA, width=1.4), marker=dict(size=6, color=TINTA),
                             error_y=dict(type="data", symmetric=False, array=q3 - med, arrayminus=med - q1,
                                          color=TINTA, thickness=1, width=3),
                             hovertemplate="diag(R) ≈ %{x:.3f}<br>mediana %{y:.3f}<extra></extra>"), 1, 2)
    rho, _ = stats.spearmanr(x, yv)
    rhos = np.array([r["spearman_diagR_vs_error"]["rho"] for r in redes])
    fig.add_annotation(xref="x2 domain", yref="y2 domain", x=0.015, y=0.985, xanchor="left", yanchor="top",
                       showarrow=False, align="left", font=dict(size=11, color=TINTA),
                       bgcolor="rgba(255,255,255,0.92)", bordercolor=TINTA, borderwidth=0.6, borderpad=4,
                       text=f"ρ<sub>Spearman</sub> = {rho:.2f} (todos los tramos)<br>"
                            f"ρ &lt; 0 en {(rhos < 0).sum()} de {len(rhos)} redes")
    publicar(fig, ancho=1040, alto=420, margen=dict(t=34),
             leyenda=dict(x=0.99, xanchor="right", y=0.98))
    fig.update_xaxes(tickvals=xpos, ticktext=nombres, range=[-0.5, len(nombres) - 0.4], row=1, col=1)
    fig.update_yaxes(title_text="RMSE de log n", row=1, col=1)
    fig.update_xaxes(type="log", title_text="diag(R)", tickvals=[0.001, 0.01, 0.1, 1],
                     ticktext=["10⁻³", "10⁻²", "10⁻¹", "1"], row=1, col=2)
    fig.update_yaxes(title_text="|log n̂ − log n|", rangemode="tozero", row=1, col=2)
    rotular(fig, ["Error tras agregar 4 estaciones", "Resolución frente a error"])
    return fig


def figura_sintesis(e01: dict) -> go.Figure:
    """Figura de síntesis de E01: (a) la resolución crece con el área de drenaje;
    (b) efecto del diseño D‑óptimo frente a la heurística de mayor área, red por red."""
    from .red import red_sintetica

    redes = e01["por_red"]
    area, dR, con = [], [], []
    for r in redes:
        A = red_sintetica(60, r["semilla"]).area_drenaje_km2()
        area.append(A)
        dR.append(np.asarray(r["diag_R"]))
        c = np.zeros(60, bool)
        c[r["estaciones_base"]] = True
        con.append(c)
    area, dR, con = map(np.concatenate, (area, dR, con))

    fig = lienzo(1, 2, column_widths=[0.56, 0.44], horizontal_spacing=0.11)
    # (a) resolución frente al área
    bordes = np.quantile(np.log10(area), np.linspace(0, 1, 9))
    cx, med, q1, q3, frac = [], [], [], [], []
    for a, b in zip(bordes[:-1], bordes[1:], strict=True):
        sel = (np.log10(area) >= a) & (np.log10(area) <= b)
        cx.append(10 ** np.median(np.log10(area[sel])))
        med.append(np.median(dR[sel]))
        q1.append(np.quantile(dR[sel], 0.25))
        q3.append(np.quantile(dR[sel], 0.75))
        frac.append((dR[sel] > 0.1).mean())
    fig.add_trace(go.Scatter(x=cx + cx[::-1], y=q3 + q1[::-1], fill="toself", mode="lines", line=dict(width=0),
                             fillcolor="rgba(0,114,178,0.14)", hoverinfo="skip", name="Rango intercuartil"), 1, 1)
    fig.add_trace(go.Scatter(x=area[~con], y=dR[~con], mode="markers", name="Tramo sin estación",
                             marker=dict(size=4, color="rgba(0,114,178,0.45)", line=dict(width=0)),
                             hovertemplate="%{x:,.0f} km²<br>diag(R) %{y:.3g}<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=area[con], y=dR[con], mode="markers", name="Tramo con estación",
                             marker=dict(size=6, color=OI_NEGRO, symbol="triangle-up", line=dict(color=BLANCO, width=0.6)),
                             hovertemplate="estación · %{x:,.0f} km²<br>diag(R) %{y:.3g}<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=cx, y=med, mode="lines+markers", name="Mediana por octil de área",
                             line=dict(color=TINTA, width=1.6), marker=dict(size=5.5, color=TINTA),
                             hovertemplate="área ≈ %{x:,.0f} km²<br>mediana diag(R) %{y:.3g}<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=[80, 4e4], y=[0.1, 0.1], mode="lines", line=dict(color=TINTA, width=0.8, dash="dot"),
                             hoverinfo="skip", showlegend=False), 1, 1)
    fig.add_annotation(x=np.log10(95), y=np.log10(0.1), xref="x", yref="y", text="diag(R) = 0,1", showarrow=False,
                       xanchor="left", yanchor="bottom", font=dict(size=11, color=TINTA_2))
    fig.add_annotation(x=np.log10(cx[-1]), y=np.log10(q3[-1]), xref="x", yref="y", showarrow=True, ax=-10, ay=-34,
                       arrowwidth=0.8, arrowhead=0, align="right", xanchor="right",
                       bgcolor="rgba(255,255,255,0.9)",
                       text=f"{100 * frac[-1]:.0f} % de los tramos<br>más grandes &gt; 0,1",
                       font=dict(size=11, color=TINTA))
    fig.add_annotation(x=np.log10(cx[0]), y=np.log10(q1[0]), xref="x", yref="y", showarrow=True, ax=40, ay=58,
                       arrowwidth=0.8, arrowhead=0, align="left", xanchor="left", bgcolor="rgba(255,255,255,0.9)",
                       text=f"{100 * frac[0]:.0f} % de las cabeceras &gt; 0,1", font=dict(size=11, color=TINTA))

    # (b) efecto del diseño, red por red
    def media(r, e):
        return float(np.mean([f["rmse_log_n"] for f in r["diseno"] if f["estrategia"] == e]))

    dif = np.array([media(r, "D-optimo") - media(r, "mayor-area") for r in redes])
    orden = np.argsort(dif)
    yv = np.arange(len(dif)) + 2
    colores = [OI_AZUL if d < 0 else OI_BERMELLON for d in dif[orden]]
    fig.add_trace(go.Scatter(x=[0, 0], y=[0, len(dif) + 2.6], mode="lines", line=dict(color=TINTA, width=0.8),
                             hoverinfo="skip", showlegend=False), 1, 2)
    for y, d in zip(yv, dif[orden], strict=True):
        fig.add_trace(go.Scatter(x=[0, d], y=[y, y], mode="lines", line=dict(color=GRIS_CLARO, width=1.2),
                                 hoverinfo="skip", showlegend=False), 1, 2)
    fig.add_trace(go.Scatter(x=dif[orden], y=yv, mode="markers", showlegend=False,
                             marker=dict(size=7.5, color=colores, line=dict(color=BLANCO, width=0.7)),
                             customdata=[redes[i]["semilla"] for i in orden],
                             hovertemplate="red %{customdata}: ΔRMSE = %{x:+.3f}<extra></extra>"), 1, 2)
    lo, hi = _ic_bootstrap(dif)
    m = dif.mean()
    fig.add_trace(go.Scatter(x=[m], y=[0.6], mode="markers", showlegend=False,
                             marker=dict(symbol="diamond", size=10, color=TINTA),
                             error_x=dict(type="data", symmetric=False, array=[hi - m], arrayminus=[m - lo],
                                          color=TINTA, thickness=1.3, width=4),
                             hovertemplate=f"media {m:+.3f} (IC 95 % {lo:+.3f} a {hi:+.3f})<extra></extra>"), 1, 2)
    p = e01["global"]["wilcoxon_D_menor_que_area"]["p"]
    gana = int((dif < 0).sum())
    fig.add_annotation(xref="x2 domain", yref="y2 domain", x=0.03, y=0.8, xanchor="left", yanchor="top",
                       showarrow=False, align="left", font=dict(size=11, color=TINTA),
                       text=f"D‑óptimo mejor en {gana} de {len(dif)} redes<br>Wilcoxon pareado: p = {p:.1e}".replace(
                           "e-04", "×10⁻⁴"))
    fig.add_annotation(xref="x2", yref="paper", x=0, y=1.0, yshift=-14, xanchor="right", xshift=-6, showarrow=False,
                       text="← mejor D‑óptimo", font=dict(size=10.5, color=TINTA_2))
    fig.add_annotation(xref="x2", yref="paper", x=0, y=1.0, yshift=-14, xanchor="left", xshift=6, showarrow=False,
                       text="mejor mayor área →", font=dict(size=10.5, color=TINTA_2))

    publicar(fig, ancho=1080, alto=440, margen=dict(t=34, l=64),
             leyenda=dict(x=dominio(fig, "x")[1] - 0.008, xanchor="right", y=0.03, yanchor="bottom",
                          font=dict(size=10.5)))
    fig.update_xaxes(type="log", title_text="Área de drenaje del tramo [km²]", row=1, col=1,
                     tickvals=[100, 300, 1000, 3000, 10000], ticktext=["10²", "3×10²", "10³", "3×10³", "10⁴"],
                     range=[np.log10(80), np.log10(4e4)])
    fig.update_yaxes(type="log", title_text="Resolución diag(R)", row=1, col=1, range=[np.log10(1.5e-4), 0.05],
                     tickvals=[1e-3, 1e-2, 1e-1, 1], ticktext=["10⁻³", "10⁻²", "10⁻¹", "1"])
    xmax = float(np.abs(dif).max()) * 1.25
    fig.update_xaxes(title_text="ΔRMSE de log n (D‑óptimo − mayor área)", row=1, col=2, range=[-xmax, xmax * 0.6],
                     zeroline=False)
    fig.update_yaxes(row=1, col=2, range=[-0.4, len(dif) + 2.8], tickvals=[0.6] + list(yv),
                     ticktext=["Media (IC 95 %)"] + [f"Red {redes[i]['semilla']}" for i in orden],
                     tickfont=dict(size=10.5))
    rotular(fig, ["La resolución crece con el área (720 tramos, 12 redes)", "Efecto del diseño, red por red"])
    return fig


# ============================================================================ Fase 0 (Colombia)
FRAGMENTOS_FASE0 = {"24067020": "23157080", "52017060": "52017010", "13037010": "13047040"}
"""Subsistemas que resultaron ser piezas de otra cuenca (docs/protocolo.md, Fase 0)."""


def _anillos(geom):
    """Anillos exteriores de un (Multi)Polygon/GeometryCollection GeoJSON o shapely."""
    if hasattr(geom, "geom_type"):
        if geom.geom_type == "Polygon":
            return [np.asarray(geom.exterior.coords)]
        if hasattr(geom, "geoms"):
            return [a for g in geom.geoms for a in _anillos(g)]
        return []
    t = geom["type"]
    if t == "Polygon":
        return [np.asarray(geom["coordinates"][0])]
    if t == "MultiPolygon":
        return [np.asarray(p[0]) for p in geom["coordinates"]]
    if t == "GeometryCollection":
        return [a for g in geom["geometries"] for a in _anillos(g)]
    return []


def _xy_concat(anillos):
    xs, ys = [], []
    for a in anillos:
        xs += list(a[:, 0]) + [None]
        ys += list(a[:, 1]) + [None]
    return xs, ys


def figura_fase0(mapa: dict, sistemas, piloto: str = "31097010") -> go.Figure:
    """(a) Mapa de Colombia con las cuencas anidadas de CAMELS‑COL, la red de drenaje,
    las estaciones y las presas de GRanD; (b) número de estaciones frente al área."""
    paises = json.loads((RECURSOS / "paises_ne10m.geojson").read_text(encoding="utf-8"))
    fig = lienzo(1, 2, column_widths=[0.6, 0.4], horizontal_spacing=0.09)

    fig.add_trace(go.Scatter(x=[-90, -60, -60, -90, -90], y=[-10, -10, 20, 20, -10], mode="lines", fill="toself",
                             fillcolor="#dfe9f3", line=dict(width=0), hoverinfo="skip", showlegend=False), 1, 1)
    for f in paises["features"]:
        es_col = f["properties"]["nombre"] == "Colombia"
        xs, ys = _xy_concat(_anillos(f["geometry"]))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself",
                                 fillcolor="#ffffff" if es_col else "#f1f1ef",
                                 line=dict(color="#7d7d7d" if es_col else "#bdbdbd", width=0.8 if es_col else 0.5),
                                 hoverinfo="skip", showlegend=False), 1, 1)

    estilos = {"natural": (OI_AZUL, "Cuenca natural (sin presas)"),
               "regulada": (OI_BERMELLON, "Cuenca regulada"),
               "pieza": (GRIS, "Subsistema dentro de otra cuenca")}
    for clave, (color, nombre) in estilos.items():
        polis = [p for p in mapa["cuencas"] if p["grupo"] == clave]
        if not polis:
            continue
        xs, ys = _xy_concat([np.asarray(a) for p in polis for a in p["anillos"]])
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor=rgba(color, 0.16),
                                 line=dict(color=color, width=0.9), name=nombre, hoverinfo="skip"), 1, 1)
    xs, ys = _xy_concat([np.asarray(a) for a in mapa["rios"]])
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#5b8fc7", width=0.45),
                             name="Red de drenaje (CAMELS‑COL)", hoverinfo="skip"), 1, 1)
    p = [c for c in mapa["cuencas"] if c["salida"] == piloto]
    if p:
        xs, ys = _xy_concat([np.asarray(a) for a in p[0]["anillos"]])
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=TINTA, width=1.8),
                                 name=f"Cuenca piloto {piloto}", hoverinfo="skip"), 1, 1)
    est = mapa["estaciones"]
    fig.add_trace(go.Scatter(x=[e["lon"] for e in est], y=[e["lat"] for e in est], mode="markers",
                             name="Estación CAMELS‑COL anidada",
                             marker=dict(size=3.4, color=TINTA, line=dict(width=0)),
                             text=[e["id"] for e in est], hovertemplate="Estación %{text}<extra></extra>"), 1, 1)
    pr = mapa["presas"]
    fig.add_trace(go.Scatter(x=[d["lon"] for d in pr], y=[d["lat"] for d in pr], mode="markers",
                             name="Presa (GRanD v1.3)",
                             marker=dict(symbol="square", size=6, color=BLANCO, line=dict(color=TINTA, width=1)),
                             text=[d["nombre"] for d in pr], hovertemplate="%{text}<extra></extra>"), 1, 1)
    lon0, lon1, lat0, lat1 = -79.6, -66.6, -4.4, 12.7
    fig.update_xaxes(range=[lon0, lon1], row=1, col=1, tickvals=[-78, -74, -70],
                     ticktext=["78° O", "74° O", "70° O"])
    fig.update_yaxes(range=[lat0, lat1], row=1, col=1, scaleanchor="x", scaleratio=1,
                     tickvals=[-4, 0, 4, 8, 12], ticktext=["4° S", "0°", "4° N", "8° N", "12° N"])

    # (b) estaciones frente al área de la cuenca de salida
    s = sistemas.copy()
    s["salida"] = s["salida"].astype(str)
    grupo = {c["salida"]: c["grupo"] for c in mapa["cuencas"]}
    s["grupo"] = s["salida"].map(grupo).fillna("pieza")
    for clave, (color, _nombre) in estilos.items():
        d = s[s["grupo"] == clave]
        fig.add_trace(go.Scatter(
            x=d["area_salida_km2"], y=d["estaciones"], mode="markers", showlegend=False,
            marker=dict(size=8, color=color, symbol="circle" if clave != "pieza" else "circle-open",
                        line=dict(color=BLANCO if clave != "pieza" else color, width=0.8 if clave != "pieza" else 1.2)),
            text=d["salida"] + " · " + d["departamento_principal"].str.title(),
            customdata=d["anos_comunes_mediana"],
            hovertemplate="%{text}<br>%{y} estaciones · %{x:,.0f} km²<br>registro común: %{customdata:.0f} años"
                          "<extra></extra>"), 1, 2)
    fila = s[s["salida"] == piloto]
    if len(fila):
        fig.add_annotation(x=np.log10(float(fila["area_salida_km2"].iloc[0])), y=np.log10(float(fila["estaciones"].iloc[0])),
                           xref="x2", yref="y2", text=f"{piloto}<br>(piloto)", showarrow=True, ax=-46, ay=-30,
                           arrowwidth=0.8, arrowhead=0, font=dict(size=11, color=TINTA), align="center")
    for _, r in s[s["estaciones"] >= 30].iterrows():
        fig.add_annotation(x=np.log10(r["area_salida_km2"]), y=np.log10(r["estaciones"]), xref="x2", yref="y2",
                           text=r["salida"], showarrow=False, xanchor="right", xshift=-7,
                           font=dict(size=10.5, color=TINTA_2))
    publicar(fig, ancho=1080, alto=640, margen=dict(t=34, l=58),
             leyenda=dict(x=dominio(fig, "x2")[0] + 0.012, xanchor="left", y=0.985, yanchor="top",
                          font=dict(size=10.5)))
    fig.update_xaxes(type="log", title_text="Área de la cuenca de salida [km²]", row=1, col=2,
                     tickvals=[1e3, 3e3, 1e4, 3e4, 1e5, 3e5], ticktext=["10³", "3×10³", "10⁴", "3×10⁴", "10⁵", "3×10⁵"])
    fig.update_yaxes(type="log", title_text="Estaciones anidadas", row=1, col=2,
                     tickvals=[3, 5, 10, 20, 50, 100, 150], ticktext=["3", "5", "10", "20", "50", "100", "150"])
    rotular(fig, ["Cuencas con ≥ 3 estaciones anidadas", "Tamaño de cada subsistema"])
    return fig


# ============================================================================ salida
def guardar(fig: go.Figure, nombre: str, carpeta: str | Path, escala: float = 3) -> None:
    """Guarda la figura como HTML interactivo y PNG de alta resolución (300 ppp aprox.)."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    fig.write_html(carpeta / f"{nombre}.html", include_plotlyjs="cdn")
    try:
        fig.write_image(carpeta / f"{nombre}.png", scale=escala)
    except Exception as e:  # kaleido sin Chrome: queda el HTML
        print(f"PNG no guardado ({type(e).__name__}); quedó {nombre}.html. "
              "Si falta Chrome: uv run plotly_get_chrome")


# ============================================================================ HTML del cuaderno
_TABLA = ("border-collapse:collapse;font-family:Arial,Helvetica,sans-serif;font-size:13px;"
          "color:#1a1a1a;margin:6px 0 12px 0")


def tabla(encabezados: Sequence[str], filas: Sequence[Sequence], resaltar: int | None = None,
          titulo: str | None = None) -> str:
    """Tabla de tres filetes (estilo de revista): filete superior, bajo el encabezado y final."""
    th = "".join(f"<th style='text-align:{'left' if k == 0 else 'right'};padding:5px 14px;"
                 f"border-top:1.5px solid #1a1a1a;border-bottom:0.8px solid #1a1a1a;font-weight:700'>{h}</th>"
                 for k, h in enumerate(encabezados))
    cuerpo = ""
    for i, fila in enumerate(filas):
        ult = "border-bottom:1.5px solid #1a1a1a;" if i == len(filas) - 1 else ""
        peso = "700" if i == resaltar else "400"
        tds = "".join(f"<td style='text-align:{'left' if k == 0 else 'right'};padding:4px 14px;{ult}"
                      f"font-weight:{peso};font-variant-numeric:tabular-nums'>{c}</td>" for k, c in enumerate(fila))
        cuerpo += f"<tr>{tds}</tr>"
    cab = (f"<div style='font:13px Arial,Helvetica,sans-serif;color:#1a1a1a;margin:6px 0 2px'>"
           f"<b>Tabla.</b> {titulo}</div>") if titulo else ""
    return f"{cab}<table style='{_TABLA}'><thead><tr>{th}</tr></thead><tbody>{cuerpo}</tbody></table>"


def resumen(pares: Sequence[tuple[str, str]], titulo: str | None = None) -> str:
    """Lista compacta «magnitud: valor», como una tabla de dos columnas sin adornos."""
    return tabla(["Magnitud", "Valor"], [[a, b] for a, b in pares], titulo=titulo)


def verificacion(texto: str, ok: bool) -> str:
    marca = "✓" if ok else "✗"
    color = "#1a1a1a" if ok else OI_BERMELLON
    return (f"<div style='font:13px Arial,Helvetica,sans-serif;color:{color};margin:2px 0'>"
            f"<span style='display:inline-block;width:16px;font-weight:700'>{marca}</span>{texto}</div>")
