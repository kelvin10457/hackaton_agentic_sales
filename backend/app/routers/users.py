from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import hash_password, get_db, requiere_rol_ejecutivo
from models import User
from schemas import UserCreate, UserRead, UserUpdate, UserStats

router = APIRouter(prefix="/users", tags=["Users"])


# ── CRUD ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere_rol_ejecutivo)])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado."
        )
    data = payload.model_dump()
    data["password"] = hash_password(data["password"])
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/", response_model=list[UserRead], dependencies=[Depends(requiere_rol_ejecutivo)])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/{user_id}/stats", response_model=UserStats, dependencies=[Depends(requiere_rol_ejecutivo)])
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """Dashboard de estadísticas: leads por estado, conversaciones activas y mensajes totales."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    total_leads = len(user.leads)
    leads_by_status: dict[str, int] = {}
    active_conversations = 0
    total_messages = 0

    for lead in user.leads:
        leads_by_status[lead.status] = leads_by_status.get(lead.status, 0) + 1
        for conv in lead.conversations:
            if conv.ended_at is None:
                active_conversations += 1
            total_messages += len(conv.messages)

    avg = round(total_messages / total_leads, 1) if total_leads > 0 else 0.0

    return UserStats(
        total_leads=total_leads,
        leads_by_status=leads_by_status,
        active_conversations=active_conversations,
        total_messages_sent=total_messages,
        avg_messages_per_lead=avg,
    )


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(requiere_rol_ejecutivo)])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return user


@router.patch("/{user_id}", response_model=UserRead, dependencies=[Depends(requiere_rol_ejecutivo)])
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        data["password"] = hash_password(data["password"])
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(requiere_rol_ejecutivo)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    db.delete(user)
    db.commit()
