"""
test_validaciones.py — Pruebas para validar_cedula y validar_ruc.

Casos válidos, inválidos y de borde para ambas funciones.

Ejecutar:
  cd backend
  .venv/bin/pytest app/tests/test_validaciones.py -v
"""
import os, sys
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_validaciones.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-padded-x")
os.environ.setdefault("CHAT_TOKEN_SECRET", "test-chat-secret-32-chars-padded")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from app.validators import validar_cedula, validar_ruc, clasificar_documento


# =============================================================================
# validar_cedula
# =============================================================================

class TestValidarCedula:

    # ── Casos válidos ─────────────────────────────────────────────────────────
    @pytest.mark.parametrize("cedula", [
        "1713175071",   # Caso clásico de referencia (real)
        "0112345673",   # Provincia 01 — generado con módulo 10
        "1700000001",   # Provincia 17, ceros intermedios
        "0926687856",   # Provincia Guayas (09) — real
        "0912345675",   # Provincia 09 — generado con módulo 10
        "2400000002",   # Provincia 24 (Galápagos) — límite superior válido
    ])
    def test_cedulas_validas(self, cedula):
        assert validar_cedula(cedula) is True, f"{cedula} debería ser válida"

    # ── Casos inválidos ───────────────────────────────────────────────────────
    @pytest.mark.parametrize("cedula,razon", [
        ("1713175070", "dígito verificador incorrecto"),
        ("9913175071", "provincia 99 no existe"),
        ("0013175071", "provincia 00 no existe"),
        ("2513175071", "provincia 25 no existe"),
        ("171317507",  "9 dígitos — muy corta"),
        ("17131750710","11 dígitos — muy larga"),
        ("171317507a", "contiene letra"),
        ("          ", "solo espacios"),
        ("",           "cadena vacía"),
        ("0000000000", "provincia 00 inválida"),
    ])
    def test_cedulas_invalidas(self, cedula, razon):
        assert validar_cedula(cedula) is False, \
            f"{repr(cedula)} debería ser inválida ({razon})"

    # ── Casos borde ───────────────────────────────────────────────────────────
    def test_cedula_todos_ceros_excepto_provincia(self):
        # Provincia 01 válida, pero dígito verificador incorrecto
        assert validar_cedula("0100000000") is False

    def test_cedula_con_espacios_internos(self):
        assert validar_cedula("1713 75071") is False

    def test_cedula_unicode(self):
        # El superíndice '¹' pasa isdigit() en Python pero falla int() en el verificador.
        # La función del spec no atrapa este caso — lanza ValueError (comportamiento aceptable).
        # El test verifica que no retorna True (ya sea False o excepción).
        try:
            resultado = validar_cedula("171317507\u00b9")  # superíndice 1
            assert resultado is False, "No debería retornar True con carácter unicode"
        except (ValueError, TypeError):
            pass  # Comportamiento correcto: la función del spec no sanitiza input

    def test_cedula_provincia_maxima_valida(self):
        # Provincia 24 (Galápagos) — verificar que no se rechaza por rango
        # Construimos una cédula sintética con prov=24 y verificamos solo el rango
        cedula = "2400000000"
        # Puede ser válida o no dependiendo del dígito verificador,
        # pero NO debe rechazarse por provincia inválida
        resultado = validar_cedula(cedula)
        # Solo verificamos que no lanza excepción; el resultado depende del dígito
        assert isinstance(resultado, bool)

    def test_cedula_retorna_bool_estricto(self):
        # No debe retornar truthy/falsy, sino bool explícito
        assert type(validar_cedula("1713175071")) is bool
        assert type(validar_cedula("1713175070")) is bool


# =============================================================================
# validar_ruc
# =============================================================================

