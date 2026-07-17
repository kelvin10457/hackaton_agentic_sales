"""
Lógica de reanudación + intenciones explícitas (Resumption Logic).
El agente no pierde el estado del embudo: puede reabrir el quiz / el correo si el
usuario lo pide, y retoma el paso pendiente ante mensajes neutrales.
Deterministas: sin LLM.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.pop("OPENROUTER_API_KEY", None)

from core.servicio_agente import procesar_turno

_OFERTA = [{"rol": "agente", "texto": "Te propongo el quiz de perfil de inversionista."}]


def _accion(msg, hist=None, quiz=None, email=False):
    return procesar_turno(hist or [], msg, quiz_perfil=quiz, nombre="Kenny",
                          email_capturado=email).get("accion")


# ── Intención explícita de quiz (fuerza el quiz, NO va a RAG) ──────────────────

def test_pide_quiz_explicito_abre_quiz():
    for m in ["quiero el quiz", "test de riesgo", "empezar test", "dame el quiz ya"]:
        assert _accion(m) == "abrir_quiz", m


def test_pregunta_sobre_el_test_no_es_intencion_de_quiz():
    # "¿qué es el test de riesgo?" es educativa, no una orden de abrir el quiz.
    assert _accion("que es el test de riesgo?") != "abrir_quiz"


def test_quiz_explicito_ya_hecho_no_se_repite():
    a = _accion("quiero el quiz", quiz="conservador", email=False)
    assert a == "pedir_email"           # ya lo hizo → siguiente paso pendiente


# ── Intención explícita de registro → intercepción temprana ───────────────────

def test_pide_registrarse_pide_email_de_inmediato():
    for m in ["quiero registrarme", "quiero hablar con un asesor",
              "autorizar datos", "quiero dar mi correo"]:
        assert _accion(m) == "pedir_email", m


def test_negacion_no_dispara_registro():
    assert _accion("no quiero registrarme") != "pedir_email"


# ── Reanudación ante mensaje neutral ──────────────────────────────────────────

def test_neutral_tras_oferta_retoma_quiz():
    assert _accion("gracias", hist=_OFERTA) in ("proponer_quiz", "abrir_quiz")


def test_neutral_con_quiz_hecho_retoma_email():
    assert _accion("ok", hist=_OFERTA, quiz="moderado", email=False) == "pedir_email"


def test_neutral_sin_embudo_iniciado_no_fuerza_nada():
    # Sin oferta previa ni quiz, "ok" no debe empujar quiz/email de la nada.
    assert _accion("ok") not in ("abrir_quiz", "pedir_email")
