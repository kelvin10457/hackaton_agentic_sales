"""Resultado de T1 · clasificar_prospecto (Biblia §11: {tipo, confianza})."""
from typing import Literal
from pydantic import BaseModel, Field


class ClasificacionProspecto(BaseModel):
    tipo: Literal["B2C", "B2B"]
    confianza: float = Field(ge=0.0, le=1.0)
