from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


# ==========================================
# USER SCHEMAS
# ==========================================

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime


# ==========================================
# LEAD SCHEMAS
# ==========================================

class LeadCreate(BaseModel):
    name: str
    email: str
    phone: str
    lead_type: str
    company: str
    interest: str
    budget: float
    urgency: str
    lead_score: float
    status: str
    user_id: int


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    lead_type: str | None = None
    company: str | None = None
    interest: str | None = None
    budget: float | None = None
    urgency: str | None = None
    lead_score: float | None = None
    status: str | None = None


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    lead_type: str
    company: str
    interest: str
    budget: float
    urgency: str
    lead_score: float
    status: str
    user_id: int


# ==========================================
# CONVERSATION SCHEMAS
# ==========================================

class ConversationCreate(BaseModel):
    lead_id: int
    ended_at: datetime | None = None


class ConversationUpdate(BaseModel):
    ended_at: datetime | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    ended_at: datetime | None
    lead_id: int


# ==========================================
# MESSAGE SCHEMAS
# ==========================================

class MessageCreate(BaseModel):
    sender: str
    content: str
    conversation_id: int


class MessageUpdate(BaseModel):
    sender: str | None = None
    content: str | None = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender: str
    content: str
    created_at: datetime
    conversation_id: int


# ==========================================
# SCHEMAS ENRIQUECIDOS (joins / agregados)
# ==========================================

class ConversationSummary(BaseModel):
    """Conversación con conteo de mensajes y último mensaje."""
    id: int
    started_at: datetime
    ended_at: datetime | None
    lead_id: int
    message_count: int
    last_message: str | None


class LeadWithConversations(LeadRead):
    """Lead completo con resumen de sus conversaciones."""
    conversations: list[ConversationSummary]


class LeadSummary(BaseModel):
    """Resumen ligero de un lead para incrustar en otros recursos."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    company: str
    status: str
    lead_score: float


class ConversationWithMessages(ConversationRead):
    """Conversación completa con lead y mensajes anidados."""
    lead: LeadSummary
    messages: list[MessageRead]


class TimelineMessage(BaseModel):
    """Mensaje en la línea de tiempo cronológica de un lead."""
    conversation_id: int
    message_id: int
    sender: str
    content: str
    created_at: datetime


class LeadActivity(LeadRead):
    """Lead con indicadores de actividad reciente."""
    open_conversations: int
    last_conversation_at: datetime | None


class UserStats(BaseModel):
    """Estadísticas de dashboard para un usuario."""
    total_leads: int
    leads_by_status: dict[str, int]
    active_conversations: int
    total_messages_sent: int
    avg_messages_per_lead: float
