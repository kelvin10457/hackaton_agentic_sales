"""Casos de referencia del contrato de scoring."""
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import SenalesLead
from scoring import calcular_score, ruta_sugerida


def _senales(**values):
    return SenalesLead(lead_id=1, **values)


def test_maria_b2c_es_88_caliente():
    maria = _senales(
        pidio_asesor=True, completo_quiz=True, mensajes_intercambiados=11,
        objetivo="invertir", monto_declarado_usd=10_000,
        experiencia_inversion="ninguna", documento_valido=True, email_valido=True,
        horizonte="1-3m",
    )
    resultado = calcular_score(maria, "b2c")
    assert resultado["total"] == 88
    assert resultado["banda"] == "caliente"
    assert resultado["dimension_interes"] == 25


def test_andres_b2b_es_65_tibio():
    andres = _senales(
        mensajes_intercambiados=9, objetivo="capacitar_equipo",
        num_colaboradores=120, presupuesto_capacitacion_usd=8000,
        es_decisor=True, ruc_valido=True, email_corporativo=True,
        horizonte="3-6m",
    )
    resultado = calcular_score(andres, "b2b")
    # capacitar_equipo es la señal de interés B2B indicada por el caso.
    assert resultado["total"] == 65
    assert resultado["banda"] == "tibio"


def test_rutas_sugeridas():
    assert ruta_sugerida("b2b", 1, False) == "ventas_corporativas"
    assert ruta_sugerida("b2c", 70, True) == "asesoria_inversion"
    assert ruta_sugerida("b2c", 70, False) == "programa_inicial"
    assert ruta_sugerida("b2c", 40, False) == "nutricion_educativa"
    assert ruta_sugerida("b2c", 39, False) == "automatico"
