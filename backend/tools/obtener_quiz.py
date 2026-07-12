"""
T7 · obtener_quiz — CÓDIGO PURO. Biblia §6.1.

REGLA DE ORO #3: el quiz NO lo genera la IA.
3 preguntas fijas + rúbrica fija. Cero LLM. Mismas respuestas -> mismo perfil_riesgo.
"""
from pathlib import Path
from typing import Literal
import yaml

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "quiz_perfil_riesgo.yaml"

PerfilRiesgo = Literal["conservador", "moderado", "agresivo"]


def _cargar_quiz() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def obtener_preguntas_quiz() -> list[dict]:
    """Devuelve las 3 preguntas fijas para mostrarlas en el chat (consume R3)."""
    return _cargar_quiz()["preguntas"]


def calcular_perfil_riesgo(respuestas: list[int]) -> PerfilRiesgo:
    """
    respuestas: lista de 3 índices (0,1,2) elegidos por el usuario, uno por pregunta,
    en el mismo orden que las preguntas del yaml.
    """
    quiz = _cargar_quiz()
    preguntas = quiz["preguntas"]

    if len(respuestas) != len(preguntas):
        raise ValueError(f"Se esperaban {len(preguntas)} respuestas, llegaron {len(respuestas)}")

    total_puntos = 0
    for pregunta, idx_elegido in zip(preguntas, respuestas):
        opciones = pregunta["opciones"]
        if not (0 <= idx_elegido < len(opciones)):
            raise ValueError(f"Índice de opción inválido: {idx_elegido}")
        total_puntos += opciones[idx_elegido]["puntos"]

    for banda in quiz["rubrica"]:
        if banda["min"] <= total_puntos <= banda["max"]:
            return banda["perfil"]

    raise ValueError(f"Puntaje {total_puntos} no cae en ninguna banda de la rúbrica")
