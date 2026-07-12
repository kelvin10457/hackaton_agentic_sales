from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_db
from models import Conversation, Lead
from schemas import (
    ConversationCreate, ConversationRead, ConversationUpdate,
    ConversationWithMessages, LeadSummary, MessageRead,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# ── CRUD ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El lead asociado no existe."
        )
    conversation = Conversation(**payload.model_dump())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/", response_model=list[ConversationRead])
def list_conversations(
    skip: int = 0,
    limit: int = 100,
    lead_id: int | None = None,
    active: bool | None = None,   # True=abiertas (ended_at IS NULL), False=cerradas
    db: Session = Depends(get_db),
):
    """Lista conversaciones. Filtra por ?lead_id=X y/o ?active=true/false."""
    query = db.query(Conversation)
    if lead_id is not None:
        query = query.filter(Conversation.lead_id == lead_id)
    if active is True:
        query = query.filter(Conversation.ended_at == None)
    elif active is False:
        query = query.filter(Conversation.ended_at != None)
    return query.offset(skip).limit(limit).all()


@router.get("/{conversation_id}/messages", response_model=ConversationWithMessages)
def get_conversation_with_messages(conversation_id: int, db: Session = Depends(get_db)):
    """Conversación completa: datos del lead + mensajes en orden cronológico."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada.")

    messages = sorted(conv.messages, key=lambda m: m.created_at)

    return ConversationWithMessages(
        **ConversationRead.model_validate(conv).model_dump(),
        lead=LeadSummary.model_validate(conv.lead),
        messages=[MessageRead.model_validate(m) for m in messages],
    )


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada.")
    return conv


@router.patch("/{conversation_id}", response_model=ConversationRead)
def update_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(conv, field, value)
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada.")
    db.delete(conv)
    db.commit()
