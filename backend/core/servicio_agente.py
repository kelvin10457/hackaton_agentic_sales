"""
core/servicio_agente.py — Entrada del núcleo agéntico para la superficie HTTP.

Cada POST /api/chat/mensaje procesa UN turno. El flujo conversacional es una
máquina de estados determinista (Biblia §7) que se deriva del HISTORIAL — el
servicio es stateless: mismo historial → misma respuesta.

  SALUDO → IDENTIFICACION_1 (nombre) → CALIFICACION (preguntas de config/)
        → EDUCACION (quiz B2C) → IDENTIFICACION_2 (email) → CONSENTIMIENTO
  (el tutor RAG es alcanzable desde CUALQUIER estado: una pregunta educativa
   siempre se responde, y luego se retoma el embudo)

Principios que este archivo garantiza:
  · Las preguntas salen de config/ (criterio 1.1). Ninguna se repite.
  · La respuesta del prospecto se ATRIBUYE a la pregunta que se le hizo:
    "10 000" al preguntar el monto ES un monto; "no" a "¿has invertido?" ES
    "ninguna". Si no calza, se intenta con las demás señales (cross-parse) y
    se aclara UNA sola vez — jamás un bucle.
  · Los acuses de recibo son plantillas con el nombre del prospecto: calidez
    sin abrir la puerta a la alucinación (G7: el LLM no toca cifras).
  · El quiz jamás lo improvisa el LLM (G-QUIZ). Pedirlo por texto abre el real.
  · Si el email ya se capturó (o se rechazó), NO se vuelve a pedir.

Regla arquitectónica: core/ solo importa tools/ y core/. Nunca app/ ni web/.
"""
from __future__ import annotations

import os
import re
import unicodedata
from typing import Optional, TypedDict


def _norm(s: str) -> str:
    """minúsculas sin tildes, para comparar intención sin depender de la grafía."""
    base = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in base if not unicodedata.combining(c))

from core.guardrails import (
    evaluar_entrada_usuario,
    evaluar_salida_agente,
    respuesta_g2,
    DisparoGuardrail,
    nuevo_disparo,
)
from tools.buscar_conocimiento import buscar_conocimiento, listar_temas
from tools.inferir_senales import (
    acuse_de_recibo,
    cross_parse,
    es_despedida,
    es_saludo,
    extraer_nombre_intro,
    inferir_senales,
    parse_nombre,
    parsear_respuesta,
)
from tools.obtener_preguntas import obtener_preguntas, siguiente_pregunta


class RespuestaTurno(TypedDict, total=False):
    mensaje: str
    fuentes: list[dict]          # [{"cita_visible": str}]
    estado_flujo: str
    badge_tipo: Optional[str]    # "B2C" | "B2B" | None
    guardrail: Optional[str]     # "G1" | "G2" | ... | None
    accion: Optional[str]        # "proponer_quiz" | "abrir_quiz" | "pedir_email" | None
    nombre_detectado: Optional[str]
    disparos: list[DisparoGuardrail]


def _respuesta(
    mensaje: str,
    *,
    fuentes: list[dict] | None = None,
    estado_flujo: str = "calificacion",
    badge_tipo: Optional[str] = None,
    guardrail: Optional[str] = None,
    accion: Optional[str] = None,
    nombre_detectado: Optional[str] = None,
    disparos: list[DisparoGuardrail] | None = None,
) -> RespuestaTurno:
    return RespuestaTurno(
        mensaje=mensaje, fuentes=fuentes or [], estado_flujo=estado_flujo,
        badge_tipo=badge_tipo, guardrail=guardrail, accion=accion,
        nombre_detectado=nombre_detectado, disparos=disparos or [],
    )


# ── Disponibilidad del LLM ────────────────────────────────────────────────────

def _hay_llm() -> bool:
    if not os.environ.get("OPENROUTER_API_KEY"):
        return False
    try:
        import openai  # noqa: F401
    except Exception:
        return False
    return True


# ── Textos fijos del flujo (plantillas; el LLM no las redacta) ───────────────

def _txt_pregunta_nombre() -> str:
    """La pregunta del nombre viene de config/ (criterio 1.1)."""
    for p in obtener_preguntas("b2c", "identificacion"):
        if p.get("id") == "nombre":
            return p["texto"]
    return "Encantado. ¿Cómo te llamas?"


_MARK_QUIZ_OFERTA = "perfil de inversionista"
_MARK_EMAIL = "correo te envío"
_MARK_EMAIL_B2B = "correo corporativo"
_MARK_POST_EMAIL = "¿Te ayudo con algo más"


