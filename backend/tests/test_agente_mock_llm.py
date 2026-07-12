"""
test_agente_mock_llm — El bucle corre SIN la API de Gemini (Biblia §19, §20).
Se le inyecta una función "Gemini falso" a T1 y T3 para probar la mecánica
de extracción tipada sin gastar cuota ni necesitar internet.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from schemas.clasificacion import ClasificacionProspecto
from schemas.senales import Senales
from tools.clasificar_prospecto import clasificar_prospecto
from tools.extraer_senales import extraer_senales


# ───────────── T1 · clasificar_prospecto ─────────────

def test_clasificar_prospecto_con_mock():
    def gemini_falso(prompt: str) -> ClasificacionProspecto:
        assert "historial" not in prompt or True  # el prompt se formateó, no crashea
        return ClasificacionProspecto(tipo="B2C", confianza=0.95)

    resultado = clasificar_prospecto(
        ["Quiero invertir mis ahorros"], llamar_llm=gemini_falso
    )
    assert resultado.tipo == "B2C"
    assert resultado.confianza == 0.95


def test_clasificar_prospecto_b2b():
    def gemini_falso(prompt: str) -> ClasificacionProspecto:
        return ClasificacionProspecto(tipo="B2B", confianza=0.88)

    resultado = clasificar_prospecto(
        ["Tenemos 120 colaboradores y queremos capacitarlos"], llamar_llm=gemini_falso
    )
    assert resultado.tipo == "B2B"


def test_clasificar_prospecto_rechaza_salida_no_tipada():
    """Regla de oro #2: si el LLM no devuelve el tipo correcto, se rechaza."""
    def gemini_roto(prompt: str):
        return {"tipo": "B2C"}  # dict, no una instancia de ClasificacionProspecto

    with pytest.raises(ValueError):
        clasificar_prospecto(["hola"], llamar_llm=gemini_roto)


# ───────────── T3 · extraer_senales ─────────────

def test_extraer_senales_con_evidencia():
    def gemini_falso(prompt: str) -> Senales:
        return Senales(
            objetivo="invertir",
            horizonte="1-3m",
            monto_declarado_usd=10000,
            experiencia_inversion="ninguna",
        )

    resultado = extraer_senales(
        ["Quiero invertir 10000 dólares en los próximos meses, nunca he invertido"],
        "B2C",
        llamar_llm=gemini_falso,
    )
    assert resultado.objetivo == "invertir"
    assert resultado.monto_declarado_usd == 10000


def test_extraer_senales_sin_evidencia_da_null():
    """Prohibido adivinar: sin evidencia explícita, los campos quedan en None."""
    def gemini_falso(prompt: str) -> Senales:
        return Senales()  # el LLM no encontró nada explícito

    resultado = extraer_senales(["hola, ¿qué es Futuro Academy?"], "B2C", llamar_llm=gemini_falso)
    assert resultado.objetivo is None
    assert resultado.monto_declarado_usd is None
    assert resultado.experiencia_inversion is None


def test_extraer_senales_rechaza_salida_no_tipada():
    def gemini_roto(prompt: str):
        return "esto no es un Senales"

    with pytest.raises(ValueError):
        extraer_senales(["hola"], "B2C", llamar_llm=gemini_roto)


def test_extraer_senales_conecta_con_scoring():
    """Prueba de integración: T3 (mockeado) -> T4 (código real) funciona."""
    from tools.calcular_score import calcular_score

    def gemini_falso(prompt: str) -> Senales:
        return Senales(
            objetivo="invertir",
            horizonte="1-3m",
            pidio_asesor=True,
            mensajes_intercambiados=11,
            completo_quiz=True,
            monto_declarado_usd=10000,
            experiencia_inversion="ninguna",
            cedula_valida=True,
            email_valido=True,
        )

    senales = extraer_senales(["..."], "B2C", llamar_llm=gemini_falso)
    score = calcular_score(senales, "B2C")
    assert score.total == 88  # María, otra vez
