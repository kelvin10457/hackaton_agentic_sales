"""test_reintentos — confirma que con_reintentos() reintenta ante 503/429
y no ante otros errores (ej. key inválida)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock

from tools._gemini_utils import con_reintentos


class _ServerErrorFalso(Exception):
    pass


class _ClientErrorFalso(Exception):
    def __init__(self, codigo):
        self.details = {"error": {"code": codigo}}


def test_reintenta_y_al_final_funciona(monkeypatch):
    from google.genai import errors as genai_errors

    monkeypatch.setattr(genai_errors, "ServerError", _ServerErrorFalso)
    monkeypatch.setattr(genai_errors, "ClientError", _ClientErrorFalso)
    monkeypatch.setattr("time.sleep", lambda s: None)  # no esperar de verdad en el test

    llamadas = {"n": 0}

    def func_que_falla_2_veces():
        llamadas["n"] += 1
        if llamadas["n"] < 3:
            raise _ServerErrorFalso("saturado")
        return "funcionó"

    resultado = con_reintentos(func_que_falla_2_veces, intentos=3, espera_inicial=0.01)
    assert resultado == "funcionó"
    assert llamadas["n"] == 3


def test_no_reintenta_error_no_temporal(monkeypatch):
    from google.genai import errors as genai_errors

    monkeypatch.setattr(genai_errors, "ServerError", _ServerErrorFalso)
    monkeypatch.setattr(genai_errors, "ClientError", _ClientErrorFalso)

    def func_con_key_invalida():
        raise _ClientErrorFalso(400)  # 400, no 429 -> no debe reintentar

    with pytest.raises(_ClientErrorFalso):
        con_reintentos(func_con_key_invalida, intentos=3, espera_inicial=0.01)


def test_se_agota_reintentos_y_relanza(monkeypatch):
    from google.genai import errors as genai_errors

    monkeypatch.setattr(genai_errors, "ServerError", _ServerErrorFalso)
    monkeypatch.setattr(genai_errors, "ClientError", _ClientErrorFalso)
    monkeypatch.setattr("time.sleep", lambda s: None)

    def siempre_falla():
        raise _ServerErrorFalso("saturado siempre")

    with pytest.raises(_ServerErrorFalso):
        con_reintentos(siempre_falla, intentos=3, espera_inicial=0.01)