def _oferta_quiz(nombre: Optional[str]) -> str:
    n = f", {nombre}" if nombre else ""
    return (
        f"Con esto ya tengo tu panorama{n}. Antes de conectarte con alguien, "
        "¿quieres descubrir tu perfil de inversionista? Son 3 preguntas y el "
        "resultado te lo llevas tú."
    )


def _pedir_email(tipo: str, nombre: Optional[str]) -> str:
    n = f", {nombre}" if nombre else ""
    if tipo == "b2b":
        return (
            f"Perfecto{n}, con esto ya puedo preparar una propuesta para tu "
            "equipo. ¿A qué correo corporativo te la envío?"
        )
    return (
        f"Listo{n}. ¿A qué correo te envío tu resultado y una ruta de "
        "aprendizaje de 3 pasos?"
    )


def _post_email(nombre: Optional[str]) -> str:
    n = f", {nombre}" if nombre else ""
    return (
        f"¿Te ayudo con algo más{n}? Puedo explicarte cualquier tema del "
        "material — ETFs, diversificación, interés compuesto, perfil de riesgo…"
    )


def _despedida(nombre: Optional[str], email_capturado: bool) -> str:
    n = f", {nombre}" if nombre else ""
    if email_capturado:
        # CV7: el agente SIEMPRE dice cuándo contactarán.
        return (
            f"¡Gracias por tu visita{n}! Recuerda: un asesor de Futuro Academy "
            "te contactará en las próximas 24 horas hábiles. Cuando quieras "
            "seguir aprendiendo, aquí estaré."
        )
    return (
        f"¡Gracias por tu visita{n}! Cuando quieras seguir aprendiendo sobre "
        "finanzas, aquí estaré."
    )


# ── Detección de intenciones cortas ──────────────────────────────────────────

_QUIZ_INTENT_KW = (
    "quiz", "pregunta", "empez", "comenz", "dale", "listo", "claro", "va",
    "ok", "de una", "adelante", "hágale", "hagale", "el test", "sí", "si",
)


def _quiere_quiz(mensaje: str, ultima_agente: str) -> bool:
    """El prospecto pidió el quiz por TEXTO justo después de la oferta."""
    contexto = _MARK_QUIZ_OFERTA in ultima_agente or "quiz" in ultima_agente.lower()
    if not contexto:
        return False
    bajo = (mensaje or "").lower().strip(" .!¡?¿,")
    if bajo.startswith("no") or "luego" in bajo or "después" in bajo or "despues" in bajo:
        return False
    return any(k in bajo for k in _QUIZ_INTENT_KW) and len(bajo.split()) <= 6


def _rechaza_email(mensaje: str) -> bool:
    bajo = (mensaje or "").lower()
    return (
        ("no" in bajo and "correo" in bajo)
        or "no quiero dar" in bajo
        or "no te voy a dar" in bajo
        or "sin correo" in bajo
        or "no doy mi" in bajo
    )


# ── Intenciones EXPLÍCITAS + reanudación (Resumption Logic) ───────────────────
# El usuario puede pedir el quiz o registrarse en CUALQUIER momento, incluso tras
# una interrupción. Estas intenciones fuerzan el flujo del embudo y NO deben
# clasificarse como pregunta educativa (RAG), que si no interceptaría la petición.

_QUIZ_PALABRAS = ("quiz", "test", "cuestionario")
_QUIZ_VERBOS = (
    "quiero", "quisiera", "hacer", "hagamos", "haganme", "empezar", "empieza",
    "comenzar", "comienza", "iniciar", "inicia", "dame", "damelo", "abrir", "abre",
    "tomar", "realizar", "vamos", "hacerlo", "pasame", "ponme", "necesito", "listo",
)
_QUIZ_NO_INTENCION = ("que es", "que son", "como funciona", "para que sirve",
                      "que significa", "que mide", "en que consiste")


def _intencion_quiz_explicita(mensaje: str) -> bool:
    """True si el usuario pide EXPLÍCITAMENTE el quiz/test (sin depender del
    contexto del turno anterior). No confunde con preguntas SOBRE el test."""
    bajo = _norm(mensaje).strip(" .!¡?¿,")
    if not any(p in bajo for p in _QUIZ_PALABRAS):
        return False
    if bajo.startswith(_QUIZ_NO_INTENCION):
        return False
    if "de riesgo" in bajo or "de perfil" in bajo:   # "test de riesgo"
        return True
    if len(bajo.split()) <= 5:                        # "el quiz", "quiz por favor"
        return True
    return any(v in bajo for v in _QUIZ_VERBOS)


