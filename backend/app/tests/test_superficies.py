"""
test_superficies.py — Prueba la segregación de las dos superficies de API.

Verifica:
  - /api/consola/* requiere JWT Bearer con rol='ejecutivo'
  - /api/chat/* requiere X-Session-Token (firmado con CHAT_TOKEN_SECRET)
  - Un token de una superficie NO sirve en la otra

Ejecutar:
  cd backend
  PYTHONPATH=app .venv/bin/pytest app/tests/test_superficies.py -v
"""
import os
import sys
from uuid import uuid4

# Establecer variables de entorno ANTES de cualquier import de la app
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_superficies.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-padded-x")
os.environ.setdefault("CHAT_TOKEN_SECRET", "test-chat-secret-32-chars-padded")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("CHAT_TOKEN_EXPIRE_HOURS", "24")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Importar DESPUÉS de setear env vars
from database import Base, engine
from auth import get_db, SECRET_KEY, CHAT_TOKEN_SECRET, ALGORITHM

# Crear tablas en SQLite de prueba
Base.metadata.create_all(bind=engine)

from main import app
from models import Conversation, Lead, Message, User

# ── Override de BD con SQLite en memoria para tests ───────────────────────────

from sqlalchemy import create_engine as _ce
from sqlalchemy.orm import sessionmaker as _sm

_test_engine = _ce(
    "sqlite:///./test_superficies.db",
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=_test_engine)
_TestSession = _sm(bind=_test_engine)


def _override_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db
_MODULE_OVERRIDES = {get_db: _override_db}
client = TestClient(app, raise_server_exceptions=False)

# ── Helpers para generar tokens ───────────────────────────────────────────────

def _ejecutivo_token(rol: str = "ejecutivo", user_id: int = 999) -> str:
    """JWT firmado con SECRET_KEY, claim rol incluido."""
    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    return jwt.encode({"sub": str(user_id), "rol": rol, "exp": exp}, SECRET_KEY, ALGORITHM)


def _chat_token(conv_id: int = 1) -> str:
    """Token opaco firmado con CHAT_TOKEN_SECRET, tipo=sesion_chat."""
    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    return jwt.encode(
        {"sub": str(conv_id), "tipo": "sesion_chat", "exp": exp},
        CHAT_TOKEN_SECRET, ALGORITHM
    )


# =============================================================================
# TEST PRINCIPAL: test_superficies
# =============================================================================

