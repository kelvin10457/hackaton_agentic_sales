"""
Router de la consola interna: /api/consola/*
Auth: JWT Bearer con claim rol='ejecutivo' (requiere_rol_ejecutivo).
Segregación garantizada: ningún endpoint de esta superficie acepta
X-Session-Token ni tokens firmados con CHAT_TOKEN_SECRET.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_db, requiere_rol_ejecutivo, create_session_token
from app.models import (
    User, Conversation, Message, DocumentoCorpus,
    EventoAuditoria as EventoAuditoriaModel,
)
from app.auditoria import (
    registrar_evento as _registrar,
    evento_lead_creado,
    evento_crm_upsert,
)
from app.validators import validar_cedula, validar_ruc
from app.identity import IdentityPort, get_identity_port
from app.schemas import (
    LeadV2Read, LeadV2Create,
    Senales, Score,
    OportunidadCreate, OportunidadRead,
    ConsentimientoRead, Otorgamiento,
    AccionPropuestaCreate, AccionPropuestaRead,
    EventoAuditoriaCreate, EventoAuditoriaRead,
    ConversacionV2Read,
    DocumentoCorpusCreate, DocumentoCorpusRead,
    EtapaEmbudo, Banda, TipoAccion, RutaSugerida,
    EstadoIdentificacion, EstadoAccion, TipoEvento,
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/consola", tags=["Consola (interna)"])
_TS = lambda: datetime.now(timezone.utc)


class VerificacionIdentidadRequest(BaseModel):
    documento: str  # Cédula (10 dígitos) o RUC (13 dígitos)


class VerificacionIdentidadResponse(BaseModel):
    documento: str
    valido: bool
    tipo: str  # cedula | ruc_natural | ruc_juridico | ruc_publico | invalido
    mensaje: str


# ──────────────────────────────────────────────────────────────────────────────
# Contrato #1 — Lead V2
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/leads", response_model=list[LeadV2Read])
def listar_leads_v2(
    skip: int = 0,
    limit: int = 100,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Lista LeadV2 persistidos con la paginación del CRUD legado."""
    return db.query(LeadV2Model).offset(skip).limit(limit).all()