_RE_REGISTRO = re.compile(
    r"(quiero|deseo|me gustaria|puedo|podria|quisiera)\s+"
    r"(registrar|suscrib|recibir|dar(te|me)?\s+mi\s+correo|dejar(te)?\s+mi\s+correo"
    r"|dar(te)?\s+mis?\s+datos|hablar\s+con\s+(un\s+)?asesor|contactar)"
    r"|registrar(me|nos)\b|autoriz(ar|o)\s+(mis\s+)?datos|dar\s+(mi\s+)?consentimiento"
    r"|hablar\s+con\s+(un\s+)?asesor|contactar\s+(a\s+)?(un\s+)?asesor"
    r"|te\s+dejo\s+mi\s+correo|quiero\s+que\s+me\s+contacten",
    re.IGNORECASE,
)


def _intencion_registro(mensaje: str) -> bool:
    """True si el usuario pide registrarse / dar su correo / hablar con un asesor."""
    bajo = _norm(mensaje).strip(" .!¡?¿,")
    if bajo.startswith(("no ", "no,")) or "no quiero" in bajo:
        return False
    return bool(_RE_REGISTRO.search(bajo))


_NEUTRALES = {
    "ok", "okay", "oka", "okey", "vale", "listo", "dale", "perfecto", "gracias",
    "entendido", "entiendo", "sigamos", "continuemos", "sigue", "bien", "genial",
    "va", "bueno", "claro", "de", "acuerdo", "excelente", "correcto", "ya",
}


def _es_neutral(mensaje: str) -> bool:
    """Mensaje corto de transición/agradecimiento tras una interrupción."""
    bajo = _norm(mensaje).strip(" .!¡?¿,")
    palabras = bajo.split()
    if not palabras or len(palabras) > 3:
        return False
    return any(p in _NEUTRALES for p in palabras)


def _reanudacion(
    mensaje: str,
    historial: list[dict],
    quiz_perfil: Optional[str],
    email_capturado: bool,
) -> Optional[RespuestaTurno]:
    """Ante un mensaje neutral, retoma el paso del embudo que quedó pendiente."""
    if not _es_neutral(mensaje):
        return None
    quiz_ofrecido = _veces_dicho(_MARK_QUIZ_OFERTA, historial) > 0
    email_pedido = (
        _veces_dicho(_MARK_EMAIL, historial) > 0
        or _veces_dicho(_MARK_EMAIL_B2B, historial) > 0
    )
    if quiz_ofrecido and not quiz_perfil:
        return _respuesta(
            "Continuemos donde estábamos, ¿te gustaría hacer el quiz? Son 3 "
            "preguntas y toma un minuto.",
            estado_flujo="educacion", accion="proponer_quiz",
        )
    if (quiz_perfil or email_pedido) and not email_capturado:
        return _respuesta(
            "Volviendo a lo anterior, ¿a qué correo te envío los resultados?",
            estado_flujo="identificacion", accion="pedir_email",
        )
    return None


_META_FLUJO = (
    "que sigue", "qué sigue", "y ahora", "ahora que", "ahora qué",
    "como continuo", "cómo continúo", "que hago ahora", "qué hago ahora",
    "en que quedamos", "en qué quedamos", "seguimos",
)


def _es_meta_flujo(mensaje: str) -> bool:
    bajo = (mensaje or "").lower().strip(" .!¡?¿,")
    return any(m in bajo for m in _META_FLUJO) and len(bajo.split()) <= 5


def _pregunta_por_nombre_propio(mensaje: str) -> bool:
    """'¿necesitas mi nombre?' — pregunta META sobre el flujo, no educativa."""
    bajo = (mensaje or "").lower()
    return ("mi nombre" in bajo or "tu nombre" in bajo or "mi correo" in bajo) and "?" in mensaje


# Palabras que, como PRIMERA palabra, indican una pregunta educativa.
# Match por palabra completa: "cualquier" NO es "cuál".
_PALABRAS_PREGUNTA = {
    "qué", "que", "cómo", "como", "cuál", "cual", "cuánto", "cuanto",
    "explica", "explícame", "explicame", "profundiza", "profundízame",
    "dime", "háblame", "hablame", "cuéntame", "cuentame", "quién", "quien",
    "dónde", "donde",
}


def _es_pregunta_educativa(mensaje: str) -> bool:
    if _pregunta_por_nombre_propio(mensaje) or _es_meta_flujo(mensaje):
        return False
    if "?" in mensaje:
        return True
    bajo = (mensaje or "").lower().strip()
    if bajo.startswith(("por qué", "porque ", "diferencia entre")):
        return True
    palabras = bajo.split()
    if not palabras:
        return False
    primera = palabras[0].strip("¿?¡!.,")
    return primera in _PALABRAS_PREGUNTA


