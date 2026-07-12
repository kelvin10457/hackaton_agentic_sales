"""
Router de la superficie pública de chat: /api/chat/*
Auth: token opaco (X-Session-Token) firmado con CHAT_TOKEN_SECRET,
atado a UNA sola conversacion_id.

REGLAS DE SEGREGACIÓN (implementadas, no solo documentadas):
  - conversacion_id viene del token, NUNCA de la URL.
  - Solo devuelve datos de esa conversación.
  - Nunca expone: score, brief, bitácora, otros leads, listados.
  - Si alguien envía un token de otro lead → 404 (no hay endpoint que lo acepte).
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_db, requiere_token_sesion
from app.models import Conversation, Message
from app.schemas import ConversacionV2Read, MessageRead

router = APIRouter(prefix="/api/chat", tags=["Chat (pública)"])
_TS = lambda: datetime.now(timezone.utc)


# ──────────────────────────────────────────────────────────────────────────────
# Contrato #8 — Conversacion  (solo los datos de ESTA conversación)
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/conversacion",
    response_model=ConversacionV2Read,
    summary="Datos de la conversación activa (determinada por el token)",
    responses={
        401: {"description": "X-Session-Token ausente, inválido o expirado."},
        404: {"description": "Conversación no encontrada."},
    },
)
def obtener_conversacion(
    conversacion_id: int = Depends(requiere_token_sesion),
    db: Session = Depends(get_db),
):
    """El token determina la conversación y solo expone su historial."""
    conv = db.query(Conversation).filter(Conversation.id == conversacion_id).first()
    if not conv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversación no encontrada.")
    return ConversacionV2Read(
        id=conv.id,
        lead_id=conv.lead_id,
        token_sesion="[redacted]",   # nunca devolver el token al cliente
        canal="web",
        agente_id="agente:cv5",
        iniciada_en=conv.started_at,
        cerrada_en=conv.ended_at,
        messages=[MessageRead.model_validate(m) for m in sorted(conv.messages, key=lambda m: m.created_at)],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Mensajes — solo de esta conversación, sin exponer otros leads
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/mensajes",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar mensaje en la conversación activa",
    responses={
        401: {"description": "X-Session-Token ausente, inválido o expirado."},
    },
)
def enviar_mensaje(
    contenido: str,
    conversacion_id: int = Depends(requiere_token_sesion),
    db: Session = Depends(get_db),
):
    """El ID proviene exclusivamente del token de sesión firmado."""
    conv = db.query(Conversation).filter(Conversation.id == conversacion_id).first()
    if not conv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversación no encontrada.")
    mensaje = Message(sender="lead", content=contenido, conversation_id=conv.id)
    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)
    return MessageRead(
        id=mensaje.id,
        sender="lead",
        content=mensaje.content,
        created_at=mensaje.created_at,
        conversation_id=mensaje.conversation_id,
    )
