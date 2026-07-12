"""
tools/_openrouter_utils.py — Llamada compartida a OpenRouter via SDK de OpenAI.

OpenRouter expone una API 100% compatible con OpenAI, por lo que usamos
el SDK `openai` apuntando a https://openrouter.ai/api/v1.

Modelo usado: deepseek/deepseek-chat-v3-0324
  - Calidad equivalente a GPT-4o para tareas de clasificación/extracción.
"""
import json
import os
import time
from typing import Callable, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_MODELO = "deepseek/deepseek-chat-v3-0324"
_BASE_URL = "https://openrouter.ai/api/v1"


def _get_client():
    """Devuelve un cliente OpenAI apuntando a OpenRouter."""
    from openai import OpenAI

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta OPENROUTER_API_KEY. Agrégala en tu archivo .env"
        )
    return OpenAI(
        api_key=api_key,
        base_url=_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://futuro-academy.com",
            "X-Title": "Futuro Academy Agent",
        },
    )


def llamar_openrouter(prompt: str, schema: Type[T]) -> T:
    """
    Llama a DeepSeek via OpenRouter y devuelve una instancia del schema Pydantic.

    Estrategia de structured output:
      - Usamos JSON mode (response_format=json_object).
      - El schema Pydantic se incluye en el system prompt como JSON Schema.
      - El resultado se parsea y valida con model.model_validate().
    """
    client = _get_client()

    schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False, indent=2)

    system_prompt = (
        "Eres un asistente de extracción de información. "
        "SIEMPRE responde con un JSON válido que cumpla exactamente este schema:\n\n"
        f"{schema_json}\n\n"
        "No incluyas texto fuera del JSON. Solo devuelve el objeto JSON."
    )

    MAX_INTENTOS = 3
    for intento in range(MAX_INTENTOS):
        try:
            response = client.chat.completions.create(
                model=_MODELO,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # baja temperatura para respuestas más deterministas
                max_tokens=1500,  # límite para evitar error 402 en OpenRouter
            )
            contenido = response.choices[0].message.content
            if contenido.startswith("```json"):
                contenido = contenido[7:]
            if contenido.startswith("```"):
                contenido = contenido[3:]
            if contenido.endswith("```"):
                contenido = contenido[:-3]
            contenido = contenido.strip()
            
            data = json.loads(contenido)
            return schema.model_validate(data)

        except Exception as e:
            if intento < MAX_INTENTOS - 1:
                espera = 2 ** intento  # backoff exponencial: 1s, 2s
                print(f"  (error temporal, reintentando en {espera}s...)")
                time.sleep(espera)
            else:
                raise RuntimeError(
                    f"OpenRouter falló después de {MAX_INTENTOS} intentos: {e}"
                ) from e


def llamar_texto_libre(prompt: str, temperatura: float = 0.4) -> str:
    """
    Llama al LLM y devuelve texto libre (sin forzar JSON).
    Usada por el modo Tutor para respuestas educativas naturales.
    """
    client = _get_client()
    # temperatura mínima permitida por DeepSeek via OpenRouter
    temperatura = max(temperatura, 0.01)

    MAX_INTENTOS = 3
    for intento in range(MAX_INTENTOS):
        try:
            response = client.chat.completions.create(
                model=_MODELO,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperatura,
                max_tokens=1500,  # límite para evitar error 402 en OpenRouter
            )
            # Protección ante choices=None o content=None
            if not response.choices:
                raise ValueError("La API devolvió choices vacío")
            contenido = response.choices[0].message.content
            return contenido if contenido else ""

        except Exception as e:
            if intento < MAX_INTENTOS - 1:
                espera = 2 ** intento
                print(f"  (error temporal, reintentando en {espera}s...)")
                time.sleep(espera)
            else:
                raise RuntimeError(
                    f"OpenRouter falló después de {MAX_INTENTOS} intentos: {e}"
                ) from e