# ── Señales desde el historial (atribución pregunta → respuesta) ─────────────

_catalogo_cache: list[tuple[str, str]] | None = None


def _catalogo_preguntas() -> list[tuple[str, str]]:
    """[(texto_pregunta, senal)] de TODAS las preguntas de calificación."""
    global _catalogo_cache
    if _catalogo_cache is None:
        cat: list[tuple[str, str]] = []
        for tipo in ("b2c", "b2b"):
            for p in obtener_preguntas(tipo, "calificacion"):
                if p.get("senal"):
                    cat.append((p["texto"], p["senal"]))
        _catalogo_cache = cat
    return _catalogo_cache


def senales_desde_historial(historial: list[dict], quiz_perfil: Optional[str] = None) -> dict:
    """Señales del contrato, combinando dos fuentes deterministas:

    1. Extracción GLOBAL del texto del prospecto (inferir_senales) — captura lo
       espontáneo ("tengo 10.000 ahorrados") con reglas conservadoras.
    2. ATRIBUCIÓN pregunta→respuesta: si el agente preguntó el monto y el
       prospecto contestó "10 000", eso ES el monto. La atribución pisa a la
       global porque tiene contexto. Si la respuesta no calza con su pregunta,
       se intenta con las otras señales (cross-parse) para no perder el dato.

    La usan el turno del chat Y el enriquecimiento del CRM: una sola verdad.
    """
    textos_usuario = [m.get("texto", "") for m in historial if m.get("rol") == "usuario"]
    senales = inferir_senales(textos_usuario, quiz_perfil=quiz_perfil)

    catalogo = _catalogo_preguntas()
    for i, m in enumerate(historial):
        if m.get("rol") != "agente":
            continue
        texto_agente = m.get("texto") or ""
        senal = next((s for t, s in catalogo if t in texto_agente), None)
        if senal is None:
            continue
        respuesta = next(
            (u.get("texto", "") for u in historial[i + 1:] if u.get("rol") == "usuario"),
            None,
        )
        if respuesta is None:
            continue
        valor = parsear_respuesta(senal, respuesta)
        if valor is not None:
            senales[senal] = valor
        else:
            for s2, v2 in cross_parse(respuesta, excluir=senal).items():
                if senales.get(s2) in (None, ""):
                    senales[s2] = v2
    return senales


# ── Helpers de historial ─────────────────────────────────────────────────────

def _ultima_agente(historial: list[dict]) -> str:
    for m in reversed(historial):
        if m.get("rol") == "agente":
            return m.get("texto") or ""
    return ""


def _veces_dicho(fragmento: str, historial: list[dict]) -> int:
    return sum(
        1 for m in historial
        if m.get("rol") == "agente" and fragmento in (m.get("texto") or "")
    )


# ── Rama TUTOR (RAG con citas) ───────────────────────────────────────────────

def _fuentes_desde_docs(docs: list[dict]) -> list[dict]:
    return [{"cita_visible": d.get("cita_visible") or d.get("id", "")} for d in docs]


# "¿Qué temas puedes explicarme?" / "¿de qué me puedes hablar?" — el agente NO
# debe dar negativa honesta a esto: el catálogo de temas sí lo conoce.
_RE_TEMAS = re.compile(
    r"(qu[eé]\s+temas"
    r"|qu[eé]\s+(me\s+)?puedes\s+(explicar|ense[ñn]ar|responder|contar|hablar)"
    r"|de\s+qu[eé]\s+(me\s+)?(puedes|sabes|hablas)"
    r"|sobre\s+qu[eé]\s+(temas|puedes|me\s+puedes)"
    r"|temas\s+(disponibles|tienes|hay|cubres?|puedes)"
    r"|list[ao]\s+de\s+temas)",
    re.IGNORECASE,
)


def _pregunta_por_temas(mensaje: str) -> bool:
    return bool(_RE_TEMAS.search(mensaje or ""))


