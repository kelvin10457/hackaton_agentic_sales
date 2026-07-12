"""
test_score — Mismo input -> mismo output. María = 88. Andrés = 65.
Biblia §5.6 (verificación de los personajes) y §19 (plan de pruebas).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.senales import Senales
from tools.calcular_score import calcular_score


def test_maria_b2c_caliente_88():
    senales = Senales(
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
    score = calcular_score(senales, "B2C")

    assert score.interes == 25
    assert score.presupuesto == 20
    assert score.perfil == 25
    assert score.urgencia == 18
    assert score.total == 88
    assert score.banda == "caliente"


def test_andres_b2b_tibio_65():
    senales = Senales(
        objetivo="capacitar_equipo",
        horizonte="3-6m",
        pidio_asesor=False,
        mensajes_intercambiados=9,
        solicito_propuesta=False,
        num_colaboradores=120,
        presupuesto_capacitacion_usd=8000,
        es_decisor=True,
        ruc_valido=True,
        email_corporativo=True,
    )
    score = calcular_score(senales, "B2B")

    assert score.interes == 10
    assert score.presupuesto == 20
    assert score.perfil == 25
    assert score.urgencia == 10
    assert score.total == 65
    assert score.banda == "tibio"


def test_lead_vacio_da_cero():
    """Bordes: todo None/False -> score 0, frío."""
    senales = Senales()
    score = calcular_score(senales, "B2C")
    assert score.total == 0
    assert score.banda == "frio"


def test_mismo_input_mismo_output():
    """La tesis del producto: determinismo total."""
    senales = Senales(objetivo="invertir", monto_declarado_usd=5000, horizonte="inmediato")
    s1 = calcular_score(senales, "B2C")
    s2 = calcular_score(senales, "B2C")
    assert s1 == s2
