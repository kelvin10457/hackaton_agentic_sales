"""
T1 · clasificar_prospecto — Biblia §11, Manual R1 §5 y §9.

Usa DeepSeek via OpenRouter para clasificar B2B vs B2C.
Regla de oro #2 (Manual R1): salida tipada o no hay salida.

Diseño importante: la llamada real al LLM vive en su propia función
(_llamar_llm) para poder INYECTAR una función distinta en los tests.
Así el grafo se puede probar sin la API real (requisito test_agente_mock_llm
de la Biblia §20/§19).
"""
import os
from pathlib import Path
from typing import Callable, Optional

from schemas.clasificacion import ClasificacionProspecto

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "clasificar_prospecto.md"


def _cargar_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _llamar_llm(prompt: str) -> ClasificacionProspecto:
    """Llamada real a DeepSeek via OpenRouter. NO se testea directamente:
    se inyecta una función distinta en los tests (patrón inalterado)."""
    from tools._openrouter_utils import llamar_openrouter
    return llamar_openrouter(prompt, ClasificacionProspecto)


def clasificar_prospecto(
    historial: list[str],
    llamar_llm: Optional[Callable[[str], ClasificacionProspecto]] = None,
) -> ClasificacionProspecto:
    """
    T1. historial: lista de strings con los mensajes del usuario (no del agente).
    llamar_llm: inyectable para tests. Por defecto llama a DeepSeek via OpenRouter.
    """
    prompt = _cargar_prompt().format(historial="\n".join(historial))

    llamar = llamar_llm or _llamar_llm
    resultado = llamar(prompt)

    if not isinstance(resultado, ClasificacionProspecto):
        raise ValueError(
            "La salida del LLM no cumplió el schema ClasificacionProspecto. "
            "Salida rechazada (regla de oro #2: salida tipada o no hay salida)."
        )

    return resultado