def _turno_temas() -> RespuestaTurno:
    """Lista determinista del catálogo de conocimiento (cita el índice FA-000)."""
    temas = listar_temas()
    b2c = [t["titulo"] for t in temas if t["publico"] in ("b2c", "ambos", "")]
    lineas = "\n".join(f"• {t}" for t in b2c[:9])
    texto = (
        "Estos son los temas que puedo explicarte con material aprobado de "
        "Futuro Academy:\n\n"
        f"{lineas}\n\n"
        "Pídeme cualquiera por su nombre o con tus propias palabras — por "
        "ejemplo «háblame del riesgo» o «cómo funciona el interés compuesto». "
        "¿Por cuál empezamos?"
    )
    return _respuesta(
        texto,
        fuentes=[{"cita_visible": "Futuro Academy - Índice y objetivo §0"}],
        estado_flujo="educacion",
        accion="proponer_quiz",
    )


def _turno_tutor(mensaje: str, historial: list[dict]) -> RespuestaTurno:
    # Catálogo de temas: respuesta directa, nunca negativa honesta.
    if _pregunta_por_temas(mensaje):
        return _turno_temas()

    docs = buscar_conocimiento(mensaje, top_k=3)

    # G2 · Negativa honesta: sin respaldo en el corpus, no se inventa nada.
    if not docs:
        return _respuesta(
            respuesta_g2(), estado_flujo="educacion", guardrail="G2",
            disparos=[nuevo_disparo("G2", "El RAG no encontró documentos aprobados.", mensaje)],
        )

    texto = ""
    uso_llm = False
    if _hay_llm():
        try:
            from tools.responder_tutor import responder_tutor
            resultado = responder_tutor(mensaje, historial)
            if resultado.get("documentos_usados", 0) == 0:
                return _respuesta(
                    respuesta_g2(), estado_flujo="educacion", guardrail="G2",
                    disparos=[nuevo_disparo("G2", "El tutor no usó documentos aprobados.", mensaje)],
                )
            texto = (resultado.get("respuesta") or "").strip()
            uso_llm = True
        except Exception:
            texto = ""

    # Degradación sin LLM: respuesta fundamentada en el corpus, textual.
    if not texto:
        doc = docs[0]
        extracto = doc["contenido"].strip()
        if len(extracto) > 480:
            extracto = extracto[:480].rsplit(" ", 1)[0] + "…"
        texto = (
            f"Según el material aprobado de Futuro Academy ({doc['cita_visible']}):\n\n"
            f"{extracto}\n\n¿Quieres que profundice en algún punto?"
        )
        uso_llm = False

    texto, disparos = evaluar_salida_agente(texto, origen_llm=uso_llm)

    return _respuesta(
        texto, fuentes=_fuentes_desde_docs(docs), estado_flujo="educacion",
        accion="proponer_quiz", disparos=disparos,
    )


# ── Rama PROSPECTO (identificación + calificación por config/) ───────────────

_SENALES_CALIFICACION = (
    "objetivo", "monto_declarado_usd", "horizonte", "experiencia_inversion",
    "num_colaboradores", "presupuesto_capacitacion_usd",
)


def _acompanar(
    contexto: str,               # "quiz" | "email" | "post_email"
    nombre: Optional[str],
    historial: list[dict],
    mensaje: str,
) -> tuple[str, bool]:
    """El prospecto sigue escribiendo con el embudo ya cerrado en ese punto.
    Devuelve (texto, uso_llm). Variantes fijas primero; el LLM solo después,
    y siempre saneado (G-QUIZ, G1-bis, G7)."""
    n = f", {nombre}" if nombre else ""
    fijas = {
        "quiz": (
            f"Sin problema{n}. El quiz de perfil está aquí abajo cuando quieras "
            "— son 3 preguntas. ¿O prefieres que te explique algún concepto?",
            "Cuando gustes retomamos el quiz. Mientras tanto pregúntame lo que "
            "quieras: ETFs, diversificación, interés compuesto…",
        ),
        "email": (
            f"Sin apuro{n}: cuando quieras me dejas tu correo y te envío tu "
            "resultado. Mientras tanto, ¿te explico algún concepto?",
            "Aquí sigo. Pregúntame lo que quieras del material aprobado.",
        ),
        "post_email": (
            _post_email(nombre),
            f"Aquí sigo{n}. Pregúntame lo que quieras del material — o si ya "
            "está todo, ¡que tengas un excelente día!",
        ),
    }[contexto]

    if _veces_dicho(fijas[0][:40], historial) == 0:
        return fijas[0], False
    if _veces_dicho(fijas[1][:40], historial) == 0:
        return fijas[1], False

    # Variantes agotadas → LLM con frenos (o la segunda fija otra vez).
    if _hay_llm():
        try:
            from tools.conversar_prospecto import conversar_prospecto
            r = conversar_prospecto(historial + [{"rol": "usuario", "texto": mensaje}])
            if (r.mensaje_agente or "").strip():
                return r.mensaje_agente.strip(), True
        except Exception:
            pass
    return fijas[1], False


