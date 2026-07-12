"""
T2 · obtener_preguntas — CÓDIGO PURO. Biblia §8, §11.

Criterio de aceptación 1.1: el agente "aplica preguntas CONFIGURABLES".

FIJO: **todas** las preguntas viven en `config/preguntas_b2c.yaml` y
`config/preguntas_b2b.yaml`. Ninguna está hardcodeada en un prompt. Cambiar una
pregunta es editar un YAML — no tocar código ni reentrenar nada. Eso es lo que
la rúbrica llama "configurables", y es lo que se enseña 1 segundo en el vídeo.

Cero LLM: el grafo decide QUÉ preguntar; el modelo solo extrae señales de la
respuesta (T3). Y nunca se repite una pregunta ya contestada (Biblia §7).
"""
from pathlib import Path

import yaml

_CONFIG_DIR = Path(__file__).parent.parent / "config"

# Cache: los YAML se leen una vez por proceso.
_cache: dict[str, dict] = {}


def _cargar(tipo: str) -> dict:
    """Carga config/preguntas_{b2c|b2b}.yaml."""
    clave = "b2b" if str(tipo).lower() == "b2b" else "b2c"
    if clave not in _cache:
        ruta = _CONFIG_DIR / f"preguntas_{clave}.yaml"
        with open(ruta, "r", encoding="utf-8") as f:
            _cache[clave] = yaml.safe_load(f) or {}
    return _cache[clave]


def obtener_preguntas(tipo: str, momento: str = "calificacion") -> list[dict]:
    """Devuelve las preguntas configuradas para un tipo de prospecto.

    `momento`: "calificacion" | "identificacion".
    """
    config = _cargar(tipo)
    return list(config.get(momento, []))


def siguiente_pregunta(
    tipo: str,
    senales: dict,
    ya_preguntadas: set[str] | None = None,
) -> dict | None:
    """La siguiente pregunta de calificación pendiente, en el orden del YAML.

    Una pregunta se salta si:
      1. La señal que alimenta (`senal:`) ya tiene valor → ya la contestó.
      2. Ya se le preguntó una vez → **no se insiste**.

    (2) no es cosmético: garantiza que la conversación SIEMPRE avanza. Si el
    prospecto responde algo que el extractor determinista no logra mapear
    ("mmm, no sé"), el agente pasa a la siguiente pregunta en vez de quedarse
    en bucle repitiendo la misma. Nunca se repite una pregunta ya hecha
    (Biblia §7 · Contrato 4 de R3).

    Devuelve None cuando ya no queda nada por preguntar.
    """
    ya_preguntadas = ya_preguntadas or set()

    for pregunta in obtener_preguntas(tipo, "calificacion"):
        senal = pregunta.get("senal")
        if not senal:
            continue
        valor = senales.get(senal)
        # None o "" = sin evidencia todavía.
        # Ojo: 0 y False SÍ son respuestas válidas, no se re-preguntan.
        respondida = valor is not None and valor != ""
        if respondida or pregunta["texto"] in ya_preguntadas:
            continue
        return pregunta
    return None


def ids_respondidos(tipo: str, senales: dict) -> list[str]:
    """IDs de las preguntas de calificación ya contestadas (para la bitácora)."""
    return [
        p["id"]
        for p in obtener_preguntas(tipo, "calificacion")
        if p.get("senal") and senales.get(p["senal"]) not in (None, "")
    ]
