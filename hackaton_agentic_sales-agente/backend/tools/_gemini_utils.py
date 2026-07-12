"""
tools/_gemini_utils.py — Reintentos automáticos para llamadas a Gemini.

Los errores 503 (servidor saturado) y 429 (límite de cuota momentáneo) son
temporales — reintentar unos segundos después casi siempre funciona. Esto
NO es para tapar errores reales (como una key inválida, ese sí debe fallar
inmediatamente y decírtelo).
"""
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def con_reintentos(func: Callable[[], T], intentos: int = 3, espera_inicial: float = 2.0) -> T:
    """
    Ejecuta func() y reintenta si Gemini devuelve un error temporal
    (servidor saturado o límite de cuota). Espera con backoff exponencial
    (2s, 4s, 8s...) entre cada intento.
    """
    from google.genai import errors as genai_errors

    ultimo_error = None
    espera = espera_inicial

    for intento in range(1, intentos + 1):
        try:
            return func()
        except genai_errors.ServerError as e:
            ultimo_error = e
            if intento < intentos:
                print(f"  (Gemini está saturado, reintentando en {espera:.0f}s... intento {intento}/{intentos})")
                time.sleep(espera)
                espera *= 2
        except genai_errors.ClientError as e:
            codigo = None
            if hasattr(e, "details") and isinstance(e.details, dict):
                codigo = e.details.get("error", {}).get("code")
            if codigo == 429 and intento < intentos:
                ultimo_error = e
                print(f"  (límite de cuota momentáneo, reintentando en {espera:.0f}s...)")
                time.sleep(espera)
                espera *= 2
            else:
                raise  # cualquier otro ClientError (ej. key inválida) falla de una vez

    raise ultimo_error
