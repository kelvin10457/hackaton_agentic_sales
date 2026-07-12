"""
Criterio 3.3 — "El ejecutivo puede APROBAR, EDITAR o RECHAZAR antes de enviar."

Es el foso del producto. Aquí se verifica que:
  · Aprobar sin tocar el borrador → 'aprobada'.
  · EDITAR y aprobar → 'editada_y_aprobada', se guarda lo que REALMENTE salió,
    se conserva el borrador original del agente y queda `editado_por_humano`.
  · Editar NO permite sortear el bloqueo por consentimiento (sigue 403).
  · Rechazar devuelve el lead a nutrición (no lo descarta).
  · Todo queda en la bitácora, con nombre y hora del humano.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_aprobacion.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-padded-x")
os.environ.setdefault("CHAT_TOKEN_SECRET", "test-chat-secret-32-chars-padded")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine as _ce
from sqlalchemy.orm import sessionmaker as _sm

from app.database import Base
from app.auth import get_db, SECRET_KEY, ALGORITHM
from app.main import app
from app.models import (
    AccionPropuesta, Consentimiento, LeadV2, ScoreLead, SenalesLead, User,
)

_engine = _ce("sqlite:///./test_aprobacion.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=_engine)
_Session = _sm(bind=_engine)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db
_MODULE_OVERRIDES = {get_db: _override_db}
client = TestClient(app, raise_server_exceptions=False)

EJECUTIVO = "carlos@futuroacademy.ec"


@pytest.fixture
def cabecera():
    db = _Session()
    user = db.query(User).filter(User.email == EJECUTIVO).first()
    if not user:
        user = User(name="Carlos Peña", email=EJECUTIVO, password="x", rol="ejecutivo")
        db.add(user)
        db.commit()
        db.refresh(user)
    uid = user.id
    db.close()
    token = jwt.encode(
        {"sub": str(uid), "rol": "ejecutivo",
         "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        SECRET_KEY, ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


def _crear_lead(comunicaciones: bool, marcador: str) -> int:
    """Lead con consentimiento, señales, score y una acción pendiente."""
    db = _Session()
    email = f"{marcador}@ejemplo.ec"
    lead = LeadV2(
        nombre=f"Lead {marcador}", email=email, email_normalizado=email,
        estado_identificacion="identificado", etapa_embudo="listo_para_asesor",
        segmento="b2c",
    )
    db.add(lead)
    db.flush()
    db.add(Consentimiento(
        lead_id=lead.id,
        tratamiento_datos_otorgado=True,
        comunicaciones_otorgado=comunicaciones,
    ))
    db.add(SenalesLead(lead_id=lead.id, pidio_asesor=True, mensajes_intercambiados=5))
    db.add(ScoreLead(lead_id=lead.id, total=88.0, banda="caliente", justificacion="x"))
    db.add(AccionPropuesta(
        lead_id=lead.id,
        tipo="agendar_reunion",
        destinatario={"email": email, "nombre": lead.nombre},
        asunto="Asunto del agente",
        mensaje_sugerido="Cuerpo redactado por el agente.",
        razonamiento="Score 88 (caliente).",
        fuentes_consultadas=["FA-003 §1"],
        snapshot_senales={},
        generado_por="agente:cv5",
        estado="pendiente",
    ))
    db.commit()
    lead_id = lead.id
    db.close()
    return lead_id


def _accion_de(lead_id: int, cabecera) -> dict:
    r = client.get(f"/api/consola/leads/{lead_id}/acciones", headers=cabecera)
    assert r.status_code == 200, r.text
    return r.json()[0]


# ── Aprobar sin cambios ──────────────────────────────────────────────────────

def test_aprobar_sin_editar_no_marca_edicion_humana(cabecera):
    lead_id = _crear_lead(comunicaciones=True, marcador="aprueba-tal-cual")
    accion = _accion_de(lead_id, cabecera)

    r = client.post(
        f"/api/consola/acciones/{accion['id']}/aprobar",
        json={"asunto": accion["asunto"], "cuerpo": accion["mensaje_sugerido"]},
        headers=cabecera,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["estado"] == "aprobada"
    assert d["editado_por_humano"] is False
    assert d["borrador_final"] is None
    assert d["revisado_por"] == EJECUTIVO


# ── EDITAR y aprobar — el plano final del vídeo ──────────────────────────────

def test_editar_y_aprobar_persiste_la_edicion(cabecera):
    lead_id = _crear_lead(comunicaciones=True, marcador="edita-y-aprueba")
    accion = _accion_de(lead_id, cabecera)

    nuevo_asunto = "Te llamo mañana a las 10:00"
    nuevo_cuerpo = "Hola, lo vemos con calma en una llamada.\n\nCarlos"

    r = client.post(
        f"/api/consola/acciones/{accion['id']}/aprobar",
        json={"asunto": nuevo_asunto, "cuerpo": nuevo_cuerpo},
        headers=cabecera,
    )
    assert r.status_code == 200, r.text
    d = r.json()

    # Lo que REALMENTE salió quedó guardado…
    assert d["estado"] == "editada_y_aprobada"
    assert d["editado_por_humano"] is True
    assert d["borrador_final"]["asunto"] == nuevo_asunto
    assert d["borrador_final"]["cuerpo"] == nuevo_cuerpo
    assert d["revisado_por"] == EJECUTIVO
    assert d["revisado_en"] is not None

    # …y el borrador ORIGINAL del agente se conserva (para poder comparar).
    assert d["asunto"] == "Asunto del agente"
    assert d["mensaje_sugerido"] == "Cuerpo redactado por el agente."


def test_editar_y_aprobar_deja_traza_en_la_bitacora(cabecera):
    """'El agente nunca tuvo la capacidad de enviarlo. Lo envió Carlos,
    y queda registrado que fue él.'"""
    lead_id = _crear_lead(comunicaciones=True, marcador="bitacora-edicion")
    accion = _accion_de(lead_id, cabecera)

    client.post(
        f"/api/consola/acciones/{accion['id']}/aprobar",
        json={"asunto": "Otro asunto", "cuerpo": "Otro cuerpo"},
        headers=cabecera,
    )

    eventos = client.get(f"/api/consola/leads/{lead_id}/auditoria", headers=cabecera).json()
    aprobados = [e for e in eventos if e["tipo_evento"] == "accion_aprobada"]
    assert aprobados, "la aprobación no quedó en la bitácora"

    evento = aprobados[0]
    assert evento["actor"] == "humano"
    assert evento["actor_id"] == EJECUTIVO          # quién
    assert evento["timestamp"]                       # cuándo
    assert evento["payload"]["editado_por_humano"] is True