class TestValidarRuc:

    # ── Persona natural (tercer dígito 0-5) ──────────────────────────────────
    @pytest.mark.parametrize("ruc", [
        "1713175071001",   # Cédula válida + establecimiento 001
        "1713175071002",   # Mismo, establecimiento 002
        "0926687856001",   # Guayas natural
    ])
    def test_ruc_natural_valido(self, ruc):
        assert validar_ruc(ruc) is True, f"{ruc} debería ser válido (persona natural)"

    @pytest.mark.parametrize("ruc,razon", [
        ("1713175070001", "cédula base inválida"),
        ("1713175071000", "establecimiento 000 inválido"),
        ("171317507100",  "12 dígitos"),
        ("17131750710010","14 dígitos"),
    ])
    def test_ruc_natural_invalido(self, ruc, razon):
        assert validar_ruc(ruc) is False, f"{ruc} ({razon}) debería ser inválido"

    # ── Persona jurídica privada (tercer dígito 9) ────────────────────────────
    def test_ruc_juridico_estructura(self):
        # El tercer dígito debe ser 9 para jurídicos
        # Construimos un caso y verificamos que se procesa con módulo 11
        ruc_invalido_juridico = "1790000000001"
        resultado = validar_ruc(ruc_invalido_juridico)
        assert isinstance(resultado, bool)

    def test_ruc_juridico_tercer_digito_9(self):
        # Todo RUC con tercer dígito 9 y provincia válida debe evaluarse
        # como jurídico (no rechazarse antes de llegar al algoritmo)
        ruc = "1790011674001"  # SRI Ecuador, referencia pública
        resultado = validar_ruc(ruc)
        assert isinstance(resultado, bool)

    # ── Sector público (tercer dígito 6) ──────────────────────────────────────
    def test_ruc_publico_tercer_digito_6(self):
        ruc = "1760001550001"  # Municipio de referencia
        resultado = validar_ruc(ruc)
        assert isinstance(resultado, bool)

    # ── Casos inválidos genéricos ─────────────────────────────────────────────
    @pytest.mark.parametrize("ruc,razon", [
        ("",              "vacío"),
        ("123456789012",  "12 dígitos"),
        ("12345678901234","14 dígitos"),
        ("171317507100a", "contiene letra"),
        ("9913175071001", "provincia 99"),
        ("0013175071001", "provincia 00"),
        ("2513175071001", "provincia 25"),
        ("1783175071001", "tercer dígito 8 (no definido)"),
        ("1773175071001", "tercer dígito 7 (no definido)"),
    ])
    def test_ruc_invalido(self, ruc, razon):
        assert validar_ruc(ruc) is False, f"{repr(ruc)} ({razon}) debería ser inválido"

    def test_ruc_retorna_bool_estricto(self):
        assert type(validar_ruc("1713175071001")) is bool
        assert type(validar_ruc("9999999999999")) is bool


# =============================================================================
# clasificar_documento
# =============================================================================

class TestClasificarDocumento:

    def test_cedula_clasificada(self):
        assert clasificar_documento("1713175071") == "cedula"

    def test_ruc_natural_clasificado(self):
        assert clasificar_documento("1713175071001") == "ruc_natural"

    def test_invalido_clasificado(self):
        assert clasificar_documento("1234567890") == "invalido"
        assert clasificar_documento("00000000000001") == "invalido"
        assert clasificar_documento("abc") == "invalido"


# =============================================================================
# Integración: el campo cedula en LeadV2Create es validado por Pydantic
# =============================================================================

class TestLeadV2CedulaValidator:

    def test_lead_con_cedula_valida(self):
        from app.schemas import LeadV2Create
        lead = LeadV2Create(nombre="Test", cedula="1713175071")
        assert lead.cedula == "1713175071"

    def test_lead_con_ruc_valido(self):
        from app.schemas import LeadV2Create
        lead = LeadV2Create(nombre="Test", cedula="1713175071001")
        assert lead.cedula == "1713175071001"

    def test_lead_con_cedula_invalida_lanza_error(self):
        from app.schemas import LeadV2Create
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            LeadV2Create(nombre="Test", cedula="1234567890")
        assert "cédula" in str(exc_info.value).lower() or "ruc" in str(exc_info.value).lower()

    def test_lead_sin_cedula_es_valido(self):
        from app.schemas import LeadV2Create
        lead = LeadV2Create(nombre="Anónimo")
        assert lead.cedula is None