def test_superficies():
    """
    Verifica que las dos superficies de API están correctamente segregadas.
    Un token válido de una superficie NO debe funcionar en la otra.
    """

    # ── 1. /api/consola/* sin ningún token → 401 ─────────────────────────────
    r = client.get("/api/consola/leads")
    assert r.status_code == 401, f"Sin token debe dar 401, dio {r.status_code}"

    # ── 2. /api/consola/* con token de chat (firmado con CHAT_TOKEN_SECRET) → 401
    #    La firma no coincide con SECRET_KEY → JWTError → 401
    chat_tok = _chat_token(conv_id=1)
    r = client.get("/api/consola/leads", headers={"Authorization": f"Bearer {chat_tok}"})
    assert r.status_code == 401, \
        f"Token de chat en consola debe dar 401, dio {r.status_code}: {r.text}"

    # ── 3. /api/consola/* con JWT válido pero rol != 'ejecutivo' → 403 ────────
    tok_sin_rol = _ejecutivo_token(rol="viewer")
    r = client.get("/api/consola/leads", headers={"Authorization": f"Bearer {tok_sin_rol}"})
    assert r.status_code == 403, \
        f"Rol incorrecto debe dar 403, dio {r.status_code}: {r.text}"

    # ── 4. /api/chat/* sin X-Session-Token → 401 ─────────────────────────────
    r = client.get("/api/chat/conversacion")
    assert r.status_code == 401, f"Sin session token debe dar 401, dio {r.status_code}"

    # ── 5. /api/chat/* con JWT ejecutivo como session token → 401 ────────────
    #    Firmado con SECRET_KEY, no con CHAT_TOKEN_SECRET → JWTError → 401
    ejec_tok = _ejecutivo_token()
    r = client.get("/api/chat/conversacion", headers={"X-Session-Token": ejec_tok})
    assert r.status_code == 401, \
        f"JWT ejecutivo en chat debe dar 401, dio {r.status_code}: {r.text}"

    # ── 6. /api/chat/* con token persistido de conversación abierta → 200 ────
    db = _TestSession()
    marcador = uuid4().hex
    user = User(name="Chat test", email=f"chat-{marcador}@local", password="hash")
    db.add(user)
    db.flush()
    lead = Lead(
        name="Lead chat", email=f"lead-{marcador}@local", phone="0000000000",
        lead_type="test", company="Test", interest="Test", budget=0,
        urgency="baja", lead_score=0, status="nuevo", user_id=user.id,
    )
    db.add(lead)
    db.flush()
    conv = Conversation(lead_id=lead.id)
    db.add(conv)
    db.flush()
    db.add(Message(sender="lead", content="Mensaje de prueba", conversation_id=conv.id))
    chat_tok_ok = _chat_token(conv_id=conv.id)
    conv.token_sesion = chat_tok_ok
    db.commit()
    conv_id = conv.id
    db.close()

    r = client.get("/api/chat/conversacion", headers={"X-Session-Token": chat_tok_ok})
    assert r.status_code == 200, \
        f"Token de sesión válido debe dar 200, dio {r.status_code}: {r.text}"
    data = r.json()
    assert data["id"] == conv_id, "El conv_id debe venir del token, no de la URL"
    assert data["messages"][0]["content"] == "Mensaje de prueba"

    # Un JWT correctamente firmado, pero distinto del token persistido, no sirve.
    token_distinto = jwt.encode(
        {
            "sub": str(conv_id),
            "tipo": "sesion_chat",
            "nonce": "token-distinto",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        CHAT_TOKEN_SECRET,
        ALGORITHM,
    )
    r = client.get("/api/chat/conversacion", headers={"X-Session-Token": token_distinto})
    assert r.status_code == 401, \
        f"Token no persistido debe dar 401, dio {r.status_code}: {r.text}"

    # ── 7. /api/chat/* con token expirado → 401 ───────────────────────────────
    exp_past = datetime.now(timezone.utc) - timedelta(hours=1)
    tok_expirado = jwt.encode(
        {"sub": "1", "tipo": "sesion_chat", "exp": exp_past},
        CHAT_TOKEN_SECRET, ALGORITHM
    )
    r = client.get("/api/chat/conversacion", headers={"X-Session-Token": tok_expirado})
    assert r.status_code == 401, \
        f"Token expirado debe dar 401, dio {r.status_code}"

    print("✅ test_superficies: todas las verificaciones de segregación pasaron.")


# ── Tests adicionales de cobertura ────────────────────────────────────────────

def test_chat_no_expone_lead_id_en_url():
    """No debe existir ningún endpoint de chat que acepte lead_id arbitrario."""
    from fastapi.routing import APIRoute
    chat_routes = [
        r.path for r in app.routes
        if isinstance(r, APIRoute) and r.path.startswith("/api/chat/")
    ]
    for path in chat_routes:
        assert "{lead_id}" not in path, \
            f"Endpoint público {path} expone lead_id arbitrario — viola segregación."


def test_consola_no_acepta_session_token_como_bearer():
    """Un token de sesión de chat NO debe funcionar como Bearer en consola,
    aunque tenga el formato correcto de JWT.
    """
    chat_tok = _chat_token(conv_id=5)
    # Intento usarlo como Bearer en consola (firma diferente)
    r = client.get("/api/consola/leads", headers={"Authorization": f"Bearer {chat_tok}"})
    assert r.status_code in (401, 403), \
        f"Token de chat como Bearer en consola debe dar 401/403, dio {r.status_code}"
