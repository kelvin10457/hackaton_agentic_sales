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
# El flujo v2 arranca con la identificación progresiva (pide el nombre), así que
# los guiones incluyen el nombre y el helper lo propaga como lo hace el router.

def _conversar(guion: list[str], quiz: str | None = None) -> list[dict]:
    historial: list[dict] = []
    salidas = []
    nombre: str | None = None
    for mensaje in guion:
        r = procesar_turno(historial, mensaje, quiz_perfil=quiz, nombre=nombre)
        if r.get("nombre_detectado"):
            nombre = r["nombre_detectado"]
        historial.append({"rol": "usuario", "texto": mensaje})
        historial.append({"rol": "agente", "texto": r["mensaje"]})
        salidas.append(r)
    return salidas


def test_b2c_el_agente_hace_las_preguntas_del_yaml_sin_repetir():
    salidas = _conversar([
        "Hola",
        "Kenny",                      # ← identificación progresiva
        "Quiero invertir mis ahorros",
        "Tengo unos 10.000 dolares",
        "Me gustaria verlo en unos meses",
    ])
    dichos = [r["mensaje"] for r in salidas]
    del_yaml = _textos_yaml("b2c")

    assert len(dichos) == len(set(dichos)), "el agente repitió un mensaje"
    # Las preguntas del YAML aparecen embebidas (con acuse de recibo delante):
    # "Anotado, Kenny: USD 10.000. ¿En cuánto tiempo...?".
    usadas = sum(1 for m in dichos if any(p in m for p in del_yaml))
    assert usadas >= 3, "el agente no está usando las preguntas de config/"


def test_b2c_tras_calificar_ofrece_el_quiz():
    salidas = _conversar([
        "Kenny", "Quiero invertir", "Tengo 10.000 dolares", "lo quiero ya",
        "nunca he invertido",
    ])
    assert salidas[-1]["accion"] == "proponer_quiz"


def test_b2c_que_ya_hizo_el_quiz_no_lo_vuelve_a_ofrecer():
    """Contrato 4: no se repite un paso ya completado. Con el quiz hecho y el
    email capturado, jamás se vuelve a ofrecer ni el quiz ni el correo."""
    r = procesar_turno(
        [{"rol": "usuario", "texto": "quiero invertir 10000 ya, nunca he invertido"},
         {"rol": "agente", "texto": "Listo. ¿A qué correo te envío tu resultado?"}],
        "cualquier cosa", quiz_perfil="moderado", nombre="Kenny", email_capturado=True,
    )
    assert r["accion"] != "proponer_quiz"
    assert "correo" not in r["mensaje"].lower()


def test_b2b_se_clasifica_y_no_tiene_quiz():
    """Un juez VA a escribir 'represento a una empresa'. B2B no puede romperse.
    El quiz es de perfil de riesgo PERSONAL: no aplica (Biblia §2.5)."""
    salidas = _conversar([
        "Represento a una empresa de 100 empleados",
        "Ana",
        "Queremos capacitar al equipo",
        "Tenemos 8.000 dolares de presupuesto",
        "Nos gustaria implementarlo este mes",
    ])
    # Una vez que hay señales B2B, el badge es B2B (el saludo inicial puede ser None).
    badges = [r["badge_tipo"] for r in salidas if r["badge_tipo"]]
    assert badges and all(b == "B2B" for b in badges), "B2B mal clasificado"
    assert all(r["accion"] != "proponer_quiz" for r in salidas), "B2B no lleva quiz"
    assert salidas[-1]["accion"] == "pedir_email"

    dichos = [r["mensaje"] for r in salidas]
    assert sum(1 for m in dichos if any(p in m for p in _textos_yaml("b2b"))) >= 3


def test_nunca_se_queda_en_bucle_si_no_entiende_la_respuesta():
    salidas = _conversar(
        ["Kenny", "Quiero invertir", "mmm no se", "ni idea", "paso", "bueno"]
    )
    dichos = [r["mensaje"] for r in salidas]
    assert len(dichos) == len(set(dichos)), "se quedó repitiendo el mismo mensaje"
