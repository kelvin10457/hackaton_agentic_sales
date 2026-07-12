"""Resultado de la decisión de conversación dinámica (siguiente pregunta o cierre de calificación)."""
from typing import Optional
from pydantic import BaseModel


class DecisionConversacion(BaseModel):
    listo_para_ruta: bool
    mensaje: str  # la pregunta natural a hacer, o el mensaje de transición si ya está listo
    campo_que_pregunta: Optional[str] = None  # para trazabilidad/auditoría
