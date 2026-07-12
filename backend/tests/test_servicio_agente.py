"""
Cobertura del servicio de turno del chat (core/servicio_agente) en MODO
DEGRADADO: sin OPENROUTER_API_KEY, el agente no llama al LLM pero sigue
respondiendo con el corpus aprobado (RAG determinista) y aplicando guardrails.

Esto prueba que la superficie web queda conectada al núcleo agéntico sin
depender de una clave de API (el chat nunca lanza 500).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.pop("OPENROUTER_API_KEY", None)  # forzar modo degradado

from core.servicio_agente import procesar_turno


def test_turno_tutor_devuelve_respuesta_fundamentada():
    r = procesar_turno([], "¿Qué es un ETF?")
    assert r["mensaje"]
    assert r["estado_flujo"] == "educacion"
    # Con corpus disponible, ofrece el quiz y cita fuentes.
    assert r["accion"] == "proponer_quiz"
    assert r["fuentes"] and r["fuentes"][0]["cita_visible"]


def test_turno_g1_intercepta_asesoramiento():
    r = procesar_turno([], "¿en qué invierto mi dinero?")
    assert r["guardrail"] == "G1"
    assert "asesor" in r["mensaje"].lower()
    assert r["fuentes"] == []


def test_turno_g2_negativa_honesta_fuera_de_corpus():
    r = procesar_turno([], "explícame la fotosíntesis del maíz en detalle")
    assert r["guardrail"] == "G2"
    assert r["fuentes"] == []


def test_turno_vacio_no_rompe():
    r = procesar_turno([], "   ")
    assert r["mensaje"]  # responde algo, nunca lanza excepción


def test_disparos_se_reportan_para_auditoria():
    r = procesar_turno([], "¿en qué invierto mi dinero?")
    disparos = r.get("disparos", [])
    assert disparos and disparos[0].guardrail == "G1"
