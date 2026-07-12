from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_db, requiere_rol_ejecutivo
from models import Lead, User
from schemas import (
    LeadCreate, LeadRead, LeadUpdate,
    LeadWithConversations, ConversationSummary,
    TimelineMessage, LeadActivity,
)

router = APIRouter(prefix="/leads", tags=["Leads"])


# ── CRUD ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=LeadRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere_rol_ejecutivo)])
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario propietario no existe."
        )
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/", response_model=list[LeadActivity], dependencies=[Depends(requiere_rol_ejecutivo)])
def list_leads(
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    sort: str | None = None,      # "last_activity" para ordenar por actividad reciente
    db: Session = Depends(get_db),
):
    """Lista leads con indicadores de actividad. Soporta ?sort=last_activity."""
    query = db.query(Lead)
    if user_id is not None:
        query = query.filter(Lead.user_id == user_id)
    leads = query.offset(skip).limit(limit).all()

    result: list[LeadActivity] = []
    for lead in leads:
        open_convs = sum(1 for c in lead.conversations if c.ended_at is None)
        last_conv_at = (
            max((c.started_at for c in lead.conversations), default=None)
            if lead.conversations else None
        )
        result.append(
            LeadActivity(
                **LeadRead.model_validate(lead).model_dump(),
                open_conversations=open_convs,
                last_conversation_at=last_conv_at,
            )
        )

    if sort == "last_activity":
        result.sort(
            key=lambda x: x.last_conversation_at or datetime.min,
            reverse=True,
        )

    return result


@router.get("/{lead_id}/full", response_model=LeadWithConversations, dependencies=[Depends(requiere_rol_ejecutivo)])
def get_lead_full(lead_id: int, db: Session = Depends(get_db)):
    """Lead con resumen de todas sus conversaciones (message_count + último mensaje)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado.")

    conv_summaries = []
    for conv in lead.conversations:
        msgs = sorted(conv.messages, key=lambda m: m.created_at)
        conv_summaries.append(
            ConversationSummary(
                id=conv.id,
                started_at=conv.started_at,
                ended_at=conv.ended_at,
                lead_id=conv.lead_id,
                message_count=len(msgs),
                last_message=msgs[-1].content if msgs else None,
            )
        )

    return LeadWithConversations(
        **LeadRead.model_validate(lead).model_dump(),
        conversations=conv_summaries,
    )


@router.get("/{lead_id}/timeline", response_model=list[TimelineMessage], dependencies=[Depends(requiere_rol_ejecutivo)])
def get_lead_timeline(lead_id: int, db: Session = Depends(get_db)):
    """Todos los mensajes del lead ordenados cronológicamente, agrupados por conversación."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado.")

    timeline: list[TimelineMessage] = []
    for conv in lead.conversations:
        for msg in conv.messages:
            timeline.append(
                TimelineMessage(
                    conversation_id=conv.id,
                    message_id=msg.id,
                    sender=msg.sender,
                    content=msg.content,
                    created_at=msg.created_at,
                )
            )

    timeline.sort(key=lambda m: m.created_at)
    return timeline


@router.get("/{lead_id}", response_model=LeadRead, dependencies=[Depends(requiere_rol_ejecutivo)])
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado.")
    return lead


@router.patch("/{lead_id}", response_model=LeadRead, dependencies=[Depends(requiere_rol_ejecutivo)])
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(requiere_rol_ejecutivo)])
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead no encontrado.")
    db.delete(lead)
    db.commit()
