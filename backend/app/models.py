from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from database import Base


# ==========================================
# USER
# ==========================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    password: Mapped[str] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    leads: Mapped[list["Lead"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


# ==========================================
# LEAD
# ==========================================

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(30))

    lead_type: Mapped[str] = mapped_column(String(50))
    company: Mapped[str] = mapped_column(String(100))
    interest: Mapped[str] = mapped_column(String(100))

    budget: Mapped[float] = mapped_column(Float)

    urgency: Mapped[str] = mapped_column(String(50))
    lead_score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50))

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    user: Mapped["User"] = relationship(
        back_populates="leads"
    )

    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan"
    )


# ==========================================
# CONVERSATION
# ==========================================

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    lead_id: Mapped[int] = mapped_column(
        ForeignKey("leads.id")
    )

    lead: Mapped["Lead"] = relationship(
        back_populates="conversations"
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


# ==========================================
# MESSAGE
# ==========================================

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    sender: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id")
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages"
    )