"""
test_upsert_idempotente.py — Prueba explícita de idempotencia del CRM.

Verifica:
  - Llamar upsert_contacto dos veces con el mismo email devuelve el mismo ID.
  - No se crean duplicados en la BD (count == 1 después de N llamadas).
  - Un lead anónimo lanza HTTP 422 antes de tocar la BD.

Ejecutar:
  cd backend
  PYTHONPATH=app .venv/bin/pytest app/tests/test_upsert_idempotente.py -v
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:///./test_upsert.db"
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-padded-x")
os.environ.setdefault("CHAT_TOKEN_SECRET", "test-chat-secret-32-chars-padded")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from database import Base
from models import LeadV2 as LeadV2Model, Oportunidad as OportunidadModel
from schemas import LeadV2Read, EstadoIdentificacion, EtapaEmbudo
from crm import CRMSimulado, CRMPort

# ── Fixtures ──────────────────────────────────────────────────────────────────

_engine = create_engine(
    "sqlite:///./test_upsert.db",
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=_engine)
_Session = sessionmaker(bind=_engine)


@pytest.fixture()
def db():
    """Sesión fresca por cada test, con rollback al final."""
    connection = _engine.connect()
    transaction = connection.begin()
    session = _Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def crm(db):
    return CRMSimulado(db)


def _lead(
    nombre: str = "María Villacís",
    email: str = "maria.villacis@ejemplo.ec",
    estado: EstadoIdentificacion = EstadoIdentificacion.IDENTIFICADO,
) -> LeadV2Read:
    email_norm = email.strip().lower()
    return LeadV2Read(
        id=0,
        nombre=nombre,
        email=email,
        email_normalizado=email_norm,
        telefono="+593991234567",
        estado_identificacion=estado,
        etapa_embudo=EtapaEmbudo.CALIFICADO,
        segmento="b2c",
        created_at=datetime.now(timezone.utc),
    )


# =============================================================================
# test_upsert_idempotente  (el test que el spec pide explícitamente)
# =============================================================================

def test_upsert_idempotente(crm, db):
    """Llamar upsert_contacto N veces con el mismo email normalizado:
    - Devuelve el mismo ID siempre.
    - Solo existe UN registro en la BD (count == 1).
    """
    lead = _lead()

    # Primera llamada — debe CREAR
    id_1 = crm.upsert_contacto(lead)
    assert id_1 is not None

    # Segunda llamada — mismo email → debe ACTUALIZAR, no crear
    id_2 = crm.upsert_contacto(lead)
    assert id_2 == id_1, f"Idempotencia rota: id_1={id_1}, id_2={id_2}"

    # Tercera llamada — misma garantía
    id_3 = crm.upsert_contacto(lead)
    assert id_3 == id_1, f"Idempotencia rota en 3ª llamada: {id_3}"

    # Solo debe existir UN registro en la BD
    count = db.query(LeadV2Model).filter(
        LeadV2Model.email_normalizado == lead.email_normalizado
    ).count()
    assert count == 1, f"Se crearon {count} registros con el mismo email — idempotencia rota"


def test_upsert_normaliza_email(crm, db):
    """El mismo email con distinto casing/espacios debe mapearse al mismo contacto."""
    lead_original = _lead(email="Maria.Villacis@EJEMPLO.EC")
    lead_variante  = _lead(email="  maria.villacis@ejemplo.ec  ")

    # Normalizar manualmente (simula lo que hace el schema validator)
    lead_original = lead_original.model_copy(
        update={"email_normalizado": "maria.villacis@ejemplo.ec"}
    )
    lead_variante = lead_variante.model_copy(
        update={"email_normalizado": "maria.villacis@ejemplo.ec"}
    )

    id_1 = crm.upsert_contacto(lead_original)
    id_2 = crm.upsert_contacto(lead_variante)

    assert id_1 == id_2, "Emails equivalentes deben producir el mismo ID de contacto"
    count = db.query(LeadV2Model).filter(
        LeadV2Model.email_normalizado == "maria.villacis@ejemplo.ec"
    ).count()
    assert count == 1


def test_upsert_anonimo_bloqueado(crm):
    """REGLA #1: un lead anónimo JAMÁS puede escribirse en el CRM."""
    lead_anonimo = _lead(estado=EstadoIdentificacion.ANONIMO)

    with pytest.raises(HTTPException) as exc_info:
        crm.upsert_contacto(lead_anonimo)

    assert exc_info.value.status_code == 422
    assert "anonimo" in exc_info.value.detail.lower()


def test_upsert_sin_email_bloqueado(crm):
    """Lead sin email_normalizado no puede entrar al CRM."""
    lead_sin_email = LeadV2Read(
        id=0, nombre="Sin Email",
        estado_identificacion=EstadoIdentificacion.IDENTIFICADO,
        etapa_embudo=EtapaEmbudo.NUEVO,
        segmento="b2c",
        created_at=datetime.now(timezone.utc),
    )
    with pytest.raises(HTTPException) as exc_info:
        crm.upsert_contacto(lead_sin_email)
    assert exc_info.value.status_code == 422


def test_upsert_oportunidad_idempotente(crm, db):
    """upsert_oportunidad también es idempotente: solo una oportunidad por lead."""
    lead = _lead()
    contacto_id = crm.upsert_contacto(lead)

    op_id_1 = crm.upsert_oportunidad(lead, contacto_id)
    op_id_2 = crm.upsert_oportunidad(lead, contacto_id)

    assert op_id_1 == op_id_2, "upsert_oportunidad debe ser idempotente"

    count = db.query(OportunidadModel).filter(
        OportunidadModel.lead_id == int(contacto_id)
    ).count()
    assert count == 1, f"Se crearon {count} oportunidades para el mismo lead"


def test_crm_port_interfaz():
    """CRMSimulado implementa correctamente la interfaz CRMPort."""
    assert issubclass(CRMSimulado, CRMPort)
    # Verificar que los métodos abstractos están implementados
    assert hasattr(CRMSimulado, "upsert_contacto")
    assert hasattr(CRMSimulado, "upsert_oportunidad")
