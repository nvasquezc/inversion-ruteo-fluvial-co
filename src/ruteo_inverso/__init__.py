"""ruteo_inverso: inversión de parámetros de ruteo fluvial con operador directo diferenciable."""

from .red import RedFluvial, red_sintetica
from .ruteo import MuskingumCunge, promedio_diario, caudal_referencia
from .forzamiento import aporte_lateral_sintetico, rugosidad_verdadera
from .inversion import (ProblemaInverso, sintetizar_observaciones, invertir_tikhonov,
                        invertir_neuronal, ParametrizacionNeuronal)
from .resolucion import (jacobiano_diario, matriz_regularizacion, resolucion,
                         informacion_por_candidato, diseno_codicioso)

__version__ = "0.1.0"
