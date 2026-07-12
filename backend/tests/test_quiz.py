"""test_quiz — Mismas respuestas -> mismo perfil_riesgo. Cero LLM."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.obtener_quiz import calcular_perfil_riesgo, obtener_preguntas_quiz


def test_hay_3_preguntas():
    preguntas = obtener_preguntas_quiz()
    assert len(preguntas) == 3


def test_perfil_conservador():
    # todas las respuestas más cautelosas -> 0 puntos
    assert calcular_perfil_riesgo([0, 0, 0]) == "conservador"


def test_perfil_moderado():
    # 1+1+1 = 3 puntos -> moderado
    assert calcular_perfil_riesgo([1, 1, 1]) == "moderado"


def test_perfil_agresivo():
    # todas las más arriesgadas -> 6 puntos
    assert calcular_perfil_riesgo([2, 2, 2]) == "agresivo"


def test_mismas_respuestas_mismo_perfil():
    r = [1, 0, 2]
    assert calcular_perfil_riesgo(r) == calcular_perfil_riesgo(r)


def test_numero_incorrecto_de_respuestas_falla():
    import pytest
    with pytest.raises(ValueError):
        calcular_perfil_riesgo([1, 1])
