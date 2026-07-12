"""
core/servicio_agente.py — Entrada del núcleo agéntico para la superficie HTTP.

El grafo de LangGraph (core/orquestador.py) está pensado para un flujo lineal
con `interrupt()` (ideal para la demo por CLI de prueba_local.py). La superficie
web, en cambio, es petición/respuesta: cada POST /api/chat/mensaje debe procesar
UN turno y devolver la respuesta del agente, mientras el frontend maneja el quiz
y el consentimiento como pasos propios (tarjeta y modal).

Este servicio expone ese "un turno" reutilizando EXACTAMENTE el mismo cerebro de
R1 (las tools que llaman al LLM) y el mismo bloque de guardrails. Así:
  - Cada mensaje web despierta al LLM (vía las tools de R1).            [README #1]
  - Los guardrails G1/G1-bis/G2/G5/G6/G7 se aplican en cada turno.     [Manual R1 §9]
  - Si no hay OPENROUTER_API_KEY, degrada a respuestas deterministas
    fundamentadas en el corpus, sin romper el chat (nunca lanza 500).

Regla arquitectónica: este módulo vive en core/ y solo importa de tools/,
schemas/ y core/. Nunca importa app/ ni web/.
"""
from __future__ import annotations

import os
from typing import Optional, TypedDict

from core.guardrails import (
    evaluar_entrada_usuario,
    evaluar_salida_agente,
    respuesta_g2,
    DisparoGuardrail,
    nuevo_disparo,
)
from tools.buscar_conocimiento import buscar_conocimiento


class RespuestaTurno(TypedDict, total=False):
    mensaje: str
    fuentes: list[dict]          # [{"cita_visible": str}]
    estado_flujo: str
    badge_tipo: Optional[str]    # "B2C" | "B2B" | None
    guardrail: Optional[str]     # "G1" | "G2" | ... | None
    accion: Optional[str]        # "proponer_quiz" | None
    disparos: list[DisparoGuardrail]


# ── Detección de disponibilidad del LLM ───────────────────────────────────────

