"""
RAG tolerante: la recuperación ya no exige la palabra literal del corpus.
Bloquea la regresión reportada ("riesgos" no encontraba "perfil de riesgo") y
protege la precisión (fuera de dominio sigue dando negativa honesta / vacío).
Deterministas: sin LLM.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.pop("OPENROUTER_API_KEY", None)

from tools.buscar_conocimiento import buscar_conocimiento, listar_temas
from core.servicio_agente import procesar_turno


# ── Recall: variantes no literales SÍ encuentran la fuente ────────────────────

def test_plural_encuentra_singular():
    # "riesgos" debe traer el doc de "perfil de riesgo" (FA-003).
    ids = [d["id"] for d in buscar_conocimiento("riesgos")]
    assert "FA-003" in ids


def test_sin_tildes_y_prefijo():
    assert any(d["id"] == "FA-004" for d in buscar_conocimiento("inflacion"))
    assert any(d["id"] == "FA-009" for d in buscar_conocimiento("comisiones altas"))
    # familia verbo↔sustantivo: "diversificar" ~ "diversificación" (FA-007)
    assert any(d["id"] == "FA-007" for d in buscar_conocimiento("diversificar mi dinero"))


# ── Precisión: fuera de dominio devuelve vacío (→ G2) ─────────────────────────

def test_fuera_de_corpus_sigue_vacio():
    assert buscar_conocimiento("explicame la fotosintesis del maiz en detalle") == []
    assert buscar_conocimiento("quien gano el mundial") == []


# ── Catálogo de temas: respuesta directa, nunca negativa honesta ──────────────

def test_pregunta_por_temas_no_da_guardrail():
    r = procesar_turno([], "¿qué temas puedes explicarme?")
    assert r.get("guardrail") != "G2"
    assert r["fuentes"]                      # cita el índice
    assert "temas" in r["mensaje"].lower()


def test_listar_temas_no_incluye_el_indice():
    ids = [t["id"] for t in listar_temas()]
    assert "FA-000" not in ids
    assert "FA-003" in ids and len(ids) >= 10
