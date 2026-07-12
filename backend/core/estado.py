"""
core/estado.py — El estado de la conversación (Biblia §4.8, Manual R1 §7).

Esto es lo que viaja de nodo a nodo en el grafo. Cada nodo recibe este
estado, lo modifica, y lo devuelve. LangGraph se encarga de persistirlo
entre turnos (con el checkpointer).
"""
from typing import Literal, Optional, TypedDict

from schemas.senales import Senales, TipoProspecto
from schemas.score import Score


class EstadoConversacion(TypedDict, total=False):
    # ---- Identidad de la conversación ----
    conversacion_id: str

    # ---- Historial ----
    historial: list[dict]  # [{"rol": "usuario"|"agente", "texto": "...", "fuentes": [...]}]

    # ---- Máquina de estados (Biblia §7) ----
    estado_flujo: Literal[
        "saludo",
        "deteccion_modo",
        "conversacion_prospecto",
        "identificacion_2",
        "consentimiento",
        "cierre",
        "tutor",
        "tutor_registro",
    ]

    # ---- Datos del lead que se van llenando ----
    tipo: Optional[TipoProspecto]           # B2B | B2C | None (aún no clasificado)
    estado_identificacion: Literal[
        "anonimo", "identificado", "verificado", "descartado", "abandonado"
    ]
    nombre: Optional[str]
    email: Optional[str]

    senales: Senales
    score: Optional[Score]
    ruta_sugerida: Optional[str]

    quiz_completado: bool
    quiz_respuestas: list[int]
    perfil_riesgo: Optional[str]

    consentimiento_tratamiento_datos: bool
    consentimiento_comunicaciones: bool

    preguntas_respondidas: list[str]  # para no repetir preguntas (§4.8)

    # ---- Resultados del Prospecto Libre ----
    asesor_sugerido: Optional[str]
    prioridad_lead: Optional[Literal["Alta", "Media", "Baja"]]

    # ---- Modo de conversación ----
    modo: Optional[Literal["PROSPECTO", "TUTOR"]]  # detectado en deteccion_modo
    tema_interes: Optional[str]                     # tema del tutor (señal comercial)


def estado_inicial(conversacion_id: str) -> EstadoConversacion:
    """Fábrica del estado en blanco para una conversación nueva."""
    return EstadoConversacion(
        conversacion_id=conversacion_id,
        historial=[],
        estado_flujo="saludo",
        tipo=None,
        estado_identificacion="anonimo",
        nombre=None,
        email=None,
        senales=Senales(),
        score=None,
        ruta_sugerida=None,
        quiz_completado=False,
        quiz_respuestas=[],
        perfil_riesgo=None,
        consentimiento_tratamiento_datos=False,
        consentimiento_comunicaciones=False,
        preguntas_respondidas=[],
        modo=None,
        tema_interes=None,
    )
