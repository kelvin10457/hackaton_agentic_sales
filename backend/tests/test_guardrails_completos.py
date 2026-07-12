"""
Cobertura de las mallas nuevas del bloque de seguridad (Manual R1 §9):
G1-bis, G2, G5, G6, G7 y la fachada evaluar_entrada/evaluar_salida.
Todas son deterministas: no llaman al LLM.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.guardrails import (
    evaluar_entrada_usuario,
    evaluar_salida_agente,
    se_dispara_g1bis,
    se_dispara_g2,
    respuesta_g2,
    se_dispara_g5,
    se_dispara_g6,
    se_dispara_g7,
)


# ── G2 · Negativa honesta ─────────────────────────────────────────────────────

def test_g2_se_dispara_con_rag_vacio():
    assert se_dispara_g2(0)
    assert not se_dispara_g2(3)


def test_g2_respuesta_no_inventa():
    r = respuesta_g2().lower()
    assert "no" in r and "futuro academy" in r


# ── G1-bis · Asesoría en la salida del agente ─────────────────────────────────

def test_g1bis_detecta_recomendacion_concreta():
    assert se_dispara_g1bis("Te recomiendo comprar acciones de Tesla ya mismo.")
    assert se_dispara_g1bis("Deberías invertir en el fondo conservador de la casa.")


def test_g1bis_no_dispara_con_educacion():
    assert not se_dispara_g1bis("Un ETF es un fondo que replica un índice.")
    assert not se_dispara_g1bis("Podemos ver juntos cómo evaluar el riesgo.")


def test_g1bis_sanitiza_y_reconduce():
    texto, disparos = evaluar_salida_agente("Invierte en Bitcoin, te conviene.")
    assert disparos and disparos[0].guardrail == "G1-bis"
    assert "asesor" in texto.lower()
    assert "bitcoin" not in texto.lower()


# ── G7 · No prometer rendimientos ─────────────────────────────────────────────

def test_g7_detecta_promesa_de_rendimiento():
    assert se_dispara_g7("Este fondo rinde 12% anual garantizado.")
    assert se_dispara_g7("Vas a ganar un 20% en un año.")


def test_g7_no_dispara_sin_cifras_de_retorno():
    assert not se_dispara_g7("La diversificación reduce el riesgo de tu cartera.")


def test_g7_agrega_nota_de_no_garantia():
    texto, disparos = evaluar_salida_agente("Con esto obtienes un 15% de rendimiento anual.")
    assert any(d.guardrail == "G7" for d in disparos)
    assert "no puedo darte cifras" in texto.lower() or "no garantiza" in texto.lower()


# ── G5 · Segregación de superficies ───────────────────────────────────────────

def test_g5_no_filtra_datos_internos_al_prospecto():
    assert se_dispara_g5("Tu score es 88 y estás en banda caliente.")
    texto, disparos = evaluar_salida_agente("Revisé tu brief en la bitácora del pipeline.")
    assert any(d.guardrail == "G5" for d in disparos)
    assert "brief" not in texto.lower() and "bitácora" not in texto.lower()


# ── G6 · Alcance temático + G1 en la entrada ──────────────────────────────────

def test_g6_rechaza_fuera_de_dominio():
    assert se_dispara_g6("escríbeme un poema sobre el mar")
    respuesta, disparo = evaluar_entrada_usuario("escríbeme un poema sobre el mar")
    assert disparo and disparo.guardrail == "G6"
    assert "educación financiera" in respuesta.lower() or "financiera" in respuesta.lower()


def test_g1_intercepta_pedido_de_recomendacion():
    respuesta, disparo = evaluar_entrada_usuario("¿en qué invierto mi dinero?")
    assert disparo and disparo.guardrail == "G1"
    assert respuesta and "asesor" in respuesta.lower()


def test_entrada_limpia_pasa_de_largo():
    respuesta, disparo = evaluar_entrada_usuario("¿Qué es un ETF?")
    assert respuesta is None and disparo is None