def test_aprobar_deriva_el_lead(cabecera):
    lead_id = _crear_lead(comunicaciones=True, marcador="deriva")
    accion = _accion_de(lead_id, cabecera)
    client.post(f"/api/consola/acciones/{accion['id']}/aprobar", json={}, headers=cabecera)

    lead = client.get(f"/api/consola/leads/{lead_id}", headers=cabecera).json()
    assert lead["etapa_embudo"] == "derivado"


# ── El bloqueo por consentimiento no se puede sortear ────────────────────────

def test_editar_no_permite_saltarse_el_bloqueo_por_consentimiento(cabecera):
    """Sin consentimiento comercial, aprobar es 403 — aunque se edite el
    borrador. El bloqueo vive en la API, no en la UI."""
    lead_id = _crear_lead(comunicaciones=False, marcador="sofia-bloqueada")
    accion = _accion_de(lead_id, cabecera)

    r = client.post(
        f"/api/consola/acciones/{accion['id']}/aprobar",
        json={"asunto": "intento", "cuerpo": "saltarme el bloqueo"},
        headers=cabecera,
    )
    assert r.status_code == 403

    # Y la acción sigue intacta: nadie la movió.
    d = _accion_de(lead_id, cabecera)
    assert d["estado"] == "pendiente"
    assert d["editado_por_humano"] is False
    assert d["borrador_final"] is None


# ── Rechazar → nutrición (no se descarta) ────────────────────────────────────

def test_rechazar_devuelve_el_lead_a_nutricion(cabecera):
    lead_id = _crear_lead(comunicaciones=True, marcador="rechaza")
    accion = _accion_de(lead_id, cabecera)

    r = client.post(
        f"/api/consola/acciones/{accion['id']}/rechazar",
        json={"motivo_rechazo": "Prefiere esperar al próximo trimestre"},
        headers=cabecera,
    )
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "rechazada"

    lead = client.get(f"/api/consola/leads/{lead_id}", headers=cabecera).json()
    assert lead["etapa_embudo"] == "nutricion", "el lead se descartó en vez de nutrirse"
