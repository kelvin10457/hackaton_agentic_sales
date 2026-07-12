"""
T4 · calcular_score — CÓDIGO PURO. Biblia §5.

REGLA DE ORO #1: El LLM extrae señales. Este archivo calcula el número.
Este módulo NO importa el SDK de Gemini. Si algún día lo hace, algo está mal.

Mismo input -> mismo output. Siempre. Es la tesis del producto.
"""
from pathlib import Path
from typing import Literal
import yaml

from schemas.senales import Senales, TipoProspecto
from schemas.score import Score

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "pesos_scoring.yaml"


def _cargar_pesos() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _calcular_interes(s: Senales, pesos: dict) -> int:
    p = pesos["interes"]
    pts = 0
    if s.pidio_asesor:
        pts += p["pidio_asesor"]
    if s.completo_quiz or s.solicito_propuesta:
        pts += p["completo_quiz_o_propuesta"]

    if s.mensajes_intercambiados >= p["mensajes"]["alto"]["min_mensajes"]:
        pts += p["mensajes"]["alto"]["puntos"]
    elif s.mensajes_intercambiados >= p["mensajes"]["medio"]["min_mensajes"]:
        pts += p["mensajes"]["medio"]["puntos"]

    if s.objetivo in p["objetivo"]["objetivos_bono_principal"]:
        pts += p["objetivo"]["bono_principal"]
    elif s.objetivo == "aprender":
        pts += p["objetivo"]["bono_aprender"]

    return min(pts, p["tope"])


def _calcular_presupuesto(s: Senales, tipo: TipoProspecto, pesos: dict) -> int:
    p = pesos["presupuesto"]
    if tipo == "B2C":
        monto = s.monto_declarado_usd
        if monto is None:
            return p["b2c"]["si_null"]
        for banda in p["b2c"]["bandas"]:
            minimo = banda["min"]
            maximo = banda.get("max", float("inf"))
            if minimo <= monto <= maximo:
                return banda["puntos"]
        return p["b2c"]["si_null"]

    # B2B
    pts = 0
    colab = s.num_colaboradores or 0
    for banda in p["b2b"]["colaboradores"]:
        minimo = banda["min"]
        maximo = banda.get("max", float("inf"))
        if minimo <= colab <= maximo:
            pts += banda["puntos"]
            break

    presupuesto_usd = s.presupuesto_capacitacion_usd or 0
    if presupuesto_usd >= p["b2b"]["bono_presupuesto"]["alto"]["min_usd"]:
        pts += p["b2b"]["bono_presupuesto"]["alto"]["puntos"]
    elif presupuesto_usd > 0:
        pts += p["b2b"]["bono_presupuesto"]["bajo"]["puntos"]

    return min(pts, p["tope"])


def _calcular_perfil(s: Senales, tipo: TipoProspecto, pesos: dict) -> int:
    p = pesos["perfil"]
    pts = 0
    if tipo == "B2C":
        if s.experiencia_inversion:
            pts += p["b2c"]["experiencia"].get(s.experiencia_inversion, 0)
        if s.cedula_valida:
            pts += p["b2c"]["cedula_valida"]
        if s.email_valido:
            pts += p["b2c"]["email_valido"]
    else:
        pts += p["b2b"]["es_decisor_true"] if s.es_decisor else p["b2b"]["es_decisor_false"]
        if s.ruc_valido:
            pts += p["b2b"]["ruc_valido"]
        if s.email_corporativo:
            pts += p["b2b"]["email_corporativo"]
    return min(pts, p["tope"])


def _calcular_urgencia(s: Senales, pesos: dict) -> int:
    p = pesos["urgencia"]
    if s.horizonte is None:
        return p["si_null"]
    return p.get(s.horizonte, p["si_null"])


def _banda(total: int, pesos: dict) -> Literal["frio", "tibio", "caliente"]:
    b = pesos["bandas"]
    if b["caliente"]["min"] <= total <= b["caliente"]["max"]:
        return "caliente"
    if b["tibio"]["min"] <= total <= b["tibio"]["max"]:
        return "tibio"
    return "frio"


def _justificacion(s: Senales, tipo: TipoProspecto, interes, presupuesto, perfil, urgencia) -> str:
    """Plantilla en código. NUNCA la escribe el LLM. Mismo input -> misma justificación."""
    partes = []
    if s.pidio_asesor:
        partes.append("pidió hablar con un asesor")
    if s.completo_quiz or s.solicito_propuesta:
        partes.append("completó el " + ("quiz de perfil" if tipo == "B2C" else "proceso de propuesta"))
    interes_txt = f"Interés alto: {', '.join(partes)}." if partes else "Interés moderado."

    if tipo == "B2C":
        monto_txt = f"declaró USD {s.monto_declarado_usd:,.0f}" if s.monto_declarado_usd else "no declaró monto"
        presupuesto_txt = f"Presupuesto: {monto_txt}."
        perfil_txt = f"Perfil: experiencia {s.experiencia_inversion or 'desconocida'}."
    else:
        presupuesto_txt = f"Presupuesto: {s.num_colaboradores or 0} colaboradores."
        perfil_txt = f"Perfil: {'decisor' if s.es_decisor else 'no decisor'}."

    return f"{interes_txt} {presupuesto_txt} {perfil_txt}"


def calcular_score(senales: Senales, tipo: TipoProspecto) -> Score:
    """T4 — Único punto de entrada. CÓDIGO PURO, sin LLM."""
    pesos = _cargar_pesos()

    interes = _calcular_interes(senales, pesos)
    presupuesto = _calcular_presupuesto(senales, tipo, pesos)
    perfil = _calcular_perfil(senales, tipo, pesos)
    urgencia = _calcular_urgencia(senales, pesos)
    total = interes + presupuesto + perfil + urgencia

    return Score(
        interes=interes,
        presupuesto=presupuesto,
        perfil=perfil,
        urgencia=urgencia,
        total=total,
        banda=_banda(total, pesos),
        justificacion=_justificacion(senales, tipo, interes, presupuesto, perfil, urgencia),
    )
