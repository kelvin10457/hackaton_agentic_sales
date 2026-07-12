"""Pruebas de los endpoints persistidos de LeadV2 en la consola."""
import os
import sys
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_consola_leads.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-padded-x")
os.environ.setdefault("CHAT_TOKEN_SECRET", "test-chat-secret-32-chars-padded")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import ALGORITHM, SECRET_KEY, get_db
from app.database import Base
from app.main import app
from app.models import LeadV2, Oportunidad, User


_test_engine = create_engine(
    "sqlite:///./test_consola_leads.db",
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=_test_engine)
_TestSession = sessionmaker(bind=_test_engine)


def _override_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db
_MODULE_OVERRIDES = {get_db: _override_db}
client = TestClient(app)


@pytest.fixture(autouse=True)
def limpiar_base():
    db = _TestSession()
    db.query(Oportunidad).delete()
    db.query(LeadV2).delete()
    db.query(User).delete()
    db.add(User(name="Ejecutiva", email="ejecutiva@empresa.ec", password="hash"))
    db.commit()
    db.close()


def _headers() -> dict[str, str]:
    db = _TestSession()
    user_id = db.query(User.id).first()[0]
    db.close()
    token = jwt.encode(
        {
            "sub": str(user_id),
            "rol": "ejecutivo",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        SECRET_KEY,
        ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


def _crear_leads() -> list[int]:
    db = _TestSession()
    leads = [
        LeadV2(nombre="Ana", email_normalizado="ana@ejemplo.ec"),
        LeadV2(nombre="Bruno", email_normalizado="bruno@ejemplo.ec"),
        LeadV2(nombre="Carla", email_normalizado="carla@ejemplo.ec"),
    ]
    db.add_all(leads)
    db.commit()
    ids = [lead.id for lead in leads]
    db.close()
    return ids


def test_listar_leads_v2_usa_tabla_real_y_paginacion():
    ids = _crear_leads()

    response = client.get("/api/consola/leads?skip=1&limit=1", headers=_headers())

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == ids[1]
    assert data[0]["nombre"] == "Bruno"


def test_obtener_lead_v2_usa_id_real():
    lead_id = _crear_leads()[2]

    response = client.get(f"/api/consola/leads/{lead_id}", headers=_headers())

    assert response.status_code == 200
    assert response.json()["id"] == lead_id
    assert response.json()["nombre"] == "Carla"


def test_obtener_lead_v2_inexistente_retorna_404():
    response = client.get("/api/consola/leads/999999", headers=_headers())

    assert response.status_code == 404
    assert response.json() == {"detail": "Lead no encontrado."}


def test_obtener_oportunidad_v2_usa_relacion_persistida():
    lead_id = _crear_leads()[0]
    db = _TestSession()
    db.add(
        Oportunidad(
            lead_id=lead_id,
            resumen="Solicitó una propuesta comercial.",
            valor_estimado=15000.0,
            probabilidad_cierre=0.78,
            ruta_sugerida="b2c_digital",
            nombre="María Villacís — Programa Inicial + Asesoría",
            tipo="B2C_asesoria",
            score_actual=85.0,
            propietario="carlos@futuroacademy.ec",
            etapa="listo_para_asesor",
        )
    )
    db.commit()
    db.close()

    response = client.get(
        f"/api/consola/leads/{lead_id}/oportunidad", headers=_headers()
    )

    assert response.status_code == 200
    assert response.json()["lead_id"] == lead_id
    assert response.json()["resumen"] == "Solicitó una propuesta comercial."


def test_obtener_oportunidad_sin_oportunidad_retorna_404():
    lead_id = _crear_leads()[0]

    response = client.get(
        f"/api/consola/leads/{lead_id}/oportunidad", headers=_headers()
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Oportunidad no encontrada para este lead."}


def test_obtener_oportunidad_de_lead_inexistente_retorna_404():
    response = client.get(
        "/api/consola/leads/999999/oportunidad", headers=_headers()
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Lead no encontrado."}
