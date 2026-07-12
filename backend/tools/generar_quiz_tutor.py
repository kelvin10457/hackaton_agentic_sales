"""
tools/generar_quiz_tutor.py — Genera un quiz diagnóstico de 3 preguntas
sobre el tema que el usuario eligió en el modo Tutor.

El LLM genera las preguntas en tiempo real basándose en el documento
de knowledge relevante al tema.
"""
from pathlib import Path
from schemas.quiz_tutor import QuizTutor, PreguntaQuiz
from tools.buscar_conocimiento import buscar_conocimiento

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "tutor_quiz.md"


def _cargar_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def generar_quiz_tutor(tema: str) -> QuizTutor:
    """
    Genera un quiz de 3 preguntas de opción múltiple sobre el tema dado.
    Busca el documento más relevante en knowledge/ y usa su contenido.

    Si no encuentra documento relevante, devuelve preguntas genéricas
    sobre finanzas personales.
    """
    # Buscar el documento más relevante para el tema
    docs = buscar_conocimiento(tema, top_k=1)

    if docs:
        doc = docs[0]
        contenido = doc["contenido"]
        titulo = doc["titulo"]
    else:
        # Fallback genérico si no hay documento específico
        contenido = (
            "Finanzas personales: ahorro, inversión, presupuesto, "
            "fondo de emergencia, interés compuesto, perfil de riesgo."
        )
        titulo = "Finanzas personales"

    prompt = _cargar_prompt().format(
        tema=titulo,
        contenido=contenido,
    )

    from tools._openrouter_utils import llamar_openrouter
    return llamar_openrouter(prompt, QuizTutor)
