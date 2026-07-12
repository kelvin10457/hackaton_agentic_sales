from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    JSON,
    Enum as SQLEnum,
)

from sqlalchemy.orm import (
    Mapped,
    foreign,
    mapped_column,
    relationship
)

from app.database import Base


# ==========================================
# USER
# ==========================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    # Rol del usuario: 'ejecutivo' habilita acceso a /api/consola/*
    rol: Mapped[str] = mapped_column(String(50), server_default="ejecutivo")

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
        primaryjoin="Lead.id == foreign(Conversation.lead_id)",
        viewonly=True,
    )


# ==========================================
# CONVERSATION
# ==========================================

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Token opaco de sesión: firmado con CHAT_TOKEN_SECRET, atado a esta conversación
    token_sesion: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # El chat comercial usa LeadV2; no se fuerza una FK a la tabla legacy.
    lead_id: Mapped[int] = mapped_column(Integer, index=True)

    lead: Mapped["Lead"] = relationship(
        primaryjoin="foreign(Conversation.lead_id) == Lead.id",
        viewonly=True,
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


# =============================================================================
# MODELOS V2 — Contratos del Manual del R2
# =============================================================================

class LeadV2(Base):
    """[TABLA BD] Lead enriquecido. email_normalizado es la clave de dedup del CRM."""
    __tablename__ = "leads_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Clave de dedup: minúsculas + trim. UNIQUE para garantizar idempotencia.
    email_normalizado: Mapped[str | None] = mapped_column(
        String(200), unique=True, index=True, nullable=True
    )
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cedula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    empresa: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado_identificacion: Mapped[str] = mapped_column(String(50), default="anonimo")
    etapa_embudo: Mapped[str] = mapped_column(String(50), default="nuevo")
    segmento: Mapped[str] = mapped_column(String(10), default="b2c")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    oportunidad: Mapped["Oportunidad | None"] = relationship(
        back_populates="lead_v2", uselist=False, cascade="all, delete-orphan"
    )
    consentimiento: Mapped["Consentimiento | None"] = relationship(
        back_populates="lead_v2", uselist=False, cascade="all, delete-orphan"
    )


class Oportunidad(Base):
    """[TABLA BD] Una oportunidad por lead. Contiene el brief."""
    __tablename__ = "oportunidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads_v2.id"), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(300))
    tipo: Mapped[str] = mapped_column(String(50))
    resumen: Mapped[str] = mapped_column(Text)  # El "brief"
    valor_estimado: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_actual: Mapped[float] = mapped_column(Float, default=0.0)
    propietario: Mapped[str] = mapped_column(String(200), default="carlos@futuroacademy.ec")
    moneda: Mapped[str] = mapped_column(String(10), default="USD")
    probabilidad_cierre: Mapped[float | None] = mapped_column(Float, nullable=True)
    ruta_sugerida: Mapped[str | None] = mapped_column(String(50), nullable=True)
    etapa: Mapped[str] = mapped_column(String(50), default="nuevo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    lead_v2: Mapped["LeadV2"] = relationship(back_populates="oportunidad")


class Consentimiento(Base):
    """[TABLA BD] Dos finalidades independientes. NUNCA un solo bool.
    REGLA #3: tratamiento_datos habilita CRM; comunicaciones habilita aprobar AccionPropuesta.
    """
    __tablename__ = "consentimientos"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads_v2.id"), unique=True, index=True)

    # Finalidad 1: habilita crm_upsert
    tratamiento_datos_otorgado: Mapped[bool] = mapped_column(Boolean, default=False)
    tratamiento_datos_fecha: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tratamiento_datos_canal: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Finalidad 2: habilita aprobar AccionPropuesta
    comunicaciones_otorgado: Mapped[bool] = mapped_column(Boolean, default=False)
    comunicaciones_fecha: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    comunicaciones_canal: Mapped[str | None] = mapped_column(String(50), nullable=True)

    version_politica: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    lead_v2: Mapped["LeadV2"] = relationship(back_populates="consentimiento")

class EventoAuditoria(Base):
    """[TABLA BD] Bitácora append-only.
    REGLA: solo INSERT. Nunca UPDATE ni DELETE.
    No hay updated_at, no hay cascada de escritura, no hay métodos de mutación.
    El timestamp lo pone el servidor al momento del INSERT.
    """
    __tablename__ = "eventos_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(20))         # agente | humano | sistema
    actor_id: Mapped[str] = mapped_column(String(200))     # email o "agente:cv5"
    tipo_evento: Mapped[str] = mapped_column(String(60), index=True)
    lead_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
        # Sin FK para que la bitácora sobreviva borrado de leads
    )
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # timestamp: inmutable, puesto por el servidor al insertar
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class AccionPropuesta(Base):
    """[TABLA BD] Acción comercial propuesta por el agente.
    REGLA: estado puede ser 'obsoleta' si las señales del lead cambiaron
    después de generar la propuesta (implementado en Tarea #8).
    """
    __tablename__ = "acciones_propuestas"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, index=True)  # sin FK para flexibilidad
    tipo: Mapped[str] = mapped_column(String(50))               # TipoAccion
    destinatario: Mapped[dict] = mapped_column(JSON)             # {email, nombre}
    mensaje_sugerido: Mapped[str] = mapped_column(Text)
    snapshot_senales: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    generado_por: Mapped[str] = mapped_column(String(200))      # "agente:cv5" o email
    estado: Mapped[str] = mapped_column(String(50), default="pendiente")
    revisado_por: Mapped[str | None] = mapped_column(String(200), nullable=True)
    motivo_rechazo: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SenalesLead(Base):
    """[TABLA BD] Señales comerciales del lead. Una fila por lead (upsert).
    REGLA CV5: cualquier UPDATE en esta tabla dispara recálculo de score
    y marca como 'obsoleta' toda AccionPropuesta pendiente del lead.
    """
    __tablename__ = "senales_lead"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    # Señales del contrato actual. Los campos de validez los determina el backend
    # a partir de la identidad/email del LeadV2, no el cliente público.
    objetivo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    horizonte: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pidio_asesor: Mapped[bool] = mapped_column(Boolean, default=False)
    mensajes_intercambiados: Mapped[int] = mapped_column(Integer, default=0)
    completo_quiz: Mapped[bool] = mapped_column(Boolean, default=False)
    monto_declarado_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    experiencia_inversion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    perfil_riesgo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    num_colaboradores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    presupuesto_capacitacion_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    es_decisor: Mapped[bool] = mapped_column(Boolean, default=False)
    solicito_propuesta: Mapped[bool] = mapped_column(Boolean, default=False)
    documento_valido: Mapped[bool] = mapped_column(Boolean, default=False)
    ruc_valido: Mapped[bool] = mapped_column(Boolean, default=False)
    email_valido: Mapped[bool] = mapped_column(Boolean, default=False)
    email_corporativo: Mapped[bool] = mapped_column(Boolean, default=False)
    # Legacy columns are retained for existing databases; scoring ignores them.
    presupuesto_declarado: Mapped[float | None] = mapped_column(Float, nullable=True)
    urgencia_declarada: Mapped[str | None] = mapped_column(String(20), nullable=True)
    num_interacciones: Mapped[int] = mapped_column(Integer, default=0)
    nivel_compromiso: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tiene_presupuesto_aprobado: Mapped[bool] = mapped_column(Boolean, default=False)
    tiene_decision_maker: Mapped[bool] = mapped_column(Boolean, default=False)
    plazo_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    competidores_evaluados: Mapped[list | None] = mapped_column(JSON, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class ScoreLead(Base):
    """[TABLA BD] Score calculado por CV5. Una fila por lead (upsert).
    Se recalcula SIEMPRE que cambian las señales del lead.
    """
    __tablename__ = "scores_lead"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    # Las 4 dimensiones de scoring
    dimension_interes: Mapped[float] = mapped_column(Float, default=0.0)
    dimension_capacidad: Mapped[float] = mapped_column(Float, default=0.0)
    dimension_urgencia: Mapped[float] = mapped_column(Float, default=0.0)
    dimension_fit: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    banda: Mapped[str] = mapped_column(String(20), default="frio")
    justificacion: Mapped[str] = mapped_column(Text, default="")
    calculado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class DocumentoCorpus(Base):
    """Documento aprobado disponible para consulta por el agente."""
    __tablename__ = "documento_corpus"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    titulo: Mapped[str] = mapped_column(String)
    seccion: Mapped[str] = mapped_column(String)
    contenido: Mapped[str] = mapped_column(Text)
    publico: Mapped[str] = mapped_column(
        SQLEnum("B2C", "B2B", "ambos", name="publico_corpus")
    )
    version: Mapped[str] = mapped_column(String)
    aprobado_por: Mapped[str] = mapped_column(String)
    cita_visible: Mapped[str] = mapped_column(Text)
