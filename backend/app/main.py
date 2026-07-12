from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models

from routers import users, leads, conversations, messages, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agentic Sales API", version="1.0.0")

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # En producción reemplaza con tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leads.router)
app.include_router(conversations.router)
app.include_router(messages.router)


@app.get("/")
def root():
    return {"message": "API funcionando"}