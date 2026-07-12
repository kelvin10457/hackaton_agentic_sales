"""
Router de la superficie pública de chat: /api/chat/*

Auth: token opaco de sesión (firmado con CHAT_TOKEN_SECRET) atado a UNA sola
conversacion_id. Llega en `Authorization: Bearer <token>` (frontend web) o en
`X-Session-Token` (contrato interno / tests). En ambos casos es el MISMO token.

REGLAS DE SEGREGACIÓN (impuestas, no solo documentadas):
  - conversacion_id viene del token, NUNCA de la URL.
  - Solo devuelve datos de esa conversación.
  - Nunca expone: score, brief, bitácora, otros leads, listados.
  - No existe endpoint público que acepte un lead_id arbitrario.

INTEGRACIÓN R1 ↔ R2 (lo que faltaba):
  - POST /api/chat/mensaje despierta al núcleo agéntico (core/servicio_agente),
    que reutiliza las tools de R1 (RAG + LLM) y aplica los guardrails.
  - Cada guardrail que se dispara se persiste en la bitácora (G8).
  - El agente PROPONE; nunca ejecuta un envío (no existe enviar_correo).
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_db, requiere_token_sesion, create_session_token
from app.auditoria import registrar_evento
from app.crm import get_crm
from app.models import Conversation, Message
from app.schemas import (
    ConsentimientoEntrada,
    ConsentimientoResultado,
    ConversacionRecuperada,
    EstadoIdentificacion,
    EstadoQuiz,
    FuenteCita,
    IniciarConversacionResponse,
    LeadV2Read,
    MensajeEntrada,
    MensajeHistorial,
    MessageRead,
    PreguntaQuizPublica,
    QuizPublico,
    RespuestaAgente,
    RespuestasQuizEntrada,
    ResultadoQuiz,
)

# Núcleo agéntico (R1). El borde HTTP (app/) puede importar core/; nunca al revés.
from core.servicio_agente import procesar_turno
from tools.obtener_quiz import obtener_preguntas_quiz, calcular_perfil_riesgo

router = APIRouter(prefix="/api/chat", tags=["Chat (pública)"])

# Convenciones de sender en la tabla messages.
_SENDER_USUARIO = "lead"
_SENDER_AGENTE = "agent"
_SENDER_SISTEMA = "system"   # metadatos (badge/perfil); no se pintan en el chat

# Marcadores de estado guardados como mensajes de sistema (continuidad sin tabla extra).
_MARCA_BADGE = "[badge]"
_MARCA_PERFIL = "[quiz_perfil]"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cargar_conversacion(db: Session, conv_id: int) -> Conversation:
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversación no encontrada.")
    return conv


def _mensajes_ordenados(conv: Conversation) -> list[Message]:
    return sorted(conv.messages, key=lambda m: (m.created_at, m.id))


def _historial_para_agente(mensajes: list[Message]) -> list[dict]:
    """Convierte los mensajes de BD al formato del núcleo, omitiendo metadatos."""
    historial = []
    for m in mensajes:
        if m.sender == _SENDER_SISTEMA:
            continue
        rol = "usuario" if m.sender == _SENDER_USUARIO else "agente"
        historial.append({"rol": rol, "texto": m.content})
    return historial


def _leer_estado_sistema(mensajes: list[Message]) -> tuple[str | None, str | None]:
    """Recupera (badge, perfil_quiz) desde los mensajes de sistema."""
    badge = None
    perfil = None
    for m in mensajes:
        if m.sender != _SENDER_SISTEMA:
            continue
        if m.content.startswith(_MARCA_BADGE):
            badge = m.content[len(_MARCA_BADGE):].strip() or None
        elif m.content.startswith(_MARCA_PERFIL):
            perfil = m.content[len(_MARCA_PERFIL):].strip() or None
    return badge, perfil


# ──────────────────────────────────────────────────────────────────────────────
# POST /iniciar — crea una conversación anónima y devuelve su token de sesión
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/iniciar",
    response_model=IniciarConversacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar una conversación pública (anónima, sin login)",
)
def iniciar_conversacion(db: Session = Depends(get_db)):
    """Crea la conversación con lead_id=0 (anónimo: aún no entra al CRM) y firma
    un token de sesión atado a su id. El token permite recuperar la conversación
    tras cerrar y reabrir el navegador (criterio de continuidad).
    """
    conv = Conversation(lead_id=0)  # 0 = anónimo; el lead se crea con consentimiento
    db.add(conv)
    db.flush()
    conv.token_sesion = create_session_token(conv.id)
    db.commit()
    db.refresh(conv)
    return IniciarConversacionResponse(
        token_sesion=conv.token_sesion,
        conversacion_id=str(conv.id),
    )


# ──────────────────────────────────────────────────────────────────────────────
# GET /conversacion — historial de ESTA conversación (superset chat + segregación)
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/conversacion",
    response_model=ConversacionRecuperada,
    summary="Recuperar la conversación activa (determinada por el token)",
    responses={
        401: {"description": "Token ausente, inválido o expirado."},
        404: {"description": "Conversación no encontrada."},
    },
)
def obtener_conversacion(
    conversacion_id: int = Depends(requiere_token_sesion),
    db: Session = Depends(get_db),
):
    conv = _cargar_conversacion(db, conversacion_id)
    mensajes = _mensajes_ordenados(conv)
    badge, perfil = _leer_estado_sistema(mensajes)

    historial = [
        MensajeHistorial(
            id=str(m.id),
            rol=("usuario" if m.sender == _SENDER_USUARIO else "agente"),
            texto=m.content,
            ts=m.created_at,
        )
        for m in mensajes
        if m.sender != _SENDER_SISTEMA
    ]

    return ConversacionRecuperada(
        id=conv.id,
        lead_id=conv.lead_id,
        estado_flujo="saludo",
        badge_tipo=badge if badge in ("B2C", "B2B") else None,
        preguntas_respondidas=[],
        quiz=EstadoQuiz(iniciado=perfil is not None, perfil_resultante=perfil),
        historial=historial,
        # `messages` mantiene el contrato de segregación (test_superficies).
        messages=[
            MessageRead.model_validate(m)
            for m in mensajes
            if m.sender != _SENDER_SISTEMA
        ],
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /mensaje — despierta al agente y devuelve su respuesta
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/mensaje",
    response_model=RespuestaAgente,
    summary="Enviar un mensaje: el núcleo agéntico responde",
    responses={401: {"description": "Token ausente, inválido o expirado."}},
)
def enviar_mensaje(
    body: MensajeEntrada,
    conversacion_id: int = Depends(requiere_token_sesion),
    db: Session = Depends(get_db),
):
    conv = _cargar_conversacion(db, conversacion_id)
    texto_usuario = (body.mensaje or "").strip()
    if not texto_usuario:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El mensaje está vacío.")

    historial = _historial_para_agente(_mensajes_ordenados(conv))

    # 1) Persistir el mensaje del usuario.
    db.add(Message(sender=_SENDER_USUARIO, content=texto_usuario, conversation_id=conv.id))
    db.flush()

    # 2) Despertar al núcleo agéntico (R1): un turno del chat.
    resultado = procesar_turno(historial, texto_usuario)

    # 3) Persistir la respuesta del agente.
    db.add(Message(sender=_SENDER_AGENTE, content=resultado["mensaje"], conversation_id=conv.id))

    # 4) Guardar badge de clasificación la primera vez (continuidad).
    badge = resultado.get("badge_tipo")
    if badge in ("B2C", "B2B"):
        ya_tiene = any(
            m.sender == _SENDER_SISTEMA and m.content.startswith(_MARCA_BADGE)
            for m in conv.messages
        )
        if not ya_tiene:
            db.add(Message(
                sender=_SENDER_SISTEMA,
                content=f"{_MARCA_BADGE}{badge}",
                conversation_id=conv.id,
            ))

    db.commit()

    # 5) G8 — cada guardrail disparado se registra en la bitácora (append-only).
    lead_id = conv.lead_id or None
    for disparo in resultado.get("disparos", []) or []:
        try:
            registrar_evento(
                db,
                actor="agente",
                actor_id="agente:cv5",
                tipo_evento="error" if disparo.guardrail in ("G2",) else "score_calculado",
                lead_id=lead_id,
                payload={"tipo": "guardrail", **disparo.a_payload()},
            )
        except Exception:
            pass  # la auditoría nunca debe tumbar la respuesta al usuario

    return RespuestaAgente(
        mensaje=resultado["mensaje"],
        fuentes=[FuenteCita(cita_visible=f["cita_visible"]) for f in resultado.get("fuentes", [])],
        estado_flujo=resultado.get("estado_flujo", "educacion"),
        badge_tipo=badge if badge in ("B2C", "B2B") else None,
        guardrail=resultado.get("guardrail"),
        accion=resultado.get("accion"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /quiz — las 3 preguntas FIJAS del perfil de riesgo (sin puntajes)
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/quiz",
    response_model=QuizPublico,
    summary="Obtener el quiz de perfil de riesgo (determinista, sin LLM)",
)
def obtener_quiz():
    """Regla de oro #3: el quiz NO lo genera la IA. Preguntas fijas del YAML.
    Se omiten los puntajes de cada opción para no filtrar la rúbrica al cliente.
    """
    preguntas = obtener_preguntas_quiz()
    return QuizPublico(
        preguntas=[
            PreguntaQuizPublica(
                id=p["id"],
                texto=p["texto"],
                opciones=[op["texto"] for op in p["opciones"]],
            )
            for p in preguntas
        ]
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /quiz/respuestas — el PERFIL lo calcula CÓDIGO (rúbrica fija)
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/quiz/respuestas",
    response_model=ResultadoQuiz,
    summary="Calcular el perfil de riesgo con la rúbrica determinista",
    responses={401: {"description": "Token ausente, inválido o expirado."}},
)
def responder_quiz(
    body: RespuestasQuizEntrada,
    conversacion_id: int = Depends(requiere_token_sesion),
    db: Session = Depends(get_db),
):
    try:
        perfil = calcular_perfil_riesgo(body.respuestas)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    conv = _cargar_conversacion(db, conversacion_id)
    # Guardar el perfil como metadato (continuidad: no re-ofrecer el quiz al volver).
    db.add(Message(
        sender=_SENDER_SISTEMA,
        content=f"{_MARCA_PERFIL}{perfil}",
        conversation_id=conv.id,
    ))
    db.commit()

    return ResultadoQuiz(
        perfil=perfil,
        mensaje=(
            f"Tu perfil salió {perfil}. ¿A qué correo te envío tu resultado y una "
            "ruta de aprendizaje de 3 pasos?"
        ),
    )


# ──────────────────────────────────────────────────────────────────────────────
# POST /consentimiento — dos finalidades independientes (LOPDP)
# ──────────────────────────────────────────────────────────────────────────────

def _nombre_desde_email(email: str | None) -> str:
    if not email or "@" not in email:
        return "Prospecto web"
    local = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    return local.title() or "Prospecto web"


@router.post(
    "/consentimiento",
    response_model=ConsentimientoResultado,
    summary="Registrar el consentimiento por finalidad (y, si aplica, entrar al CRM)",
    responses={401: {"description": "Token ausente, inválido o expirado."}},
)
def registrar_consentimiento(
    body: ConsentimientoEntrada,
    conversacion_id: int = Depends(requiere_token_sesion),
    db: Session = Depends(get_db),
):
    """Consentimiento por finalidad:
      - tratamiento_datos: habilita crear/actualizar el lead en el CRM (idempotente).
      - comunicaciones_comerciales: habilita que Carlos APRUEBE comunicaciones.
    Rechazar ambas NO degrada el servicio: el tutor sigue disponible.
    REGLA #1: sin tratamiento de datos (o sin email) el lead nunca entra al CRM.
    """
    conv = _cargar_conversacion(db, conversacion_id)

    # Sin consentimiento de datos: no se escribe nada en el CRM. Servicio intacto.
    if not body.tratamiento_datos or not body.email:
        return ConsentimientoResultado(
            mensaje=(
                "Sin problema — no registraré tus datos. Podemos seguir aprendiendo "
                "aquí en el chat con total normalidad."
            )
        )

    # Con consentimiento + email: el lead se identifica y entra al CRM (crea o actualiza).
    try:
        lead_in = LeadV2Read(
            id=0,  # el id real lo asigna el CRM; upsert_contacto no lo usa
            nombre=_nombre_desde_email(body.email),
            email=body.email,
            email_normalizado=body.email.strip().lower(),  # clave de dedup del CRM
            estado_identificacion=EstadoIdentificacion.IDENTIFICADO,
            created_at=_now(),
        )
        crm = get_crm(db)
        contacto_id = crm.upsert_contacto(lead_in)   # idempotente por email_normalizado
        crm.upsert_oportunidad(lead_in, contacto_id)
        lead_db_id = int(contacto_id)

        # Vincular la conversación anónima al lead ya identificado.
        conv.lead_id = lead_db_id

        # Registrar los consentimientos por finalidad en la bitácora (append-only).
        registrar_evento(
            db, actor="sistema", actor_id="sistema",
            tipo_evento="consentimiento_otorgado", lead_id=lead_db_id,
            payload={"finalidad": "tratamiento_datos", "canal": "web"},
        )
        if body.comunicaciones_comerciales:
            registrar_evento(
                db, actor="sistema", actor_id="sistema",
                tipo_evento="consentimiento_otorgado", lead_id=lead_db_id,
                payload={"finalidad": "comunicaciones_comerciales", "canal": "web"},
            )
        registrar_evento(
            db, actor="sistema", actor_id="agente:cv5",
            tipo_evento="crm_upsert", lead_id=lead_db_id,
            payload={"contacto_id": contacto_id, "accion": "upsert_desde_chat"},
        )
        db.commit()
    except Exception:
        db.rollback()
        # No rompemos la UX del prospecto por un fallo de CRM/BD.
        return ConsentimientoResultado(
            mensaje=(
                f"¡Gracias! Registré tu interés con {body.email}. En breve recibirás "
                "tu resultado y la ruta de aprendizaje."
            )
        )

    if body.comunicaciones_comerciales:
        mensaje = (
            f"¡Listo! Te envié tu resultado y la ruta de aprendizaje a {body.email}. "
            "Un asesor podrá contactarte, y cualquier comunicación la aprueba primero "
            "un humano — así trabajamos."
        )
    else:
        mensaje = (
            f"¡Listo! Te envié tu resultado y la ruta de aprendizaje a {body.email}. "
            "No recibirás comunicaciones comerciales: solo el material que pediste."
        )
    return ConsentimientoResultado(mensaje=mensaje)
