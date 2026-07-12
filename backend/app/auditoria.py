"""
auditoria.py — Helper de bitácora append-only.

REGLA DE NEGOCIO #5:
  - EventoAuditoria es append-only: solo INSERT, nunca UPDATE ni DELETE.
  - Esta función es la ÚNICA puerta de entrada a la tabla eventos_auditoria.
  - No existe ninguna función update_evento() ni delete_evento() en este módulo.
  - Las rutas PATCH y DELETE para esta tabla no existen en ningún router.

Uso:
    from auditoria import registrar_evento
    registrar_evento(db, actor="humano", actor_id=user.email,
                     tipo_evento="lead_creado", lead_id=lead.id)
"""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from models import EventoAuditoria as EventoAuditoriaModel


def registrar_evento(
    db: Session,
    actor: str,              # "agente" | "humano" | "sistema"
    actor_id: str,           # email del usuario, "agente:cv5", "sistema"
    tipo_evento: str,        # valor de TipoEvento enum
    lead_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> EventoAuditoriaModel:
    """Inserta un evento en la bitácora. APPEND-ONLY: nunca modifica registros existentes.

    Args:
        db: Sesión de SQLAlchemy activa.
        actor: Quién genera el evento ('agente', 'humano', 'sistema').
        actor_id: Identificador del actor (email, nombre de agente).
        tipo_evento: Tipo de evento (usar valores de TipoEvento enum).
        lead_id: ID del lead involucrado (opcional).
        payload: Datos adicionales del evento en JSON (opcional).

    Returns:
        El EventoAuditoria recién creado (con id y timestamp asignados por el servidor).
    """
    evento = EventoAuditoriaModel(
        actor=actor,
        actor_id=actor_id,
        tipo_evento=tipo_evento,
        lead_id=lead_id,
        payload=payload,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


# ── Atajos tipados (evitan strings sueltos en el código) ─────────────────────

def evento_lead_creado(db: Session, actor_id: str, lead_id: int, extra: dict | None = None):
    return registrar_evento(db, "humano", actor_id, "lead_creado", lead_id, extra)


def evento_crm_upsert(db: Session, actor_id: str, lead_id: int, contacto_id: str, accion: str):
    return registrar_evento(db, "humano", actor_id, "crm_upsert", lead_id,
                            {"contacto_id": contacto_id, "accion": accion})


def evento_accion_aprobada(db: Session, actor_id: str, lead_id: int, accion_id: int):
    return registrar_evento(db, "humano", actor_id, "accion_aprobada", lead_id,
                            {"accion_id": accion_id})


def evento_accion_rechazada(db: Session, actor_id: str, lead_id: int, accion_id: int):
    return registrar_evento(db, "humano", actor_id, "accion_rechazada", lead_id,
                            {"accion_id": accion_id})


def evento_score_calculado(db: Session, lead_id: int, total: float, banda: str):
    return registrar_evento(db, "sistema", "sistema", "score_calculado", lead_id,
                            {"total": total, "banda": banda})


def evento_consentimiento_otorgado(db: Session, lead_id: int, finalidad: str, canal: str):
    return registrar_evento(db, "sistema", "sistema", "consentimiento_otorgado", lead_id,
                            {"finalidad": finalidad, "canal": canal})