@router.get("/leads/{lead_id}", response_model=LeadV2Read)
def obtener_lead_v2(
    lead_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Obtiene un LeadV2 persistido por su identificador real."""
    lead = db.query(LeadV2Model).filter(LeadV2Model.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado.")
    return lead


@router.post(
    "/identidad/verificar",
    response_model=VerificacionIdentidadResponse,
    summary="Verificar cédula o RUC ecuatoriano (módulo 10 / módulo 11)",
    tags=["Consola (interna)", "Identidad"],
)
def verificar_identidad(
    payload: VerificacionIdentidadRequest,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    identity: IdentityPort = Depends(get_identity_port),
):
    """Valida una cédula o RUC ecuatoriano usando algoritmo módulo 10 / módulo 11.
    Cuando es válido, clasifica el tipo de documento.
    Nota: esta validación es solo algorítmica — no consulta el Registro Civil ni el SRI.
    Para actualizar el estado_identificacion del lead, usa PATCH /api/consola/leads/{id}.
    [Tarea #4 — implementado en validators.py, función exacta del spec]
    """
    resultado = identity.resolver(payload.documento)
    return VerificacionIdentidadResponse(
        documento=resultado.documento,
        valido=resultado.valido,
        tipo=resultado.tipo,
        mensaje=resultado.mensaje,
    )


# ── Contratos #2 y #3 — Señales y Score ───────────────────────────────────────

from app.models import SenalesLead as SenalesModel, ScoreLead as ScoreModel
from app.scoring import recalcular_con_obsolescencia
from pydantic import BaseModel as _BMscoring


class SenalesUpsert(_BMscoring):
    """Payload para crear/actualizar señales del lead.
    REGLA CV5: cualquier cambio dispara recalculo de score
    y marca como 'obsoleta' toda AccionPropuesta pendiente.
    """
    objetivo: str | None = None
    horizonte: str | None = None
    pidio_asesor: bool | None = None
    completo_quiz: bool | None = None
    monto_declarado_usd: float | None = None
    experiencia_inversion: str | None = None
    perfil_riesgo: str | None = None
    num_colaboradores: int | None = None
    presupuesto_capacitacion_usd: float | None = None
    es_decisor: bool | None = None
    solicito_propuesta: bool | None = None


def _senales_to_schema(s: SenalesModel) -> Senales:
    return Senales(
        objetivo=s.objetivo, horizonte=s.horizonte, pidio_asesor=s.pidio_asesor,
        mensajes_intercambiados=s.mensajes_intercambiados or 0,
        completo_quiz=s.completo_quiz, monto_declarado_usd=s.monto_declarado_usd,
        experiencia_inversion=s.experiencia_inversion, perfil_riesgo=s.perfil_riesgo,
        num_colaboradores=s.num_colaboradores,
        presupuesto_capacitacion_usd=s.presupuesto_capacitacion_usd,
        es_decisor=s.es_decisor, solicito_propuesta=s.solicito_propuesta,
    )


def _score_to_schema(sc: ScoreModel, lead_id: int) -> Score:
    return Score(
        lead_id=lead_id,
        dimension_interes=sc.dimension_interes,
        dimension_capacidad=sc.dimension_capacidad,
        dimension_urgencia=sc.dimension_urgencia,
        dimension_fit=sc.dimension_fit,
        total=sc.total,
        banda=Banda(sc.banda),
        justificacion=sc.justificacion,
        calculado_en=sc.calculado_en,
    )


@router.get("/leads/{lead_id}/senales", response_model=Senales)
def obtener_senales(
    lead_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Devuelve las señales comerciales actuales del lead."""
    s = db.query(SenalesModel).filter(SenalesModel.lead_id == lead_id).first()
    if not s:
        # Señales neutras si no hay registro
        return Senales(mensajes_intercambiados=0)
    return _senales_to_schema(s)


@router.patch("/leads/{lead_id}/senales", response_model=Score)
def actualizar_senales(
    lead_id: int,
    payload: SenalesUpsert,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """REGLA CV5: actualiza señales, recalcula score y marca AccionPropuesta
    pendientes como 'obsoleta'. Retorna el score actualizado.
    """
    lead = db.query(LeadV2Model).filter(LeadV2Model.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead no encontrado.")

    cambios = payload.model_dump(exclude_unset=True)
    # Nunca se acepta el conteo desde el cliente: se deriva de mensajes reales.
    mensajes = db.query(Message).join(Conversation).filter(Conversation.lead_id == lead_id).count()
    cambios["mensajes_intercambiados"] = mensajes
    s = db.query(SenalesModel).filter(SenalesModel.lead_id == lead_id).first()
    if s:
        # PATCH real: no invalida acciones si el cliente no cambió ningún valor.
        cambio_real = any(getattr(s, campo) != valor for campo, valor in cambios.items())
        if not cambio_real:
            score = db.query(ScoreModel).filter(ScoreModel.lead_id == lead_id).first()
            if score:
                return _score_to_schema(score, lead_id)
            score, _ = recalcular_con_obsolescencia(db, lead_id, s, lead.segmento)
            return _score_to_schema(score, lead_id)
        for campo, valor in cambios.items():
            setattr(s, campo, valor)
        s.actualizado_en = _TS()
    else:
        s = SenalesModel(
            lead_id=lead_id,
            **cambios,
            actualizado_en=_TS(),
        )
        db.add(s)
    # Evidencia de identidad/email controlada por el backend.
    s.documento_valido = bool(lead.cedula and validar_cedula(lead.cedula))
    s.ruc_valido = bool(lead.cedula and validar_ruc(lead.cedula))
    s.email_valido = bool(lead.email and "@" in lead.email)
    dominio = (lead.email or "").split("@")[-1].lower()
    s.email_corporativo = bool(lead.email and dominio not in {"gmail.com", "hotmail.com", "outlook.com", "yahoo.com"})
    db.commit()
    db.refresh(s)

    # Motor CV5: recalcular + marcar obsoletas
    score, n_obsoletas = recalcular_con_obsolescencia(db, lead_id, s, lead.segmento)

    # Bitácora
    from app.auditoria import evento_score_calculado
    evento_score_calculado(db, lead_id, score.total, score.banda)
    if n_obsoletas:
        from app.auditoria import registrar_evento as _reg
        _reg(db, "sistema", "sistema", "acciones_marcadas_obsoletas", lead_id,
             {"n_obsoletas": n_obsoletas})

    return _score_to_schema(score, lead_id)


@router.get("/leads/{lead_id}/score", response_model=Score)
def obtener_score(
    lead_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Devuelve el score más reciente del lead.
    Si no existe, recalcula desde señales actuales (o retorna score 0).
    """
    score = db.query(ScoreModel).filter(ScoreModel.lead_id == lead_id).first()
    if score:
        return _score_to_schema(score, lead_id)

    # Intentar calcular desde señales existentes
    senales = db.query(SenalesModel).filter(SenalesModel.lead_id == lead_id).first()
    if senales:
        from app.scoring import upsert_score
        lead = db.query(LeadV2Model).filter(LeadV2Model.id == lead_id).first()
        score = upsert_score(db, lead_id, senales, lead.segmento if lead else None)
        return _score_to_schema(score, lead_id)

    # Sin datos: devolver score neutro
    return Score(
        lead_id=lead_id, dimension_interes=0, dimension_capacidad=0,
        dimension_urgencia=0, dimension_fit=0, total=0.0,
        banda=Banda.FRIO,
        justificacion="Sin señales registradas. Ejecuta PATCH /senales para calcular.",
        calculado_en=_TS(),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Contrato #4 — Oportunidad
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/leads/{lead_id}/oportunidad", response_model=OportunidadRead)
def obtener_oportunidad(
    lead_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Obtiene la oportunidad 1:1 del LeadV2.

    Retorna 404 si el lead no existe o si todavía no tiene oportunidad creada.
    """
    lead = db.query(LeadV2Model).filter(LeadV2Model.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado.")

    oportunidad = (
        db.query(OportunidadModel)
        .filter(OportunidadModel.lead_id == lead_id)
        .first()
    )
    if not oportunidad:
        raise HTTPException(
            status_code=404,
            detail="Oportunidad no encontrada para este lead.",
        )
    return oportunidad


# Helpers para convertir modelo BD → schema Pydantic
def _consentimiento_to_schema(c) -> ConsentimientoRead:
    return ConsentimientoRead(
        id=c.id, lead_id=c.lead_id,
        tratamiento_datos=Otorgamiento(
            otorgado=c.tratamiento_datos_otorgado,
            fecha=c.tratamiento_datos_fecha,
            canal=c.tratamiento_datos_canal,
        ),
        comunicaciones_comerciales=Otorgamiento(
            otorgado=c.comunicaciones_otorgado,
            fecha=c.comunicaciones_fecha,
            canal=c.comunicaciones_canal,
        ),
        version_politica=c.version_politica,
        updated_at=c.updated_at,
    )


def _accion_to_schema(a) -> AccionPropuestaRead:
    destinatario = a.destinatario
    if isinstance(destinatario, str):
        destinatario = {"email": destinatario, "nombre": ""}
    return AccionPropuestaRead(
        id=a.id, lead_id=a.lead_id,
        tipo=TipoAccion(a.tipo),
        destinatario=destinatario,
        mensaje_sugerido=a.mensaje_sugerido,
        snapshot_senales=Senales(**(a.snapshot_senales or {})),
        generado_por=a.generado_por,
        estado=EstadoAccion(a.estado),
        revisado_por=a.revisado_por,
        motivo_rechazo=a.motivo_rechazo,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


# ── Contrato #5 — Consentimiento ────────────────────────────────────────────

from app.models import Consentimiento as ConsentimientoModel
from pydantic import BaseModel as _BM


class ConsentimientoUpsertRequest(_BM):
    """Payload para crear/actualizar el consentimiento de un lead."""
    tratamiento_datos_otorgado: bool = False
    tratamiento_datos_canal: str | None = None
    comunicaciones_comerciales_otorgado: bool = False
    comunicaciones_comerciales_canal: str | None = None
    version_politica: str | None = None


@router.get("/leads/{lead_id}/consentimiento", response_model=ConsentimientoRead)
def obtener_consentimiento(
    lead_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Devuelve el consentimiento del lead con las DOS finalidades independientes."""
    c = db.query(ConsentimientoModel).filter(ConsentimientoModel.lead_id == lead_id).first()
    if not c:
        # Devolver estado neutro (no otorgado) si no hay registro aún
        return ConsentimientoRead(
            id=0, lead_id=lead_id,
            tratamiento_datos=Otorgamiento(otorgado=False),
            comunicaciones_comerciales=Otorgamiento(otorgado=False),
        )
    return _consentimiento_to_schema(c)


@router.post("/leads/{lead_id}/consentimiento", response_model=ConsentimientoRead, status_code=201)
def upsert_consentimiento(
    lead_id: int,
    payload: ConsentimientoUpsertRequest,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Crea o actualiza el consentimiento del lead (upsert).
    REGLA #3: las dos finalidades son INDEPENDIENTES:
    - tratamiento_datos → habilita crm_upsert
    - comunicaciones_comerciales → habilita aprobar AccionPropuesta
    """
    ahora = _TS()
    c = db.query(ConsentimientoModel).filter(ConsentimientoModel.lead_id == lead_id).first()
    if c:
        c.tratamiento_datos_otorgado = payload.tratamiento_datos_otorgado
        c.tratamiento_datos_canal = payload.tratamiento_datos_canal
        c.tratamiento_datos_fecha = ahora if payload.tratamiento_datos_otorgado else c.tratamiento_datos_fecha
        c.comunicaciones_otorgado = payload.comunicaciones_comerciales_otorgado
        c.comunicaciones_canal = payload.comunicaciones_comerciales_canal
        c.comunicaciones_fecha = ahora if payload.comunicaciones_comerciales_otorgado else c.comunicaciones_fecha
        c.version_politica = payload.version_politica
        c.updated_at = ahora
    else:
        c = ConsentimientoModel(
            lead_id=lead_id,
            tratamiento_datos_otorgado=payload.tratamiento_datos_otorgado,
            tratamiento_datos_canal=payload.tratamiento_datos_canal,
            tratamiento_datos_fecha=ahora if payload.tratamiento_datos_otorgado else None,
            comunicaciones_otorgado=payload.comunicaciones_comerciales_otorgado,
            comunicaciones_canal=payload.comunicaciones_comerciales_canal,
            comunicaciones_fecha=ahora if payload.comunicaciones_comerciales_otorgado else None,
            version_politica=payload.version_politica,
        )
        db.add(c)
    db.commit()
    db.refresh(c)
    # Bitácora
    from app.auditoria import evento_consentimiento_otorgado
    if payload.tratamiento_datos_otorgado:
        evento_consentimiento_otorgado(db, lead_id, "tratamiento_datos", payload.tratamiento_datos_canal or "")
    if payload.comunicaciones_comerciales_otorgado:
        evento_consentimiento_otorgado(db, lead_id, "comunicaciones_comerciales", payload.comunicaciones_comerciales_canal or "")
    return _consentimiento_to_schema(c)


# ── Contrato #6 — AccionPropuesta ───────────────────────────────────────────

from app.models import AccionPropuesta as AccionPropuestaModel


@router.get("/leads/{lead_id}/acciones", response_model=list[AccionPropuestaRead])
def listar_acciones(
    lead_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Lista acciones propuestas para el lead (orden: más reciente primero)."""
    acciones = (
        db.query(AccionPropuestaModel)
        .filter(AccionPropuestaModel.lead_id == lead_id)
        .order_by(AccionPropuestaModel.created_at.desc())
        .all()
    )
    return [_accion_to_schema(a) for a in acciones]


@router.post("/leads/{lead_id}/acciones", response_model=AccionPropuestaRead, status_code=201)
def crear_accion(
    lead_id: int,
    payload: AccionPropuestaCreate,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Crea una AccionPropuesta con snapshot de señales actuales."""
    accion = AccionPropuestaModel(
        lead_id=lead_id,
        tipo=payload.tipo.value,
        destinatario=payload.destinatario.model_dump(),
        mensaje_sugerido=payload.mensaje_sugerido,
        snapshot_senales=payload.snapshot_senales.model_dump(exclude_none=True),
        generado_por=payload.generado_por,
        estado="pendiente",
    )
    db.add(accion)
    db.commit()
    db.refresh(accion)
    from app.auditoria import registrar_evento as _reg
    _reg(db, "sistema", payload.generado_por, "accion_generada", lead_id, {"accion_id": accion.id})
    return _accion_to_schema(accion)


@router.post(
    "/acciones/{accion_id}/aprobar",
    response_model=AccionPropuestaRead,
    responses={
        403: {"description": "Lead no ha consentido comunicaciones comerciales."},
        409: {"description": "Acción obsoleta: los datos del lead cambiaron después de generarla."},
    },
)
def aprobar_accion(
    accion_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """REGLA #3: Verifica comunicaciones_comerciales antes de aprobar.
    Este bloqueo ocurre en el BACKEND, no en la UI.
    """
    accion = db.query(AccionPropuestaModel).filter(AccionPropuestaModel.id == accion_id).first()
    if not accion:
        raise HTTPException(status_code=404, detail="Acción no encontrada.")

    # REGLA #3 — verificar consentimiento comunicaciones_comerciales
    consentimiento = (
        db.query(ConsentimientoModel)
        .filter(ConsentimientoModel.lead_id == accion.lead_id)
        .first()
    )
    if not consentimiento or not consentimiento.comunicaciones_otorgado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este lead no ha consentido comunicaciones comerciales. "
                   "Obtener consentimiento antes de aprobar la acción.",
        )

    # CV5 — verificar que la acción no esté obsoleta
    if accion.estado == "obsoleta":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Los datos del lead cambiaron después de generar esta propuesta. "
                   "La acción está obsoleta; genera una nueva.",
        )

    if accion.estado not in ("pendiente", "rechazada"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La acción ya está en estado '{accion.estado}' y no puede aprobarse.",
        )

    accion.estado = "aprobada"
    accion.revisado_por = ejecutivo.email
    accion.updated_at = _TS()
    db.commit()
    db.refresh(accion)

    from app.auditoria import evento_accion_aprobada
    evento_accion_aprobada(db, actor_id=ejecutivo.email, lead_id=accion.lead_id, accion_id=accion_id)

    return _accion_to_schema(accion)


class RechazarAccionRequest(BaseModel):
    motivo_rechazo: str


@router.post("/acciones/{accion_id}/rechazar", response_model=AccionPropuestaRead)
def rechazar_accion(
    accion_id: int,
    payload: RechazarAccionRequest,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Rechaza únicamente una propuesta pendiente y envía el lead a nutrición."""
    accion = db.query(AccionPropuestaModel).filter(AccionPropuestaModel.id == accion_id).first()
    if not accion:
        raise HTTPException(404, "Acción no encontrada.")
    if accion.estado != "pendiente":
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se pueden rechazar acciones pendientes.")
    accion.estado = "rechazada"
    accion.motivo_rechazo = payload.motivo_rechazo
    accion.revisado_por = ejecutivo.email
    accion.updated_at = _TS()
    lead = db.query(LeadV2Model).filter(LeadV2Model.id == accion.lead_id).first()
    if lead:
        lead.etapa_embudo = "nutricion"
        lead.updated_at = _TS()
    db.commit()
    db.refresh(accion)
    _registrar(db, "humano", ejecutivo.email, "accion_rechazada", accion.lead_id,
               {"accion_id": accion.id, "motivo_rechazo": payload.motivo_rechazo})
    return _accion_to_schema(accion)


# ──────────────────────────────────────────────────────────────────────────────
# Contrato #7 — EventoAuditoria (solo GET y POST — nunca PATCH/DELETE)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/leads/{lead_id}/auditoria", response_model=list[EventoAuditoriaRead])
def obtener_auditoria(
    lead_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Bitácora append-only de un lead. Solo lectura.
    Orden: más reciente primero.
    REGLA: no existe PATCH ni DELETE para esta tabla.
    """
    from app.models import EventoAuditoria as M
    eventos = (
        db.query(M)
        .filter(M.lead_id == lead_id)
        .order_by(M.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        EventoAuditoriaRead(
            id=e.id,
            actor=e.actor,
            actor_id=e.actor_id,
            tipo_evento=TipoEvento(e.tipo_evento),
            lead_id=e.lead_id,
            payload=e.payload,
            timestamp=e.timestamp,
        )
        for e in eventos
    ]


@router.post("/auditoria", response_model=EventoAuditoriaRead, status_code=201)
def registrar_evento_endpoint(
    payload: EventoAuditoriaCreate,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Inserta un EventoAuditoria. APPEND-ONLY: nunca actualiza ni borra.
    No existen rutas PATCH ni DELETE para esta tabla.
    """
    evento = _registrar(
        db,
        actor=payload.actor,
        actor_id=payload.actor_id,
        tipo_evento=payload.tipo_evento.value,
        lead_id=payload.lead_id,
        payload=payload.payload,
    )
    return EventoAuditoriaRead(
        id=evento.id,
        actor=evento.actor,
        actor_id=evento.actor_id,
        tipo_evento=TipoEvento(evento.tipo_evento),
        lead_id=evento.lead_id,
        payload=evento.payload,
        timestamp=evento.timestamp,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Contrato #8 — Generar token de sesión de chat para una conversación
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/conversaciones/{conv_id}/token-sesion",
    summary="Genera un token de sesión de chat para la conversación indicada",
)
def generar_token_sesion(
    conv_id: int,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """El ejecutivo emite el token opaco que se entrega al lead para /api/chat/*.
    El token está firmado con CHAT_TOKEN_SECRET y lleva conv_id embebido.
    """
    conversacion = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conversacion:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    token = create_session_token(conv_id)
    conversacion.token_sesion = token
    db.commit()
    return {"conversacion_id": conv_id, "token_sesion": token}


# ──────────────────────────────────────────────────────────────────────────────
# Contrato #9 — DocumentoCorpus
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/corpus", response_model=list[DocumentoCorpusRead])
def listar_corpus(
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Lista los documentos aprobados persistidos en el corpus."""
    return db.query(DocumentoCorpus).order_by(DocumentoCorpus.id).all()


@router.post("/corpus", response_model=DocumentoCorpusRead, status_code=201)
def crear_documento(
    payload: DocumentoCorpusCreate,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Inserta un documento aprobado en el corpus."""
    documento = DocumentoCorpus(
        **payload.model_dump(exclude={"publico"}),
        publico=payload.publico.value,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


# ──────────────────────────────────────────────────────────────────────────────
# CRM — Tarea #5: upsert idempotente + bloqueo de anónimos
# ──────────────────────────────────────────────────────────────────────────────

from app.crm import get_crm
from app.models import LeadV2 as LeadV2Model, Oportunidad as OportunidadModel
from pydantic import BaseModel as _BaseModel


class CRMUpsertRequest(_BaseModel):
    lead_id: int


class CRMUpsertResponse(_BaseModel):
    lead_id: int
    contacto_id: str
    oportunidad_id: str
    accion: str  # "creado" | "actualizado"


@router.post(
    "/leads",
    response_model=LeadV2Read,
    status_code=201,
    summary="Crear lead V2 (tabla leads_v2)",
)
def crear_lead_v2(
    payload: LeadV2Create,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """Crea un lead en leads_v2. El email_normalizado se deriva automáticamente."""
    from app.models import LeadV2 as M
    existente = None
    if payload.email_normalizado:
        existente = db.query(M).filter(M.email_normalizado == payload.email_normalizado).first()
    if existente:
        raise HTTPException(409, f"Ya existe un lead con email '{payload.email_normalizado}'.")

    data = payload.model_dump()
    lead = M(**data)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    # Bitácora: registrar creación del lead
    evento_lead_creado(db, actor_id=ejecutivo.email, lead_id=lead.id,
                       extra={"segmento": lead.segmento, "estado": lead.estado_identificacion})
    return LeadV2Read.model_validate(lead)


@router.post(
    "/crm/upsert",
    response_model=CRMUpsertResponse,
    summary="Upsert idempotente en CRM — bloquea leads anónimos (Regla #1)",
    responses={
        422: {"description": "Lead anónimo o sin email — no puede entrar al CRM."},
    },
)
def crm_upsert(
    payload: CRMUpsertRequest,
    ejecutivo: User = Depends(requiere_rol_ejecutivo),
    db: Session = Depends(get_db),
):
    """REGLA #1: Lanza 422 si el lead tiene estado_identificacion='anonimo'.
    Idempotente: se puede llamar N veces con el mismo lead_id sin crear duplicados.
    Registra el evento CRM_UPSERT en la bitácora (implementación real en Tarea #6).
    """
    from app.models import LeadV2 as M
    lead_db = db.query(M).filter(M.id == payload.lead_id).first()
    if not lead_db:
        raise HTTPException(404, f"Lead #{payload.lead_id} no encontrado en leads_v2.")

    # Conserva los bloqueos previos antes de evaluar el nuevo consentimiento.
    if lead_db.estado_identificacion == "anonimo":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Lead con estado 'anonimo' no puede escribirse en el CRM.")
    if not lead_db.email_normalizado:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "El lead necesita email para registrarse en el CRM.")
    consentimiento = db.query(ConsentimientoModel).filter(ConsentimientoModel.lead_id == lead_db.id).first()
    if not consentimiento or not consentimiento.tratamiento_datos_otorgado:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "El lead debe otorgar consentimiento de tratamiento de datos antes del CRM.")

    lead_schema = LeadV2Read.model_validate(lead_db)

    crm = get_crm(db)

    # Verificar si ya existía antes del upsert
    from app.models import Oportunidad as OM
    ya_existia = db.query(OM).filter(OM.lead_id == lead_db.id).first() is not None

    contacto_id = crm.upsert_contacto(lead_schema)
    oportunidad_id = crm.upsert_oportunidad(lead_schema, contacto_id)
    accion = "actualizado" if ya_existia else "creado"

    # Contacto, oportunidad y bitácora se confirman en una única transacción.
    db.add(EventoAuditoriaModel(
        actor="humano",
        actor_id=ejecutivo.email,
        tipo_evento="crm_upsert",
        lead_id=payload.lead_id,
        payload={"contacto_id": contacto_id, "accion": accion},
        timestamp=_TS(),
    ))
    db.commit()

    return CRMUpsertResponse(
        lead_id=payload.lead_id,
        contacto_id=contacto_id,
        oportunidad_id=oportunidad_id,
        accion=accion,
    )
