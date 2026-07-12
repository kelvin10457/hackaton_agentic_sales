"""
Criterio 1.1 — "aplica preguntas CONFIGURABLES".

Las preguntas salen de config/preguntas_*.yaml, no de un prompt. Cambiar el YAML
cambia lo que pregunta el agente, sin tocar código. Y nunca se repite una
pregunta (Biblia §7 · Contrato 4 de R3).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.pop("OPENROUTER_API_KEY", None)   # determinista, sin LLM

import yaml

from core.servicio_agente import procesar_turno
from tools.obtener_preguntas import obtener_preguntas, siguiente_pregunta

_CONFIG = Path(__file__).parent.parent / "config"


def _textos_yaml(tipo: str) -> list[str]:
    datos = yaml.safe_load((_CONFIG / f"preguntas_{tipo}.yaml").read_text(encoding="utf-8"))
    return [p["texto"] for p in datos["calificacion"]]


# ── T2 · obtener_preguntas (código puro) ─────────────────────────────────────

def test_las_preguntas_vienen_del_yaml():
    b2c = obtener_preguntas("b2c", "calificacion")
    assert b2c and all("texto" in p and "senal" in p for p in b2c)
    assert [p["texto"] for p in b2c] == _textos_yaml("b2c")


def test_no_pregunta_una_senal_que_ya_tiene():
    senales = {"objetivo": "invertir"}
    siguiente = siguiente_pregunta("b2c", senales)
    assert siguiente is not None
    assert siguiente["senal"] != "objetivo", "repitió una pregunta ya contestada"


def test_no_insiste_con_una_pregunta_ya_formulada():
    """Si el extractor no logró mapear la respuesta, se avanza igual."""
    preguntas = obtener_preguntas("b2c", "calificacion")
    primera = preguntas[0]["texto"]
    siguiente = siguiente_pregunta("b2c", {}, ya_preguntadas={primera})
    assert siguiente is not None
    assert siguiente["texto"] != primera, "se quedó en bucle repitiendo la pregunta"


def test_sin_preguntas_pendientes_devuelve_none():
    senales = {
        "objetivo": "invertir", "monto_declarado_usd": 10000,
        "horizonte": "1-3m", "experiencia_inversion": "ninguna",
    }
    assert siguiente_pregunta("b2c", senales) is None


# ── El agente las usa de verdad ──────────────────────────────────────────────

def _conversar(guion: list[str], quiz: str | None = None) -> list[dict]:
    historial: list[dict] = []
    salidas = []
    for mensaje in guion:
        r = procesar_turno(historial, mensaje, quiz_perfil=quiz)
        historial.append({"rol": "usuario", "texto": mensaje})
        historial.append({"rol": "agente", "texto": r["mensaje"]})
        salidas.append(r)
    return salidas


def test_b2c_el_agente_hace_las_preguntas_del_yaml_sin_repetir():
    salidas = _conversar([
        "Hola",
        "Quiero invertir mis ahorros",
        "Tengo unos 10.000 dolares",
        "Me gustaria verlo en unos meses",
    ])
    dichos = [r["mensaje"] for r in salidas]
    del_yaml = _textos_yaml("b2c")

    assert len(dichos) == len(set(dichos)), "el agente repitió un mensaje"
    assert sum(1 for m in dichos if m in del_yaml) >= 3, \
        "el agente no está usando las preguntas de config/"


def test_b2c_tras_calificar_ofrece_el_quiz():
    salidas = _conversar([
        "Quiero invertir", "Tengo 10.000 dolares", "lo quiero ya", "nunca he invertido",
    ])
    assert salidas[-1]["accion"] == "proponer_quiz"


def test_b2c_que_ya_hizo_el_quiz_no_lo_vuelve_a_ofrecer():
    """Contrato 4: no se repite un paso ya completado."""
    salidas = _conversar(
        ["quiero invertir 10000 ya, nunca he invertido", "listo"],
        quiz="moderado",
    )
    assert all(r["accion"] != "proponer_quiz" for r in salidas)
    assert salidas[-1]["accion"] == "pedir_email"


def test_b2b_se_clasifica_y_no_tiene_quiz():
    """Un juez VA a escribir 'represento a una empresa'. B2B no puede romperse.
    El quiz es de perfil de riesgo PERSONAL: no aplica (Biblia §2.5)."""
    salidas = _conversar([
        "Represento a una empresa de 100 empleados",
        "Queremos capacitar al equipo",
        "Tenemos 8.000 dolares de presupuesto",
        "Nos gustaria implementarlo este mes",
    ])
    assert all(r["badge_tipo"] == "B2B" for r in salidas), "B2B mal clasificado"
    assert all(r["accion"] != "proponer_quiz" for r in salidas), "B2B no lleva quiz"
    assert salidas[-1]["accion"] == "pedir_email"

    dichos = [r["mensaje"] for r in salidas]
    assert sum(1 for m in dichos if m in _textos_yaml("b2b")) >= 3


def test_nunca_se_queda_en_bucle_si_no_entiende_la_respuesta():
    salidas = _conversar(["Quiero invertir", "mmm no se", "ni idea", "paso", "bueno"])
    dichos = [r["mensaje"] for r in salidas]
    assert len(dichos) == len(set(dichos)), "se quedó repitiendo el mismo mensaje"