def _turno_prospecto(
    mensaje: str,
    historial: list[dict],
    quiz_perfil: Optional[str],
    nombre: Optional[str],
    email_capturado: bool,
) -> RespuestaTurno:
    ultima = _ultima_agente(historial)
    txt_nombre = _txt_pregunta_nombre()
    nombre_detectado: Optional[str] = None

    # ── 0 · Despedida y meta-preguntas (antes que cualquier otra etapa) ──────
    if es_despedida(mensaje):
        return _respuesta(
            _despedida(nombre, email_capturado), estado_flujo="cierre",
        )

    if _pregunta_por_nombre_propio(mensaje):
        return _respuesta(
            "Tu nombre no es obligatorio — me ayuda a darte una atención más "
            "cercana, nada más. Y tu correo solo lo uso si quieres recibir tu "
            "resultado. ¿Seguimos?",
        )

    if _rechaza_email(mensaje):
        return _respuesta(
            "Sin problema — el correo no es obligatorio y no te lo volveré a "
            "pedir. Podemos seguir aprendiendo aquí en el chat con total "
            "normalidad. ¿Qué tema te interesa?",
            estado_flujo="educacion",
        )

    # ── 1 · Identificación 1: el NOMBRE (mensaje 2 · Biblia §2.3) ────────────
    nombre_preguntado = _veces_dicho(txt_nombre, historial) > 0

    if not nombre and txt_nombre in ultima:
        # Están respondiendo a "¿cómo te llamas?"
        n, rechazo = parse_nombre(mensaje)
        if n:
            nombre = nombre_detectado = n
            senales = senales_desde_historial(
                historial + [{"rol": "usuario", "texto": mensaje}], quiz_perfil
            )
            pendiente = siguiente_pregunta(senales["segmento"], senales)
            cuerpo = pendiente["texto"] if pendiente else _oferta_quiz(n)
            return _respuesta(
                f"¡Un gusto, {n}! {cuerpo}",
                estado_flujo="calificacion",
                accion=None if pendiente else "proponer_quiz",
                nombre_detectado=nombre_detectado,
            )
        if rechazo:
            senales = senales_desde_historial(historial, quiz_perfil)
            pendiente = siguiente_pregunta(senales["segmento"], senales)
            cuerpo = pendiente["texto"] if pendiente else _oferta_quiz(None)
            return _respuesta(
                f"Sin problema, seguimos igual. {cuerpo}",
                estado_flujo="calificacion",
                accion=None if pendiente else "proponer_quiz",
            )
        # Respondió con contenido, no con un nombre → se procesa normal abajo.

    if not nombre and not nombre_preguntado:
        # Primer contacto: saludar y pedir el nombre (no obligatorio).
        n_intro = extraer_nombre_intro(mensaje)
        if n_intro:
            nombre = nombre_detectado = n_intro
            return _respuesta(
                f"¡Hola, {n_intro}! Un gusto. Soy el asistente de Futuro Academy: "
                "puedo explicarte temas de finanzas con fuentes verificadas o "
                "ayudarte a dar tus primeros pasos. ¿Qué te gustaría lograr con "
                "tu dinero?",
                estado_flujo="calificacion",
                nombre_detectado=nombre_detectado,
            )
        if es_saludo(mensaje):
            return _respuesta(
                f"¡Hola! Soy el asistente de Futuro Academy. {txt_nombre} "
                "(si prefieres no decirlo, seguimos igual)",
                estado_flujo="identificacion_1",
            )
        # Mensaje con sustancia desde el inicio: reconocerlo y pedir el nombre.
        return _respuesta(
            f"¡Claro que sí, te ayudo con eso! Antes de seguir: {txt_nombre}",
            estado_flujo="identificacion_1",
        )

    # ── 2 · Saludo repetido con nombre ya conocido ────────────────────────────
    if es_saludo(mensaje) and nombre:
        senales = senales_desde_historial(historial, quiz_perfil)
        pendiente = siguiente_pregunta(senales["segmento"], senales)
        cuerpo = pendiente["texto"] if pendiente else "¿En qué te ayudo hoy?"
        return _respuesta(f"¡Hola de nuevo, {nombre}! {cuerpo}")

    # ── 3 · Quiz pedido por texto → se abre el REAL ───────────────────────────
    if not quiz_perfil and _quiere_quiz(mensaje, ultima):
        n = f", {nombre}" if nombre else ""
        return _respuesta(
            f"Perfecto{n} — aquí está el quiz. Son 3 preguntas fijas y el "
            "resultado lo calcula una rúbrica aprobada por cumplimiento:",
            estado_flujo="educacion",
            accion="abrir_quiz",
        )

    # ── 5 · Señales + siguiente pregunta del YAML ─────────────────────────────
    historial_con_msg = historial + [{"rol": "usuario", "texto": mensaje}]
    senales = senales_desde_historial(historial_con_msg, quiz_perfil)
    tipo = senales["segmento"]

    badge: Optional[str] = None
    if tipo == "b2b":
        badge = "B2B"
    elif any(senales.get(s) not in (None, "") for s in _SENALES_CALIFICACION):
        badge = "B2C"

    # Acuse de recibo de lo que ACABA de contestar (plantilla, cero LLM).
    acuse = ""
    catalogo = _catalogo_preguntas()
    senal_previa = next((s for t, s in catalogo if t in ultima), None)
    respuesta_directa_fallida = False
    if senal_previa:
        valor = parsear_respuesta(senal_previa, mensaje)
        if valor is not None:
            # El nombre se usa de vez en cuando (no en cada frase).
            usa_nombre = (
                nombre
                if senal_previa in ("monto_declarado_usd", "presupuesto_capacitacion_usd")
                else None
            )
            acuse = acuse_de_recibo(senal_previa, valor, usa_nombre) + " "
        else:
            cruzados = cross_parse(mensaje, excluir=senal_previa)
            if cruzados:
                s2, v2 = next(iter(cruzados.items()))
                acuse = acuse_de_recibo(s2, v2) + " "
            else:
                respuesta_directa_fallida = True

    # Conteo de veces preguntada (para aclarar UNA vez y nunca entrar en bucle).
    conteos = {t: _veces_dicho(t, historial) for t, _ in catalogo}
    agotadas = {t for t, c in conteos.items() if c >= 2}
    pendiente = siguiente_pregunta(tipo, senales, ya_preguntadas=agotadas)

    if pendiente is not None:
        base = pendiente["texto"]
        veces = conteos.get(base, 0)
        if veces == 0:
            texto = f"{acuse}{base}" if acuse else base
        elif base in ultima and respuesta_directa_fallida:
            # Falló justo esta respuesta → aclarar UNA vez, con cortesía.
            texto = f"Creo que no te entendí bien. {base}"
        elif acuse:
            # La respuesta se guardó en otra señal → re-preguntar con contexto.
            texto = f"{acuse}Y sobre lo anterior: {base}"
        else:
            texto = f"Retomando: {base}"
        texto, disparos = evaluar_salida_agente(texto)
        return _respuesta(
            texto, badge_tipo=badge, estado_flujo="calificacion",
            nombre_detectado=nombre_detectado, disparos=disparos,
        )

    # ── 6 · Calificación completa → siguiente etapa del embudo ───────────────
    if tipo == "b2c" and quiz_perfil is None:
        if _veces_dicho(_MARK_QUIZ_OFERTA, historial) == 0:
            return _respuesta(
                f"{acuse}{_oferta_quiz(nombre)}",
                badge_tipo=badge, estado_flujo="educacion",
                accion="proponer_quiz", nombre_detectado=nombre_detectado,
            )
        texto, uso_llm = _acompanar("quiz", nombre, historial, mensaje)
        texto, disparos = evaluar_salida_agente(texto, origen_llm=uso_llm)
        return _respuesta(
            texto, badge_tipo=badge, estado_flujo="educacion",
            accion="proponer_quiz", disparos=disparos,
        )

    if not email_capturado:
        marca = _MARK_EMAIL_B2B if tipo == "b2b" else _MARK_EMAIL
        if _veces_dicho(marca, historial) == 0:
            return _respuesta(
                f"{acuse}{_pedir_email(tipo, nombre)}",
                badge_tipo=badge, estado_flujo="identificacion_2",
                accion="pedir_email", nombre_detectado=nombre_detectado,
            )
        texto, uso_llm = _acompanar("email", nombre, historial, mensaje)
        texto, disparos = evaluar_salida_agente(texto, origen_llm=uso_llm)
        return _respuesta(
            texto, badge_tipo=badge, estado_flujo="identificacion_2",
            disparos=disparos,
        )

    # Email ya capturado: NUNCA volver a pedirlo. Acompañar y cerrar bien.
    texto, uso_llm = _acompanar("post_email", nombre, historial, mensaje)
    texto, disparos = evaluar_salida_agente(texto, origen_llm=uso_llm)
    return _respuesta(
        texto, badge_tipo=badge, estado_flujo="cierre", disparos=disparos,
    )


