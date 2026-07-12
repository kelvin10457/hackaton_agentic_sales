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
from tools.inferir_senales import inferir_senales
from tools.obtener_preguntas import siguiente_pregunta


class RespuestaTurno(TypedDict, total=False):
    mensaje: str
    fuentes: list[dict]          # [{"cita_visible": str}]
    estado_flujo: str
    badge_tipo: Optional[str]    # "B2C" | "B2B" | None
    guardrail: Optional[str]     # "G1" | "G2" | ... | None
    accion: Optional[str]        # "proponer_quiz" | "pedir_email" | None
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
    # Ambiguo (p. ej. un saludo) → PROSPECTO: evita disparar un G2 innecesario.
    # TUTOR solo se activa con keywords financieras explícitas.
    return "PROSPECTO"


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


# Señales que, si están presentes, ya permiten clasificar al prospecto.
_SENALES_CALIFICACION = (
    "objetivo", "monto_declarado_usd", "horizonte", "experiencia_inversion",
    "num_colaboradores", "presupuesto_capacitacion_usd",
)


def _seguir_acompanando(
    mensaje: str,
    historial: list[dict],
    accion: Optional[str],
) -> str:
    """El prospecto sigue escribiendo con la calificación ya completa.

    Con LLM: responde con naturalidad (sin volver a preguntar nada).
    Sin LLM: una frase fija que no cierra la puerta y mantiene viva la acción
    pendiente. En ningún caso se repite la pregunta ni el cierre anterior.
    """
    if _hay_llm():
        try:
            from tools.conversar_prospecto import conversar_prospecto
            r = conversar_prospecto(historial + [{"rol": "usuario", "texto": mensaje}])
            if (r.mensaje_agente or "").strip():
                return r.mensaje_agente.strip()
        except Exception:
            pass

    if accion == "proponer_quiz":
        return (
            "Sin problema. Cuando quieras, el quiz de perfil está aquí abajo — son "
            "3 preguntas. Y si prefieres, puedo explicarte primero cualquier "
            "concepto: ¿qué es un ETF, la diversificación, el interés compuesto…?"
        )
    return (
        "Sin problema, no hay prisa. Cuando quieras me dejas tu correo y te lo "
        "hago llegar. Mientras tanto, ¿te explico algún concepto?"
    )


def _turno_prospecto(
    mensaje: str,
    historial: list[dict],
    quiz_perfil: Optional[str] = None,
) -> RespuestaTurno:
    """Calificación (Biblia §7).

    Las preguntas NO las improvisa el LLM: salen de `config/preguntas_*.yaml`
    (T2 · criterio 1.1 "preguntas configurables"). El grafo decide QUÉ preguntar;
    el modelo, a lo sumo, extrae señales de la respuesta.

    Ninguna pregunta se repite: ni las ya contestadas, ni las ya formuladas.
    """
    textos_usuario = [m["texto"] for m in historial if m.get("rol") == "usuario"]
    textos_usuario.append(mensaje)

    senales = inferir_senales(textos_usuario, quiz_perfil=quiz_perfil)
    tipo = senales["segmento"]                    # "b2c" | "b2b"

    # Badge B2B/B2C — solo con evidencia, nunca adivinado.
    badge: Optional[str] = None
    if tipo == "b2b":
        badge = "B2B"
    elif any(senales.get(s) not in (None, "") for s in _SENALES_CALIFICACION):
        badge = "B2C"

    # Lo que el agente YA preguntó (para no insistir).
    ya_preguntadas = {
        m["texto"] for m in historial if m.get("rol") == "agente" and m.get("texto")
    }

    pregunta = siguiente_pregunta(tipo, senales, ya_preguntadas)

    if pregunta is not None:
        # ← El texto sale del YAML, literal. Cambiarlo es editar config/.
        texto = pregunta["texto"]
        estado_flujo = "calificacion"
        accion = None
    else:
        # Calificación completa. Siguiente paso del embudo (Biblia §7).
        if tipo == "b2c" and quiz_perfil is None:
            # B2C → EDUCACION: el quiz determinista de perfil de riesgo.
            texto = (
                "Con esto ya tengo tu panorama. Antes de conectarte con alguien, "
                "¿quieres descubrir tu perfil de inversionista? Son 3 preguntas y "
                "el resultado te lo llevas tú."
            )
            estado_flujo = "educacion"
            accion = "proponer_quiz"
        else:
            # B2B no tiene quiz (Biblia §2.5), y el B2C que ya lo hizo tampoco.
            # → IDENTIFICACION_2: el email, a cambio de valor.
            texto = (
                "Perfecto, con esto ya puedo preparar una propuesta para tu equipo. "
                "¿A qué correo corporativo te la envío?"
                if tipo == "b2b"
                else
                "Listo. ¿A qué correo te envío tu resultado y una ruta de "
                "aprendizaje de 3 pasos?"
            )
            estado_flujo = "identificacion_2"
            accion = "pedir_email"

        # Si el cierre ya se dijo y el prospecto sigue escribiendo, no se repite
        # la misma frase como un loro: se le acompaña sin perder la acción
        # pendiente (el botón del quiz / la captura de email siguen en pantalla).
        if texto in ya_preguntadas:
            texto = _seguir_acompanando(mensaje, historial, accion)

    texto, disparos = evaluar_salida_agente(texto)

    return RespuestaTurno(
        mensaje=texto,
        fuentes=[],
        estado_flujo=estado_flujo,
        badge_tipo=badge,
        guardrail=None,
        accion=accion,
        disparos=disparos,
    )


# ── Entrada pública ───────────────────────────────────────────────────────────

def procesar_turno(
    historial: list[dict],
    mensaje_usuario: str,
    quiz_perfil: Optional[str] = None,
) -> RespuestaTurno:
    """Procesa UN turno del chat público y devuelve la respuesta del agente.

    `historial` es la lista de mensajes PREVIOS [{"rol", "texto", "fuentes"?}].
    `mensaje_usuario` es el texto que acaba de enviar el prospecto (aún no incluido
    en `historial`).
    `quiz_perfil` es el perfil de riesgo si el prospecto ya completó el quiz
    determinista — evita volver a ofrecérselo.
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
    return _turno_prospecto(mensaje_usuario, historial, quiz_perfil=quiz_perfil)
