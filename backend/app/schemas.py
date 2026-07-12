"""
schemas.py — Fuente de verdad de contratos Pydantic para toda la API.
Los contratos #1-13 del "Manual del R2" viven en la sección V2 de este archivo.
FastAPI los expone automáticamente en /openapi.json cuando se usan como
response_model o request body en algún endpoint (ver routers/consola.py y chat.py).

Nota sobre SQLModel: el proyecto usa SQLAlchemy puro + Pydantic v2 por separado.
No se migró a SQLModel para no romper los modelos existentes.
Qué va a la BD: Lead, Oportunidad, Consentimiento, AccionPropuesta,
               EventoAuditoria, ConversacionV2, DocumentoCorpus.
Solo validación: Senales (JSONB en Lead), Score (calculado), Otorgamiento
               (embebido en Consentimiento).
"""

from datetime import datetime, date, timezone
from enum import Enum
from typing import Literal, Any
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_serializer, field_validator


# ==========================================
# USER SCHEMAS  (sin cambios)
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
# LEAD SCHEMAS  (sin cambios — CRUD original)
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
# CONVERSATION SCHEMAS  (sin cambios)
# ==========================================

class ConversationCreate(BaseModel):
    lead_id: int
    ended_at: datetime | None = None

    @field_validator("ended_at")
    @classmethod
    def normalizar_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None
                else value.astimezone(timezone.utc))


