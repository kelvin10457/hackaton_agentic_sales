"""
generar_pregunta_calificacion — decide la siguiente pregunta dinámica de
calificación, o si ya hay suficiente información para pasar a scoring.

Mismo patrón que T1/T3: la llamada real al LLM está aislada para poder
inyectar un mock en los tests.
"""
import os
from pathlib import Path
from typing import Callable, Optional

from schemas.decision_conversacion import DecisionConversacion

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "conversar_calificacion.md"


def _cargar_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _llamar_llm(prompt: str) -> DecisionConversacion:
    """Llamada real a DeepSeek via OpenRouter. NO se testea directamente:
    se inyecta una función distinta en los tests."""
    from tools._openrouter_utils import llamar_openrouter
    return llamar_openrouter(prompt, DecisionConversacion)


def generar_pregunta_calificacion(
    tipo: str,
    senales_json: str,
    historial: list[dict],
    preguntas_config: list[dict],
    llamar_llm: Optional[Callable[[str], DecisionConversacion]] = None,
) -> DecisionConversacion:
    historial_texto = "\n".join(f"{m['rol']}: {m['texto']}" for m in historial)
    preguntas_texto = "\n".join(
        f"- ({p.get('senal', p.get('id'))}) {p['texto']}" for p in preguntas_config
    )

    prompt = _cargar_prompt().format(
        tipo=tipo,
        senales_json=senales_json,
        preguntas_config=preguntas_texto,
        historial=historial_texto,
    )

    llamar = llamar_llm or _llamar_llm
    resultado = llamar(prompt)

    if not isinstance(resultado, DecisionConversacion):
        raise ValueError("La salida del LLM no cumplió el schema DecisionConversacion.")

    return resultado
