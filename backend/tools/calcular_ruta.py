"""
T12 · calcular_ruta — CÓDIGO PURO. Biblia §6.3.
El "para que" de la HU1: "...para que la empresa me dirija al producto,
asesor o proceso correcto."
"""
from typing import Literal

from schemas.senales import TipoProspecto

RutaSugerida = Literal[
    "ventas_corporativas",
    "asesoria_inversion",
    "programa_inicial",
    "nutricion_educativa",
    "automatico",
]


def calcular_ruta(tipo: TipoProspecto, score_total: int, pidio_asesor: bool) -> RutaSugerida:
    if tipo == "B2B":
        return "ventas_corporativas"

    # B2C
    if score_total >= 70:
        return "asesoria_inversion" if pidio_asesor else "programa_inicial"
    if score_total >= 40:
        return "nutricion_educativa"
    return "automatico"
