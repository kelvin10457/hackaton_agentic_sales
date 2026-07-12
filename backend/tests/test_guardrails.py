"""test_guardrails — G1: no-asesoramiento de inversión. Biblia §19/§20."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.guardrails.g1_no_asesoramiento import se_dispara_g1, respuesta_g1


def test_g1_se_dispara_con_pregunta_directa():
    assert se_dispara_g1("¿En qué invierto mi dinero?")
    assert se_dispara_g1("¿Me conviene comprar ahora?")
    assert se_dispara_g1("¿Cuál es mejor, ETF o fondo?")
    assert se_dispara_g1("¿Es buen momento para invertir?")


def test_g1_no_se_dispara_con_pregunta_educativa():
    assert not se_dispara_g1("¿Qué es un ETF?")
    assert not se_dispara_g1("Quiero aprender sobre diversificación")
    assert not se_dispara_g1("Tengo 5000 dólares ahorrados")


def test_g1_respuesta_nunca_nombra_un_producto():
    """La respuesta es una plantilla fija — nunca la genera el LLM,
    así que nunca puede "resbalarse" y nombrar un producto financiero."""
    respuesta = respuesta_g1()
    assert "fondo conservador" not in respuesta.lower()
    assert "acciones de" not in respuesta.lower()
    assert "asesor" in respuesta.lower()  # sí debe redirigir a un asesor
