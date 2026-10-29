"""ruteo_inverso: inversión de parámetros de ruteo fluvial con operador directo diferenciable."""

from .forzamiento import aporte_lateral_sintetico, rugosidad_verdadera
from .inversion import (
    ParametrizacionNeuronal,
    ProblemaInverso,
    invertir_neuronal,
    invertir_tikhonov,
    sintetizar_observaciones,
)
from .red import RedFluvial, red_sintetica
from .resolucion import (
    diseno_codicioso,
    informacion_por_candidato,
    jacobiano_diario,
    matriz_regularizacion,
    resolucion,
)
from .ruteo import MuskingumCunge, caudal_referencia, promedio_diario

__all__ = [
    "MuskingumCunge",
    "ParametrizacionNeuronal",
    "ProblemaInverso",
    "RedFluvial",
    "aporte_lateral_sintetico",
    "caudal_referencia",
    "diseno_codicioso",
    "informacion_por_candidato",
    "invertir_neuronal",
    "invertir_tikhonov",
    "jacobiano_diario",
    "matriz_regularizacion",
    "promedio_diario",
    "red_sintetica",
    "resolucion",
    "rugosidad_verdadera",
    "sintetizar_observaciones",
]

__version__ = "0.1.1"
