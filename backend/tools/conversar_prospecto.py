"""
tools/conversar_prospecto.py — Herramienta para la conversación libre B2B/B2C.
"""
from pathlib import Path
from schemas.conversacion_prospecto import RespuestaConversacionProspecto

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "conversar_prospecto.md"

def _cargar_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")

def conversar_prospecto(historial: list[dict]) -> RespuestaConversacionProspecto:
    """
    Llama al LLM (OpenRouter) para que genere la respuesta consultiva
    y evalúe el estado actual del lead.
    """
    # Formatear historial omitiendo el mensaje inicial "saludo" del agente
    # si está muy lejos, pero generalmente es bueno pasarlo todo.
    historial_texto = "\n".join(
        f"{m['rol']}: {m['texto']}" for m in historial
    )

    prompt = _cargar_prompt().replace("{historial}", historial_texto)

    from tools._openrouter_utils import llamar_openrouter
    return llamar_openrouter(prompt, RespuestaConversacionProspecto)