# ── Entrada pública ───────────────────────────────────────────────────────────

def procesar_turno(
    historial: list[dict],
    mensaje_usuario: str,
    quiz_perfil: Optional[str] = None,
    nombre: Optional[str] = None,
    email_capturado: bool = False,
) -> RespuestaTurno:
    """Procesa UN turno del chat público y devuelve la respuesta del agente.

    `historial`: mensajes PREVIOS [{"rol", "texto"}].
    `quiz_perfil`: perfil del quiz determinista si ya lo completó (no repetir).
    `nombre`: nombre del prospecto si ya lo dio (para acuses y saludos).
    `email_capturado`: True si ya dejó su correo (no volver a pedirlo).
    """
    mensaje_usuario = (mensaje_usuario or "").strip()
    if not mensaje_usuario:
        return _respuesta(
            "¿Podrías escribir tu pregunta? Estoy aquí para ayudarte.",
            estado_flujo="saludo",
        )

    # 1 · Guardrails de ENTRADA: G5 inyección, G1 no-asesoramiento, G6 alcance.
    respuesta_fija, disparo = evaluar_entrada_usuario(mensaje_usuario)
    if respuesta_fija is not None:
        return _respuesta(
            respuesta_fija, estado_flujo="educacion",
            guardrail=disparo.guardrail if disparo else None,
            disparos=[disparo] if disparo else [],
        )

    # 2 · Quiz pedido por texto (con contexto) — antes que cualquier ruteo.
    if not quiz_perfil and _quiere_quiz(mensaje_usuario, _ultima_agente(historial)):
        n = f", {nombre}" if nombre else ""
        return _respuesta(
            f"Perfecto{n} — aquí está el quiz. Son 3 preguntas fijas y el "
            "resultado lo calcula una rúbrica aprobada por cumplimiento:",
            estado_flujo="educacion",
            accion="abrir_quiz",
        )

    # 2-bis · Intención EXPLÍCITA de quiz (sin depender del contexto del turno
    #   anterior). Fuerza el quiz y evita que RAG intercepte ("test de riesgo").
    if _intencion_quiz_explicita(mensaje_usuario):
        n = f", {nombre}" if nombre else ""
        if quiz_perfil and not email_capturado:
            return _respuesta(
                f"Ese quiz ya lo completaste{n} — tu perfil salió {quiz_perfil}. "
                "¿A qué correo te envío tu resultado y una ruta de 3 pasos?",
                estado_flujo="identificacion", accion="pedir_email",
            )
        if quiz_perfil:
            return _respuesta(
                f"Ya tienes tu perfil ({quiz_perfil}) y tus datos registrados{n}. "
                "¿Te explico algún concepto o hay algo más en lo que te ayude?",
                estado_flujo="educacion",
            )
        return _respuesta(
            f"Perfecto{n} — aquí está el quiz. Son 3 preguntas fijas y el resultado "
            "lo calcula una rúbrica aprobada por cumplimiento:",
            estado_flujo="educacion", accion="abrir_quiz",
        )

    # 2-ter · Intención EXPLÍCITA de registrarse / dar correo → INTERCEPCIÓN
    #   TEMPRANA: se pide el correo YA, aunque queden preguntas de calificación.
    if _intencion_registro(mensaje_usuario) and not email_capturado:
        n = f", {nombre}" if nombre else ""
        seg = senales_desde_historial(
            historial + [{"rol": "usuario", "texto": mensaje_usuario}], quiz_perfil
        ).get("segmento", "b2c")
        return _respuesta(
            f"Con gusto{n}. {_pedir_email(seg, nombre)}",
            estado_flujo="identificacion", accion="pedir_email",
        )

    # 2-quater · Reanudación: ante un mensaje neutral ("ok", "gracias", "sigamos")
    #   tras una interrupción, se retoma el paso del embudo pendiente.
    reanuda = _reanudacion(mensaje_usuario, historial, quiz_perfil, email_capturado)
    if reanuda is not None:
        return reanuda

    # 3 · Una pregunta educativa SIEMPRE se responde (Biblia §7: EDUCACION es
    #     alcanzable desde cualquier estado). Con corpus → tutor con citas;
    #     sin corpus → G2 negativa honesta. Nunca se ignora la pregunta.
    if _es_pregunta_educativa(mensaje_usuario):
        return _turno_tutor(mensaje_usuario, historial)

    # 4 · Flujo comercial (identificación → calificación → embudo).
    return _turno_prospecto(
        mensaje_usuario, historial, quiz_perfil, nombre, email_capturado
    )