def _hay_llm() -> bool:
    """True si podemos llamar al LLM (hay key y el SDK está instalado)."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        return False
    try:
        import openai  # noqa: F401
    except Exception:
        return False
    return True


# ── Detección de modo (misma heurística que el orquestador) ───────────────────

_KEYWORDS_TUTOR = {
    "aprender", "educación", "educacion", "entender", "explicar", "explícame",
    "explicame", "qué es", "que es", "cómo funciona", "como funciona", "enseñar",
    "enséñame", "enseñame", "qué son", "que son", "información sobre",
    "informacion sobre", "saber más", "saber mas", "concepto", "definición",
    "definicion", "diferencia entre", "aprendizaje", "etf", "fondo", "acciones",
    "diversificación", "diversificacion", "interés compuesto", "interes compuesto",
    "inflación", "inflacion", "riesgo",
}

_KEYWORDS_ASESOR = {
    "asesor", "hablar con alguien", "contactar", "reunión", "reunion",
    "necesito ayuda con mi", "para mi empresa", "somos una empresa",
    "capacitar", "cotización", "cotizacion", "propuesta",
}


def _detectar_modo(mensaje: str, historial: list[dict]) -> str:
    """TUTOR (educación) o PROSPECTO (consultoría comercial). Pegajoso: si ya
    veníamos educando, un mensaje corto no cambia de modo bruscamente."""
    texto = mensaje.lower()
    if any(k in texto for k in _KEYWORDS_ASESOR):
        return "PROSPECTO"
    if any(k in texto for k in _KEYWORDS_TUTOR):
        return "TUTOR"
    # Continuidad: si el último turno del agente fue educativo, seguimos en tutor.
    for m in reversed(historial):
        if m.get("rol") == "agente":
            if m.get("fuentes"):
                return "TUTOR"
            break
    # Mensaje inicial ambiguo y corto → tutor (menos invasivo que vender).
    return "PROSPECTO" if len(texto.split()) > 6 else "TUTOR"


# ── Utilidades de fuentes ─────────────────────────────────────────────────────

def _fuentes_desde_docs(docs: list[dict]) -> list[dict]:
    return [{"cita_visible": d.get("cita_visible") or d.get("id", "")} for d in docs]


# ── Rama TUTOR ────────────────────────────────────────────────────────────────

def _turno_tutor(mensaje: str, historial: list[dict]) -> RespuestaTurno:
    docs = buscar_conocimiento(mensaje, top_k=3)

    # G2 · Negativa honesta: sin respaldo en el corpus, no se inventa nada.
    if not docs:
        return RespuestaTurno(
            mensaje=respuesta_g2(),
            fuentes=[],
            estado_flujo="educacion",
            badge_tipo=None,
            guardrail="G2",
            accion=None,
            disparos=[nuevo_disparo("G2", "El RAG no encontró documentos aprobados.", mensaje)],
        )

    texto = ""
    if _hay_llm():
        try:
            from tools.responder_tutor import responder_tutor
            resultado = responder_tutor(mensaje, historial)
            if resultado.get("documentos_usados", 0) == 0:
                return RespuestaTurno(
                    mensaje=respuesta_g2(), fuentes=[], estado_flujo="educacion",
                    badge_tipo=None, guardrail="G2", accion=None,
                    disparos=[nuevo_disparo("G2", "El tutor no usó documentos aprobados.", mensaje)],
                )
            texto = (resultado.get("respuesta") or "").strip()
        except Exception:
            texto = ""  # cae al modo determinista abajo

    # Degradación sin LLM (o si falló): respuesta fundamentada en el corpus.
    if not texto:
        doc = docs[0]
        extracto = doc["contenido"].strip()
        if len(extracto) > 480:
            extracto = extracto[:480].rsplit(" ", 1)[0] + "…"
        texto = (
            f"Según el material aprobado de Futuro Academy ({doc['cita_visible']}):\n\n"
            f"{extracto}\n\n¿Quieres que profundice en algún punto?"
        )

    # Guardrails de SALIDA (G1-bis, G7, G5).
    texto, disparos = evaluar_salida_agente(texto)

    return RespuestaTurno(
        mensaje=texto,
        fuentes=_fuentes_desde_docs(docs),
        estado_flujo="educacion",
        badge_tipo=None,
        guardrail=None,
        accion="proponer_quiz",   # el frontend ofrece el quiz de perfil de riesgo
        disparos=disparos,
    )


# ── Rama PROSPECTO ────────────────────────────────────────────────────────────

_BADGE = {"B2B": "B2B", "B2C": "B2C"}


def _turno_prospecto(mensaje: str, historial: list[dict]) -> RespuestaTurno:
    badge: Optional[str] = None
    texto = ""

    if _hay_llm():
        try:
            from tools.conversar_prospecto import conversar_prospecto
            conv = historial + [{"rol": "usuario", "texto": mensaje}]
            r = conversar_prospecto(conv)
            texto = (r.mensaje_agente or "").strip()
            badge = _BADGE.get(r.tipo_prospecto_detectado)
        except Exception:
            texto = ""

    # Degradación sin LLM: consultoría breve y determinista para no romper el chat.
    if not texto:
        turnos_usuario = sum(1 for m in historial if m.get("rol") == "usuario")
        if turnos_usuario == 0:
            texto = (
                "Cuéntame un poco más: ¿buscas empezar a invertir tus ahorros, "
                "aprender sobre un tema en particular, o es para tu empresa?"
            )
        else:
            texto = (
                "Entiendo. Para darte la mejor guía y, si lo deseas, conectarte con "
                "un asesor de Futuro Academy, ¿podrías contarme cuál es tu objetivo "
                "principal y en qué plazo te gustaría lograrlo?"
            )

    texto, disparos = evaluar_salida_agente(texto)

    return RespuestaTurno(
        mensaje=texto,
        fuentes=[],
        estado_flujo="calificacion",
        badge_tipo=badge,
        guardrail=None,
        accion=None,
        disparos=disparos,
    )


# ── Entrada pública ───────────────────────────────────────────────────────────

def procesar_turno(historial: list[dict], mensaje_usuario: str) -> RespuestaTurno:
    """Procesa UN turno del chat público y devuelve la respuesta del agente.

    `historial` es la lista de mensajes PREVIOS [{"rol", "texto", "fuentes"?}].
    `mensaje_usuario` es el texto que acaba de enviar el prospecto (aún no incluido
    en `historial`).
    """
    mensaje_usuario = (mensaje_usuario or "").strip()
    if not mensaje_usuario:
        return RespuestaTurno(
            mensaje="¿Podrías escribir tu pregunta? Estoy aquí para ayudarte.",
            fuentes=[], estado_flujo="saludo", badge_tipo=None,
            guardrail=None, accion=None, disparos=[],
        )

    # 1) Guardrails de ENTRADA (G1 no-asesoramiento, G6 alcance temático).
    respuesta_fija, disparo = evaluar_entrada_usuario(mensaje_usuario)
    if respuesta_fija is not None:
        return RespuestaTurno(
            mensaje=respuesta_fija,
            fuentes=[],
            estado_flujo="educacion",
            badge_tipo=None,
            guardrail=disparo.guardrail if disparo else None,
            accion=None,
            disparos=[disparo] if disparo else [],
        )

    # 2) Enrutar por modo y delegar en el cerebro de R1.
    modo = _detectar_modo(mensaje_usuario, historial)
    if modo == "TUTOR":
        return _turno_tutor(mensaje_usuario, historial)
    return _turno_prospecto(mensaje_usuario, historial)
