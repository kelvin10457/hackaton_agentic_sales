"""
T3 · extraer_senales — Biblia §4.2, §11, Manual R1 §5 y §9.

★ La herramienta más importante del núcleo: el LLM SOLO llena este objeto.
No calcula nada, no puntúa nada. Eso lo hace tools/calcular_score.py, código
puro (Regla de Oro #1).

Mismo diseño que T1: la llamada real al LLM está aislada en su propia
función para poder inyectar un mock en los tests.
"""
import os
from pathlib import Path
from typing import Callable, Literal, Optional

from schemas.senales import Senales

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "extraer_senales.md"

TipoProspecto = Literal["B2C", "B2B"]


def _cargar_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _llamar_llm(prompt: str) -> Senales:
    """Llamada real a DeepSeek via OpenRouter. NO se testea directamente:
    se inyecta una función distinta en los tests."""
    from tools._openrouter_utils import llamar_openrouter
    return llamar_openrouter(prompt, Senales)


def extraer_senales(
    historial: list[str],
    tipo: TipoProspecto,
    llamar_llm: Optional[Callable[[str], Senales]] = None,
) -> Senales:
    """
    T3. historial: mensajes del usuario. tipo: B2C o B2B (ya clasificado por T1).
    llamar_llm: inyectable para tests.
    """
    prompt = _cargar_prompt().format(tipo=tipo, historial="\n".join(historial))

    llamar = llamar_llm or _llamar_llm
    resultado = llamar(prompt)

    if not isinstance(resultado, Senales):
        raise ValueError(
            "La salida del LLM no cumplió el schema Senales. "
            "Salida rechazada (regla de oro #2: salida tipada o no hay salida)."
        )

    return resultado
