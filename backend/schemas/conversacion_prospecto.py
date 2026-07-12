"""
schemas/conversacion_prospecto.py — Schema para el nodo de consultoría libre.
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional


class EvaluaciónLead(BaseModel):
    nivel_interes: int = Field(
        description="Nivel de interés del usuario del 1 al 10, según su participación y respuestas."
    )
    presupuesto: Literal["Alto", "Medio", "Bajo", "Desconocido"] = Field(
        description="Nivel de presupuesto estimado o mencionado por el usuario."
    )
    urgencia: Literal["Alta", "Media", "Baja"] = Field(
        description="Qué tan urgente es para el usuario resolver el problema."
    )


class RespuestaConversacionProspecto(BaseModel):
    mensaje_agente: str = Field(
        description="El texto de la respuesta que se le mostrará al usuario. Debe ser natural, empático y consultivo."
    )
    tipo_prospecto_detectado: Literal["B2B", "B2C", "DESCONOCIDO"] = Field(
        description="El tipo de prospecto actual basado en la conversación."
    )
    listo_para_asesor: bool = Field(
        description="True si ya se entendió completamente el problema del cliente y se le puede recomendar un asesor. False si aún necesitas explorar más."
    )
    asesor_sugerido: Optional[str] = Field(
        default=None,
        description="Si 'listo_para_asesor' es True, indica el nombre del rol del asesor (ej: 'Asesor de optimización de procesos', 'Asesor patrimonial')."
    )
    evaluacion_lead: Optional[EvaluaciónLead] = Field(
        default=None,
        description="Si 'listo_para_asesor' es True, extrae las variables del lead (interés, presupuesto, urgencia)."
    )
