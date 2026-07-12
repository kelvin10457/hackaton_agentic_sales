"""
test_consentimiento.py — Prueba del bloqueo de Regla #3 en el backend.

Verifica que la aprobación de AccionPropuesta está bloqueada en el BACKEND
cuando falta el consentimiento de comunicaciones_comerciales.
Esto NO es un botón oculto en el frontend — es un HTTP 403 real.

Ejecutar:
  cd backend
  .venv/bin/pytest app/tests/test_consentimiento.py -v
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:///./test_consentimiento.db"
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-padded-x")
os.environ.setdefault("CHAT_TOKEN_SECRET", "test-chat-secret-32-chars-padded")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base

_engine = create_engine("sqlite:///./test_consentimiento.db",
                        connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=_engine)
_Session = sessionmaker(bind=_engine)

from app.main import app
from app.auth import get_db, requiere_rol_ejecutivo
from app.models import (
    LeadV2 as LeadV2Model,
    Consentimiento as ConsentimientoModel,
    AccionPropuesta as AccionPropuestaModel,
    EventoAuditoria as EventoAuditoriaModel,
    User as UserModel,
)

# Hash precomputado — evita el bug passlib+bcrypt en la detección de versión
_TEST_PW_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewMH6vVkz.Au0B5m"
_STUB_USER = UserModel(id=1, name="Ejecutivo Test",
                       email="exec@test.com", password=_TEST_PW_HASH, rol="ejecutivo")


def _get_test_db():
    """Sesión sobre el archivo SQLite de prueba (sin rollback)."""
    db = _Session()
    try:
        yield db
    finally:
        db.close()


def _override_ejecutivo():
    """Sin verificación de BD — retorna usuario stub con rol ejecutivo."""
    return _STUB_USER


app.dependency_overrides[get_db] = _get_test_db
app.dependency_overrides[requiere_rol_ejecutivo] = _override_ejecutivo
# Registrar overrides de este módulo para que conftest los restaure antes de cada test
_MODULE_OVERRIDES = {get_db: _get_test_db, requiere_rol_ejecutivo: _override_ejecutivo}
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module", autouse=True)
def restaurar_overrides():
    """Limpia los overrides al terminar el módulo para no contaminar otros tests."""
    yield
    app.dependency_overrides.pop(requiere_rol_ejecutivo, None)


# ── Helpers de BD ─────────────────────────────────────────────────────────────

def _setup_lead() -> int:
    db = _Session()
    lead = LeadV2Model(
        nombre="Sofía Andrade",
        email="sofia.andrade@test.ec",
        email_normalizado="sofia.andrade@test.ec",
        estado_identificacion="identificado",
        etapa_embudo="calificado",
        segmento="b2c",
    )
    db.add(lead); db.commit(); db.refresh(lead)
    lead_id = lead.id; db.close()
    return lead_id


def _setup_accion(lead_id: int, estado: str = "pendiente") -> int:
    db = _Session()
    accion = AccionPropuestaModel(
        lead_id=lead_id, tipo="whatsapp",
        destinatario="+593991234567",
        mensaje_sugerido="Hola Sofía...",
        snapshot_senales={"urgencia_declarada": "alta"},
        generado_por="agente:cv5", estado=estado,
    )
    db.add(accion); db.commit(); db.refresh(accion)
    accion_id = accion.id; db.close()
    return accion_id


def _setup_consentimiento(lead_id: int, tratamiento: bool, comunicaciones: bool):
    db = _Session()
    c = ConsentimientoModel(
        lead_id=lead_id,
        tratamiento_datos_otorgado=tratamiento,
        comunicaciones_otorgado=comunicaciones,
    )
    db.add(c); db.commit(); db.close()


def _teardown():
    db = _Session()
    db.query(EventoAuditoriaModel).delete()
    db.query(ConsentimientoModel).delete()
    db.query(AccionPropuestaModel).delete()
    db.query(LeadV2Model).delete()
    db.commit(); db.close()


@pytest.fixture(autouse=True)
def limpiar_bd():
    _teardown(); yield; _teardown()


# =============================================================================
# TESTS — Regla #3: bloqueo de aprobación por consentimiento
# =============================================================================

def test_aprobar_sin_consentimiento_da_403():
    """Sin registro de consentimiento → HTTP 403 (no solo ocultar botón)."""
    lead_id = _setup_lead()
    accion_id = _setup_accion(lead_id)
    r = client.post(f"/api/consola/acciones/{accion_id}/aprobar")
    assert r.status_code == 403, \
        f"Sin consentimiento debe dar 403, dio {r.status_code}: {r.text}"
    assert "comunicaciones comerciales" in r.json().get("detail", "").lower()


def test_aprobar_con_solo_tratamiento_datos_da_403():
    """tratamiento_datos=True pero comunicaciones=False → HTTP 403."""
    lead_id = _setup_lead()
    accion_id = _setup_accion(lead_id)
    _setup_consentimiento(lead_id, tratamiento=True, comunicaciones=False)
    r = client.post(f"/api/consola/acciones/{accion_id}/aprobar")
    assert r.status_code == 403, \
        f"Solo tratamiento_datos debe dar 403, dio {r.status_code}: {r.text}"


def test_aprobar_con_comunicaciones_otorgado_da_200():
    """Ambos consentimientos → HTTP 200 y estado='aprobada'."""
    lead_id = _setup_lead()
    accion_id = _setup_accion(lead_id)
    _setup_consentimiento(lead_id, tratamiento=True, comunicaciones=True)
    r = client.post(f"/api/consola/acciones/{accion_id}/aprobar")
    assert r.status_code == 200, \
        f"Con consentimiento debe dar 200, dio {r.status_code}: {r.text}"
    data = r.json()
    assert data["estado"] == "aprobada"
    assert data["revisado_por"] == _STUB_USER.email


def test_aprobar_accion_obsoleta_da_409():
    """estado='obsoleta' → HTTP 409, aunque haya consentimiento."""
    lead_id = _setup_lead()
    accion_id = _setup_accion(lead_id, estado="obsoleta")
    _setup_consentimiento(lead_id, tratamiento=True, comunicaciones=True)
    r = client.post(f"/api/consola/acciones/{accion_id}/aprobar")
    assert r.status_code == 409, \
        f"Acción obsoleta debe dar 409, dio {r.status_code}: {r.text}"
    assert "obsoleta" in r.json().get("detail", "").lower()


def test_aprobar_accion_ya_aprobada_da_409():
    """Doble aprobación → HTTP 409."""
    lead_id = _setup_lead()
    accion_id = _setup_accion(lead_id, estado="aprobada")
    _setup_consentimiento(lead_id, tratamiento=True, comunicaciones=True)
    r = client.post(f"/api/consola/acciones/{accion_id}/aprobar")
    assert r.status_code == 409, \
        f"Acción ya aprobada debe dar 409, dio {r.status_code}"


def test_consentimiento_finalidades_son_independientes():
    """comunicaciones=True con tratamiento=False permite aprobar."""
    lead_id = _setup_lead()
    accion_id = _setup_accion(lead_id)
    _setup_consentimiento(lead_id, tratamiento=False, comunicaciones=True)

    r = client.post(f"/api/consola/acciones/{accion_id}/aprobar")
    assert r.status_code == 200, \
        f"comunicaciones=True permite aprobar aunque tratamiento=False, dio {r.status_code}"

    r2 = client.get(f"/api/consola/leads/{lead_id}/consentimiento")
    assert r2.status_code == 200
    data = r2.json()
    assert data["tratamiento_datos"]["otorgado"] is False
    assert data["comunicaciones_comerciales"]["otorgado"] is True
