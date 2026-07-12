"""
schemas/quiz_tutor.py — Schema del quiz diagnóstico del Tutor IA.
"""
from pydantic import BaseModel
from typing import Literal


class PreguntaQuiz(BaseModel):
    pregunta: str
    opciones: list[str]      # exactamente 3 opciones
    correcta: int            # índice de la correcta: 0, 1 o 2
    explicacion: str         # por qué esa opción es correcta


class QuizTutor(BaseModel):
    tema: str
    preguntas: list[PreguntaQuiz]  # siempre 3 preguntas
