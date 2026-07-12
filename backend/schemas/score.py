"""Score — nunca un número opaco (Biblia §4.3)."""
from typing import Literal
from pydantic import BaseModel


class Score(BaseModel):
    interes: int
    presupuesto: int
    perfil: int
    urgencia: int
    total: int
    banda: Literal["frio", "tibio", "caliente"]
    justificacion: str
    version_motor: str = "1.0"
