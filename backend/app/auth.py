"""
Utilidades de autenticación: hashing de contraseñas y JWT.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import bcrypt

from app.database import SessionLocal
from app.models import Conversation, User

import os
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────────────────────

SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

# ── Chat session token (superficie pública /api/chat/*) ───────────────────────
CHAT_TOKEN_SECRET: str = os.getenv("CHAT_TOKEN_SECRET", "chat-changeme")
CHAT_TOKEN_EXPIRE_HOURS: int = int(os.getenv("CHAT_TOKEN_EXPIRE_HOURS", "24"))

def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))


# ── JWT ───────────────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_session_token(conversacion_id: int) -> str:
    """Crea un token opaco de sesión atado a una sola conversación.
    Firmado con CHAT_TOKEN_SECRET, diferente al SECRET_KEY de usuarios.
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=CHAT_TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(conversacion_id), "tipo": "sesion_chat", "exp": expire},
        CHAT_TOKEN_SECRET,
        algorithm=ALGORITHM,
    )


# ── Dependency ────────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


# ── Dependencias de superficie ────────────────────────────────────────────────

def requiere_rol_ejecutivo(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Dependency para /api/consola/*: JWT Bearer con claim rol='ejecutivo'.
    Verifica el claim ANTES de consultar la BD para poder rechazar con 403
    sin exponer información de existencia de usuarios.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        rol: str | None = payload.get("rol")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Verificar rol ANTES de tocar la BD
    if rol != "ejecutivo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol 'ejecutivo'.",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def requiere_token_sesion(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
    db: Session = Depends(get_db),
) -> int:
    """Dependency para /api/chat/*: token opaco firmado con CHAT_TOKEN_SECRET.
    Devuelve conversacion_id extraído del token.
    El endpoint NUNCA acepta un conversacion_id arbitrario del cliente.
    """
    if not x_session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere el header X-Session-Token.",
        )
    try:
        payload = jwt.decode(x_session_token, CHAT_TOKEN_SECRET, algorithms=[ALGORITHM])
        tipo = payload.get("tipo")
        conv_id = payload.get("sub")
        if tipo != "sesion_chat" or conv_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de sesión inválido.",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido o expirado.",
        )
    conversacion = db.query(Conversation).filter(Conversation.id == int(conv_id)).first()
    if (
        conversacion is None
        or conversacion.ended_at is not None
        or conversacion.token_sesion != x_session_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido o la conversación está cerrada.",
        )

    return int(conv_id)
