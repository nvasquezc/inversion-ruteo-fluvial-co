"""Gráficos de la red fluvial y estilo común para las figuras del proyecto."""

from __future__ import annotations

import numpy as np

from .red import RedFluvial

SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
SERIE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]


def estilo() -> None:
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE,
        "axes.edgecolor": TEXTO_2, "axes.labelcolor": TEXTO, "text.color": TEXTO,
        "xtick.color": TEXTO_2, "ytick.color": TEXTO_2, "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
        "axes.prop_cycle": __import__("cycler").cycler(color=SERIE),
        "lines.linewidth": 2.0, "figure.dpi": 110,
    })


def posiciones(red: RedFluvial) -> tuple[np.ndarray, np.ndarray]:
    """Disposición tipo dendrograma: x = distancia a la salida (km, negativa
    hacia aguas arriba); y = orden de las hojas. Devuelve (x_inicio, x_fin) e y."""
    n = red.n
    hijos = [[] for _ in range(n)]
    for i, j in enumerate(red.aguas_abajo):
        if j >= 0:
            hijos[j].append(i)
    salida = int(np.where(red.aguas_abajo < 0)[0][0])
    x_fin = np.zeros(n)   # extremo aguas abajo del tramo
    for i in range(n - 1, -1, -1):  # aguas abajo primero
        j = red.aguas_abajo[i]
        x_fin[i] = 0.0 if j < 0 else x_fin[j] - red.longitud_m[j] / 1e3
    x_ini = x_fin - red.longitud_m / 1e3
    y = np.zeros(n)
    contador = [0.0]

    def asignar(i):
        if not hijos[i]:
            y[i] = contador[0]
            contador[0] += 1
        else:
            for h in hijos[i]:
                asignar(h)
            y[i] = np.mean([y[h] for h in hijos[i]])

    import sys
    sys.setrecursionlimit(max(10000, 4 * n))
    asignar(salida)
    return np.column_stack([x_ini, x_fin]), y


def dibujar_red(red: RedFluvial, ax, valores=None, estaciones=(), estaciones_nuevas=(),
                cmap="Blues", vmin=None, vmax=None, etiqueta_color="", ancho_por_area=True,
                anotar=()):
    """Dibuja la red; colorea cada tramo por ``valores`` si se dan."""
    import matplotlib as mpl

    xs, y = posiciones(red)
    A = red.area_drenaje_km2()
    w = 1.0 + 4.0 * (np.sqrt(A) / np.sqrt(A).max()) if ancho_por_area else np.full(red.n, 2.0)
    if valores is not None:
        valores = np.asarray(valores, dtype=float)
        norm = mpl.colors.Normalize(vmin if vmin is not None else valores.min(),
                                    vmax if vmax is not None else valores.max())
        cm = mpl.colormaps[cmap]
        colores = [cm(0.15 + 0.85 * norm(v)) for v in valores]
    else:
        colores = [SERIE[0]] * red.n
    for i in range(red.n):
        ax.plot(xs[i], [y[i], y[i]], color=colores[i], lw=w[i], solid_capstyle="round", zorder=2)
        j = red.aguas_abajo[i]
        if j >= 0:  # conector vertical hacia el tramo receptor
            ax.plot([xs[i, 1], xs[i, 1]], [y[i], y[j]], color="#c9c8c3", lw=0.8, zorder=1)
    for e in estaciones:
        ax.scatter(xs[e, 1], y[e], s=70, marker="v", color=SERIE[1], edgecolor=SUPERFICIE,
                   linewidth=1.5, zorder=4)
    for e in estaciones_nuevas:
        ax.scatter(xs[e, 1], y[e], s=70, marker="v", color=SERIE[2], edgecolor=SUPERFICIE,
                   linewidth=1.5, zorder=4)
    for e in anotar:
        ax.annotate(str(e), (xs[e].mean(), y[e]), textcoords="offset points", xytext=(0, 5),
                    ha="center", fontsize=7, color=TEXTO_2)
    ax.set_xlabel("distancia a la salida [km]")
    ax.set_yticks([])
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    if valores is not None:
        sm = mpl.cm.ScalarMappable(norm=norm, cmap=mpl.colors.ListedColormap(
            [mpl.colormaps[cmap](0.15 + 0.85 * t) for t in np.linspace(0, 1, 256)]))
        cb = ax.figure.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
        cb.set_label(etiqueta_color)
        cb.outline.set_visible(False)
    return xs, y