# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
# pyrefly: ignore [missing-import]
from sqlalchemy import text

from app.database import engine, Base
import app.models as models

Base.metadata.create_all(bind=engine)

from app.routers import (
    auth,
    users,
    leads,
    conversations,
    messages,
    consola,
    chat,
)

app = FastAPI()

# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para el hackathon permitimos todo, o puedes restringir a ["http://localhost:3000", "https://tudominio.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leads.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(consola.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "API funcionando"}


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

    return {"ok": True}
