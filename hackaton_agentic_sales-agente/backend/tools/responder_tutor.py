"""
tools/responder_tutor.py — El TutorIA responde preguntas educativas.

Usa los documentos encontrados por buscar_conocimiento para generar
una respuesta fundamentada y citando la fuente. Si no hay documentos
relevantes, responde que no tiene información sobre ese tema.
"""
from pathlib import Path
from typing import Optional

from tools.buscar_conocimiento import buscar_conocimiento, formatear_documentos_para_prompt

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "tutor_responder.md"


def _cargar_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def responder_tutor(
    pregunta: str,
    historial: list[dict],
) -> dict:
    """
    Genera una respuesta educativa del TutorIA.

    Returns:
        {
            "respuesta": str,       # texto de la respuesta al usuario
            "fuentes": list[str],   # IDs de documentos usados (ej: ["FA-003"])
            "tema": str,            # tema principal detectado (para señal comercial)
            "documentos_usados": int
        }
    """
    # 1. Buscar documentos relevantes
    docs = buscar_conocimiento(pregunta, top_k=3)

    # 2. Formatear el historial para el prompt
    historial_texto = "\n".join(
        f"{m['rol']}: {m['texto']}" for m in historial[-6:]  # últimos 6 mensajes
    )

    # 3. Formatear los documentos para el prompt
    documentos_texto = formatear_documentos_para_prompt(docs)

    # 4. Construir el prompt
    prompt = _cargar_prompt().format(
        documentos=documentos_texto,
        historial=historial_texto,
        pregunta=pregunta,
    )

    # 5. Llamar al LLM
    from tools._openrouter_utils import llamar_texto_libre
    respuesta = llamar_texto_libre(prompt)

    fuentes = [doc["id"] for doc in docs]
    tema = docs[0]["titulo"] if docs else "general"

    return {
        "respuesta": respuesta,
        "fuentes": fuentes,
        "tema": tema,
        "documentos_usados": len(docs),
    }