class ConversationUpdate(BaseModel):
    ended_at: datetime | None = None

    @field_validator("ended_at")
    @classmethod
    def normalizar_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None
                else value.astimezone(timezone.utc))


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    ended_at: datetime | None
    lead_id: int

    @field_serializer("started_at", "ended_at", when_used="json")
    def serializar_utc(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# ==========================================
# MESSAGE SCHEMAS  (sin cambios)
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
# SCHEMAS ENRIQUECIDOS  (sin cambios)
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


# =============================================================================
# ── CONTRATOS V2 — "Manual del R2" ───────────────────────────────────────────
# Estos son la fuente de verdad. El frontend genera tipos TypeScript desde
# /openapi.json con `npx openapi-typescript`. NO escribas tipos a mano.
# =============================================================================


# ──────────────────────────────────────────────────────────────────────────────
# ENUMS  (#10 EtapaEmbudo · #11 Banda · #12 TipoAccion · #13 RutaSugerida)
# ──────────────────────────────────────────────────────────────────────────────

class EtapaEmbudo(str, Enum):
    """Etapas cerradas de la Biblia, compartidas por Lead y Oportunidad."""
    NUEVO = "nuevo"
    EN_CALIFICACION = "en_calificacion"
    CALIFICADO = "calificado"
    EDUCANDO = "educando"
    LISTO_PARA_ASESOR = "listo_para_asesor"
    DERIVADO = "derivado"
    NUTRICION = "nutricion"
    DESCARTADO = "descartado"


class Banda(str, Enum):
    """Temperatura del lead según score total.
    Rangos: frio 0-39 · tibio 40-69 · caliente 70-89 · critico 90-100
    """
    FRIO     = "frio"      # Score 0–39
    TIBIO    = "tibio"     # Score 40–69
    CALIENTE = "caliente"  # Score 70–89
    CRITICO  = "critico"   # Score 90–100, máxima urgencia


class TipoAccion(str, Enum):
    """Tipo de acción comercial propuesta por el agente."""
    LLAMADA          = "llamada"
    EMAIL            = "email"
    WHATSAPP         = "whatsapp"
    REUNION          = "reunion"
    DEMO             = "demo"
    PROPUESTA_FORMAL = "propuesta_formal"
    DESCUENTO        = "descuento"


class RutaSugerida(str, Enum):
    """Ruta de cierre recomendada según perfil del lead."""
    B2C_DIGITAL    = "b2c_digital"     # Cierre online / autoservicio
    B2C_PRESENCIAL = "b2c_presencial"  # Visita o evento presencial
    B2B_EJECUTIVO  = "b2b_ejecutivo"   # Venta consultiva con ejecutivo
    B2B_LICITACION = "b2b_licitacion"  # Proceso formal de licitación
    NURTURING      = "nurturing"       # Lead no listo; mantener caliente
    REACTIVACION   = "reactivacion"    # Lead perdido/inactivo a recuperar
    VENTAS_CORPORATIVAS = "ventas_corporativas"
    ASESORIA_INVERSION = "asesoria_inversion"
    PROGRAMA_INICIAL = "programa_inicial"
    NUTRICION_EDUCATIVA = "nutricion_educativa"
    AUTOMATICO = "automatico"


# Enums de apoyo (no en la lista de 13, pero requeridos por los contratos)

class EstadoIdentificacion(str, Enum):
    ANONIMO      = "anonimo"       # Sin datos que lo identifiquen
    IDENTIFICADO = "identificado"  # Nombre + email confirmados
    VERIFICADO   = "verificado"    # Cédula/RUC validado por módulo 10


class EstadoAccion(str, Enum):
    PENDIENTE  = "pendiente"   # Generada, esperando revisión humana
    APROBADA   = "aprobada"    # Revisada y autorizada
    RECHAZADA  = "rechazada"   # Revisada y descartada
    EJECUTADA  = "ejecutada"   # Ya enviada al lead
    OBSOLETA   = "obsoleta"    # Señales del lead cambiaron después de crearla


class TipoEvento(str, Enum):
    LEAD_CREADO              = "lead_creado"
    LEAD_ACTUALIZADO         = "lead_actualizado"
    IDENTIDAD_VERIFICADA     = "identidad_verificada"
    CONSENTIMIENTO_OTORGADO  = "consentimiento_otorgado"
    SCORE_CALCULADO          = "score_calculado"
    ACCION_GENERADA          = "accion_generada"
    ACCION_APROBADA          = "accion_aprobada"
    ACCION_RECHAZADA         = "accion_rechazada"
    CRM_UPSERT               = "crm_upsert"
    ERROR                    = "error"


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #1 — Lead  [TABLA BD: tabla leads_v2 (futura) o extensión de leads]
# ──────────────────────────────────────────────────────────────────────────────

class LeadV2Base(BaseModel):
    """Lead enriquecido con estado de identidad, etapa y segmento.
    REGLA: estado_identificacion == 'anonimo' bloquea escritura al CRM.
    """
    nombre: str
    email: str | None = None          # None si es anónimo
    email_normalizado: str | None = None  # minúsculas + trim, clave de dedup
    telefono: str | None = None
    cedula: str | None = None         # Validada con módulo 10 o RUC (Tarea #4)
    empresa: str | None = None
    cargo: str | None = None
    estado_identificacion: EstadoIdentificacion = EstadoIdentificacion.ANONIMO
    etapa_embudo: EtapaEmbudo = EtapaEmbudo.NUEVO
    segmento: Literal["b2c", "b2b"] = "b2c"

    @field_validator("cedula")
    @classmethod
    def cedula_o_ruc_valido(cls, v: str | None) -> str | None:
        """Valida cédula (10 dígitos, módulo 10) o RUC (13 dígitos).
        Si el campo es None, lo acepta sin validar (lead anónimo).
        """
        if v is None:
            return v
        from app.validators import validar_cedula, validar_ruc
        if not (validar_cedula(v) or validar_ruc(v)):
            raise ValueError(
                f"Cédula o RUC inválido: '{v}'. "
                "Debe ser una cédula ecuatoriana de 10 dígitos (módulo 10) "
                "o un RUC de 13 dígitos."
            )
        return v

    @field_validator("email_normalizado", mode="before")
    @classmethod
    def normalizar_email(cls, v: str | None, info) -> str | None:
        """Si email_normalizado no se pasa explícitamente, se deriva del email."""
        if v is not None:
            return v.strip().lower()
        # Intentar derivar desde el campo email si está presente
        email = info.data.get("email") if hasattr(info, "data") else None
        return email.strip().lower() if email else None


class LeadV2Create(LeadV2Base):
    """Payload para crear un lead V2. El email_normalizado se genera automáticamente."""
    pass


class LeadV2Read(LeadV2Base):
    """Lead V2 tal como lo devuelve la API (incluye id y timestamps)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime | None = None


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #2 — Señales  [SOLO VALIDACIÓN — almacenada como JSONB en Lead]
# Todos los campos opcionales: None significa "sin evidencia todavía".
# ──────────────────────────────────────────────────────────────────────────────

class Senales(BaseModel):
    """Señales de compra observadas para un lead.
    Todos los campos son opcionales: None == sin evidencia aún.
    """
    objetivo: str | None = None
    horizonte: Literal["inmediato", "1-3m", "3-6m", "mas_6m"] | None = None
    pidio_asesor: bool | None = None
    mensajes_intercambiados: int | None = None
    completo_quiz: bool | None = None
    monto_declarado_usd: float | None = None
    experiencia_inversion: Literal["ninguna", "basica", "intermedia", "avanzada"] | None = None
    perfil_riesgo: str | None = None
    num_colaboradores: int | None = None
    presupuesto_capacitacion_usd: float | None = None
    es_decisor: bool | None = None
    solicito_propuesta: bool | None = None


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #3 — Score  [SOLO VALIDACIÓN — calculado, no tabla propia]
# 4 dimensiones + total + banda + justificación.
# ──────────────────────────────────────────────────────────────────────────────

class Score(BaseModel):
    """Score multidimensional CV5 del lead.
    Cada dimensión va de 0 a 100. El total es la media ponderada.
    La banda se asigna automáticamente: frio<40, tibio<70, caliente<90, critico>=90.
    """
    lead_id: int
    dimension_interes: float    # Interés declarado + conducta en sesión
    dimension_capacidad: float  # Presupuesto + tamaño empresa + cargo
    dimension_urgencia: float   # Urgencia declarada + señales temporales
    dimension_fit: float        # Alineación producto-segmento
    total: float                # 0–100
    banda: Banda
    justificacion: str          # Texto explicativo para el ejecutivo
    calculado_en: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #4 — Oportunidad  [TABLA BD]
# Una por lead, con resumen (brief) y ruta sugerida.
# ──────────────────────────────────────────────────────────────────────────────

class OportunidadBase(BaseModel):
    lead_id: int
    nombre: str
    tipo: Literal["B2C_programa", "B2C_asesoria", "B2B_corporativo", "B2B_licencia"]
    resumen: str                          # El "brief" para el ejecutivo
    valor_estimado: float | None = None
    score_actual: float
    propietario: str
    moneda: str = "USD"
    probabilidad_cierre: float | None = None  # 0.0–1.0
    fecha_cierre_estimada: date | None = None
    ruta_sugerida: RutaSugerida | None = None
    etapa: EtapaEmbudo = EtapaEmbudo.NUEVO


class OportunidadCreate(OportunidadBase):
    pass


class OportunidadRead(OportunidadBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime | None = None


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #5 — Consentimiento  [TABLA BD]
# DOS finalidades independientes. Nunca un solo booleano.
# ──────────────────────────────────────────────────────────────────────────────

class Otorgamiento(BaseModel):
    """Un consentimiento para UNA finalidad específica.
    Inmutable una vez otorgado (append-only en espíritu).
    """
    otorgado: bool = False
    fecha: datetime | None = None
    ip_origen: str | None = None
    canal: Literal["web", "whatsapp", "email", "presencial"] | None = None
    texto_mostrado: str | None = None   # Hash SHA256 o texto exacto mostrado


class ConsentimientoBase(BaseModel):
    lead_id: int
    # ── REGLA: estas dos finalidades son INDEPENDIENTES ───────────────────────
    tratamiento_datos: Otorgamiento = Field(
        default_factory=Otorgamiento,
        description="Habilita escribir en el CRM (bloquea crm_upsert si False).",
    )
    comunicaciones_comerciales: Otorgamiento = Field(
        default_factory=Otorgamiento,
        description="Habilita aprobar AccionPropuesta (HTTP 403 si False).",
    )
    version_politica: str | None = None


class ConsentimientoRead(ConsentimientoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    updated_at: datetime | None = None


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #6 — AccionPropuesta  [TABLA BD]
# Con destinatario, snapshot_senales, y estado que puede llegar a "obsoleta".
# ──────────────────────────────────────────────────────────────────────────────

class Destinatario(BaseModel):
    email: str
    nombre: str


class AccionPropuestaBase(BaseModel):
    lead_id: int
    tipo: TipoAccion
    destinatario: Destinatario
    mensaje_sugerido: str
    snapshot_senales: Senales           # Copia de señales al momento de generarla
    generado_por: str                   # "agente:<nombre>" o email del ejecutivo


class AccionPropuestaCreate(AccionPropuestaBase):
    pass


class AccionPropuestaRead(AccionPropuestaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    estado: EstadoAccion = EstadoAccion.PENDIENTE
    revisado_por: str | None = None     # Email del ejecutivo que aprobó/rechazó
    motivo_rechazo: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #7 — EventoAuditoria  [TABLA BD — append-only]
# Solo INSERT. Nunca UPDATE ni DELETE.
# No exponer rutas PATCH/DELETE para esta tabla (ver routers/consola.py).
# ──────────────────────────────────────────────────────────────────────────────

class EventoAuditoriaCreate(BaseModel):
    """Payload para registrar un evento. El timestamp lo pone el servidor."""
    actor: Literal["agente", "humano", "sistema"]
    actor_id: str               # Email del usuario, "agente:cv5", "sistema"
    tipo_evento: TipoEvento
    lead_id: int | None = None
    payload: dict[str, Any] | None = None   # Datos adicionales del evento


class EventoAuditoriaRead(EventoAuditoriaCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime         # UTC, puesto por el servidor al insertar


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #8 — Conversacion  [TABLA BD — extiende la tabla conversations]
# Agrega token_sesion: token opaco atado a esta conversación, usado en /api/chat/*.
# ──────────────────────────────────────────────────────────────────────────────

class ConversacionV2Base(BaseModel):
    lead_id: int
    canal: Literal["web", "whatsapp", "email", "presencial"] = "web"
    agente_id: str | None = None        # ID del agente IA asignado


class ConversacionV2Create(ConversacionV2Base):
    pass


class ConversacionV2Read(ConversacionV2Base):
    model_config = ConfigDict(from_attributes=True)
    id: int
    token_sesion: str           # Token opaco firmado con CHAT_TOKEN_SECRET
    iniciada_en: datetime
    cerrada_en: datetime | None = None
    messages: list[MessageRead] = Field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# SUPERFICIE PÚBLICA DE CHAT — contratos de request/response de /api/chat/*
# Consumidos por el frontend (web/lib/api-client.ts). El agente vive en
# core/servicio_agente.py; estos schemas solo describen el borde HTTP.
# ──────────────────────────────────────────────────────────────────────────────

class IniciarConversacionResponse(BaseModel):
    """Respuesta de POST /api/chat/iniciar."""
    token_sesion: str
    conversacion_id: str


class MensajeEntrada(BaseModel):
    """Body de POST /api/chat/mensaje."""
    mensaje: str


class FuenteCita(BaseModel):
    """Chip de cita del corpus aprobado (mismo componente en chat y consola)."""
    cita_visible: str


class RespuestaAgente(BaseModel):
    """Respuesta de POST /api/chat/mensaje. El agente PROPONE; nunca ejecuta."""
    mensaje: str
    fuentes: list[FuenteCita] = Field(default_factory=list)
    estado_flujo: str = "educacion"
    badge_tipo: Literal["B2C", "B2B"] | None = None
    guardrail: str | None = None          # "G1" | "G2" | ... si se activó una malla
    accion: Literal["proponer_quiz"] | None = None


class MensajeHistorial(BaseModel):
    """Un turno del historial tal como lo pinta el chat."""
    id: str
    rol: Literal["usuario", "agente"]
    texto: str
    ts: datetime
    fuentes: list[FuenteCita] = Field(default_factory=list)


class EstadoQuiz(BaseModel):
    iniciado: bool = False
    perfil_resultante: str | None = None


class ConversacionRecuperada(BaseModel):
    """Respuesta de GET /api/chat/conversacion (superset).
    Incluye `historial`/`badge_tipo` (frontend) y `id`/`messages` (segregación).
    """
    id: int
    lead_id: int
    estado_flujo: str = "saludo"
    badge_tipo: Literal["B2C", "B2B"] | None = None
    preguntas_respondidas: list[str] = Field(default_factory=list)
    quiz: EstadoQuiz = Field(default_factory=EstadoQuiz)
    historial: list[MensajeHistorial] = Field(default_factory=list)
    messages: list[MessageRead] = Field(default_factory=list)


class PreguntaQuizPublica(BaseModel):
    id: str
    texto: str
    opciones: list[str]


class QuizPublico(BaseModel):
    """Respuesta de POST /api/chat/quiz (opciones sin puntajes: no se filtra la rúbrica)."""
    preguntas: list[PreguntaQuizPublica]


class RespuestasQuizEntrada(BaseModel):
    """Body de POST /api/chat/quiz/respuestas."""
    respuestas: list[int]


class ResultadoQuiz(BaseModel):
    """Respuesta de POST /api/chat/quiz/respuestas. El perfil lo calcula CÓDIGO."""
    perfil: str
    mensaje: str


class ConsentimientoEntrada(BaseModel):
    """Body de POST /api/chat/consentimiento. Dos finalidades independientes."""
    email: str | None = None
    tratamiento_datos: bool = False
    comunicaciones_comerciales: bool = False


class ConsentimientoResultado(BaseModel):
    mensaje: str


# ──────────────────────────────────────────────────────────────────────────────
# CONTRATO #9 — DocumentoCorpus  [TABLA BD]
# ──────────────────────────────────────────────────────────────────────────────

class PublicoCorpus(str, Enum):
    B2C = "B2C"
    B2B = "B2B"
    AMBOS = "ambos"


class DocumentoCorpusBase(BaseModel):
    id: str
    titulo: str
    seccion: str
    contenido: str
    publico: PublicoCorpus
    version: str
    aprobado_por: str
    cita_visible: str


class DocumentoCorpusCreate(DocumentoCorpusBase):
    pass


class DocumentoCorpusRead(DocumentoCorpusBase):
    model_config = ConfigDict(from_attributes=True)
