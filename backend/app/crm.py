"""
crm.py — Puerto CRM del hackathon.

Interfaz exacta del spec (no cambiar nombres: el resto del equipo la usa así):

    class CRMPort(ABC):
        def upsert_contacto(self, lead: Lead) -> str: ...
        def upsert_oportunidad(self, lead: Lead, contacto_id: str) -> str: ...

CRMSimulado implementa el puerto sobre Postgres para la demo.
En producción se reemplazaría por HubSpot, Salesforce, etc.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from schemas import LeadV2Read, EstadoIdentificacion
from models import LeadV2 as LeadV2Model, Oportunidad as OportunidadModel, ScoreLead, SenalesLead
from scoring import ruta_sugerida


# ──────────────────────────────────────────────────────────────────────────────
# INTERFAZ (no cambiar nombres)
# ──────────────────────────────────────────────────────────────────────────────

class CRMPort(ABC):
    """Puerto abstracto del CRM. Implementar para cada CRM externo."""

    @abstractmethod
    def upsert_contacto(self, lead: LeadV2Read) -> str:
        """Crea o actualiza el contacto en el CRM.
        Clave de dedup: email_normalizado (minúsculas + trim).
        Retorna el ID del contacto (str para compatibilidad con CRMs externos).
        REGLA #1: lanza 422 si lead.estado_identificacion == 'anonimo'.
        """
        ...

    @abstractmethod
    def upsert_oportunidad(self, lead: LeadV2Read, contacto_id: str) -> str:
        """Crea o actualiza la oportunidad del CRM asociada al contacto.
        Retorna el ID de la oportunidad en el CRM.
        """
        ...


# ──────────────────────────────────────────────────────────────────────────────
# IMPLEMENTACIÓN SIMULADA (Postgres / SQLite para demo)
# ──────────────────────────────────────────────────────────────────────────────

class CRMSimulado(CRMPort):
    """Implementación sobre la BD local. Para la demo del hackathon.
    Garantiza idempotencia: se busca por email_normalizado antes de insertar.
    """

    def __init__(self, db: Session):
        self.db = db

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _bloquear_anonimo(self, lead: LeadV2Read) -> None:
        """REGLA DE NEGOCIO #1 — nunca escribir un lead anónimo en el CRM."""
        if lead.estado_identificacion == EstadoIdentificacion.ANONIMO:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Lead con estado 'anonimo' no puede escribirse en el CRM. "
                    "Debe estar identificado o verificado primero."
                ),
            )

    def _buscar_por_email(self, email_normalizado: str) -> LeadV2Model | None:
        return (
            self.db.query(LeadV2Model)
            .filter(LeadV2Model.email_normalizado == email_normalizado)
            .first()
        )

    # ── upsert_contacto ───────────────────────────────────────────────────────

    def upsert_contacto(self, lead: LeadV2Read) -> str:
        """Idempotente: busca por email_normalizado; actualiza si existe, crea si no.
        NUNCA crea un duplicado aunque se llame N veces con el mismo email.
        """
        self._bloquear_anonimo(lead)

        if not lead.email_normalizado:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El lead necesita email para registrarse en el CRM.",
            )

        existente = self._buscar_por_email(lead.email_normalizado)

        if existente:
            # ACTUALIZAR — idempotencia garantizada
            existente.nombre = lead.nombre
            existente.telefono = lead.telefono
            existente.cedula = lead.cedula
            existente.empresa = lead.empresa
            existente.cargo = lead.cargo
            existente.estado_identificacion = lead.estado_identificacion.value
            existente.etapa_embudo = lead.etapa_embudo.value
            existente.segmento = lead.segmento
            existente.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            return str(existente.id)
        else:
            # CREAR
            nuevo = LeadV2Model(
                nombre=lead.nombre,
                email=lead.email,
                email_normalizado=lead.email_normalizado,
                telefono=lead.telefono,
                cedula=lead.cedula,
                empresa=lead.empresa,
                cargo=lead.cargo,
                estado_identificacion=lead.estado_identificacion.value,
                etapa_embudo=lead.etapa_embudo.value,
                segmento=lead.segmento,
            )
            self.db.add(nuevo)
            self.db.flush()
            self.db.refresh(nuevo)
            return str(nuevo.id)

    # ── upsert_oportunidad ────────────────────────────────────────────────────

    def upsert_oportunidad(self, lead: LeadV2Read, contacto_id: str) -> str:
        """Una oportunidad por lead. Actualiza si existe, crea si no.
        El resumen se genera automáticamente si el lead no tiene uno explícito.
        """
        self._bloquear_anonimo(lead)

        lead_db_id = int(contacto_id)
        existente = (
            self.db.query(OportunidadModel)
            .filter(OportunidadModel.lead_id == lead_db_id)
            .first()
        )

        resumen = (
            f"Lead {lead.segmento.upper()} — {lead.nombre}. "
            f"Etapa: {lead.etapa_embudo.value}. "
            f"Estado: {lead.estado_identificacion.value}."
        )
        score = self.db.query(ScoreLead).filter(ScoreLead.lead_id == lead_db_id).first()
        senales = self.db.query(SenalesLead).filter(SenalesLead.lead_id == lead_db_id).first()
        ruta = ruta_sugerida(lead.segmento, score.total if score else 0.0,
                              bool(senales and senales.pidio_asesor))
        valor_estimado = senales.monto_declarado_usd if senales else None
        tipo = (
            "B2B_corporativo" if lead.segmento == "b2b" else
            "B2C_asesoria" if ruta == "asesoria_inversion" else
            "B2C_programa"
        )
        nombre = (
            f"{lead.empresa or lead.nombre} — Programa Corporativo"
            if tipo == "B2B_corporativo" else
            f"{lead.nombre} — Programa Inicial + Asesoría"
            if tipo == "B2C_asesoria" else
            f"{lead.nombre} — Programa Inicial"
        )

        if existente:
            existente.resumen = resumen
            existente.etapa = lead.etapa_embudo.value
            existente.ruta_sugerida = ruta
            existente.nombre = nombre
            existente.tipo = tipo
            existente.valor_estimado = valor_estimado
            existente.score_actual = score.total if score else 0.0
            existente.propietario = "carlos@futuroacademy.ec"
            existente.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            return str(existente.id)
        else:
            nueva = OportunidadModel(
                lead_id=lead_db_id,
                nombre=nombre,
                tipo=tipo,
                resumen=resumen,
                valor_estimado=valor_estimado,
                score_actual=score.total if score else 0.0,
                propietario="carlos@futuroacademy.ec",
                etapa=lead.etapa_embudo.value,
                ruta_sugerida=ruta,
            )
            self.db.add(nueva)
            self.db.flush()
            self.db.refresh(nueva)
            return str(nueva.id)


# ──────────────────────────────────────────────────────────────────────────────
# Factory — inyección de dependencia para FastAPI
# ──────────────────────────────────────────────────────────────────────────────

def get_crm(db: Session) -> CRMPort:
    """Retorna la implementación activa del CRM.
    Cambiar aquí para apuntar a HubSpot/Salesforce en producción.
    """
    return CRMSimulado(db)
