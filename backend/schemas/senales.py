"""
Señales — lo único que el LLM produce (Biblia §4.2).
⚠ Si no hay evidencia, el campo es None. Adivinar está PROHIBIDO.
Este schema es PROVISIONAL: cuando R2 publique schemas/ oficial, se alinean.
"""
from typing import Literal, Optional
from pydantic import BaseModel


class Senales(BaseModel):
    # ---- Comunes ----
    objetivo: Optional[
        Literal["aprender", "invertir", "capacitar_equipo", "licenciar", "otro"]
    ] = None
    horizonte: Optional[Literal["inmediato", "1-3m", "3-6m", "mas_6m"]] = None
    pidio_asesor: bool = False
    mensajes_intercambiados: int = 0       # lo cuenta el código, no el LLM
    completo_quiz: bool = False            # lo marca el código, no el LLM

    # ---- Solo B2C ----
    monto_declarado_usd: Optional[float] = None
    experiencia_inversion: Optional[
        Literal["ninguna", "basica", "intermedia", "avanzada"]
    ] = None
    perfil_riesgo: Optional[Literal["conservador", "moderado", "agresivo"]] = None

    # ---- Solo B2B ----
    num_colaboradores: Optional[int] = None
    presupuesto_capacitacion_usd: Optional[float] = None
    es_decisor: Optional[bool] = None
    solicito_propuesta: bool = False

    # ---- Identidad (necesarias para el cálculo de "perfil") ----
    cedula_valida: bool = False
    ruc_valido: bool = False
    email_valido: bool = False
    email_corporativo: bool = False


TipoProspecto = Literal["B2C", "B2B"]
