"""
core/guardrails — El bloque de seguridad del agente (25 % de la nota).

Fachada unificada. El orquestador y el servicio de chat solo importan de aquí:

    from core.guardrails import evaluar_entrada_usuario, evaluar_salida_agente

Mallas implementadas (Manual R1 §9 + 5 principios de diseño):
  G1     · No-asesoramiento sobre la ENTRADA del usuario   (g1_no_asesoramiento)
  G1-bis · No-asesoramiento sobre la SALIDA del agente     (g1bis_salida_asesoramiento)
  G2     · Negativa honesta cuando el RAG viene vacío       (g2_negativa_honesta)
  G3     · Consentimiento por finalidad                     (adicionales)
  G4     · Minimización de datos                            (adicionales)
  G5     · Segregación de superficies                       (adicionales)
  G6     · Alcance temático                                 (adicionales)
  G7     · Cifras deterministas / no prometer rendimientos  (g7_cifras_deterministas)
  G8     · Auditoría de cada disparo                        (registro)
"""
from core.guardrails.g1_no_asesoramiento import se_dispara_g1, respuesta_g1
from core.guardrails.g1bis_salida_asesoramiento import (
    se_dispara_g1bis,
    sanitizar_salida_g1bis,
)
from core.guardrails.g2_negativa_honesta import se_dispara_g2, respuesta_g2
from core.guardrails.g7_cifras_deterministas import (
    se_dispara_g7,
    sanitizar_salida_g7,
)
from core.guardrails.adicionales import (
    g3_puede_comunicar,
    g3_puede_entrar_crm,
    se_dispara_g4,
    se_dispara_g5,
    sanitizar_salida_g5,
    se_dispara_g6,
    respuesta_g6,
)
from core.guardrails.registro import DisparoGuardrail, nuevo_disparo


def evaluar_entrada_usuario(mensaje: str) -> tuple[str | None, DisparoGuardrail | None]:
    """Corre las mallas que actúan sobre el mensaje del USUARIO.

    Devuelve (respuesta_fija, disparo):
      - Si algún guardrail intercepta, `respuesta_fija` es la plantilla FIJA con
        la que debe responder el agente (nunca la redacta el LLM) y `disparo`
        describe el evento para auditar.
      - Si nada intercepta, devuelve (None, None) y el flujo normal continúa.
    """
    if se_dispara_g1(mensaje):
        return respuesta_g1(), nuevo_disparo(
            "G1", "El usuario pidió una recomendación concreta de inversión.", mensaje
        )
    if se_dispara_g6(mensaje):
        return respuesta_g6(), nuevo_disparo(
            "G6", "Consulta fuera del dominio de educación financiera.", mensaje
        )
    return None, None


def evaluar_salida_agente(
    texto: str,
    *,
    pidio_asesor: bool = False,
) -> tuple[str, list[DisparoGuardrail]]:
    """Corre las mallas que actúan sobre la SALIDA redactada por el agente.

    Sanea el texto en cadena (G1-bis → G7 → G5) y devuelve
    (texto_seguro, [disparos]) para que la capa API los persista (G8).
    """
    disparos: list[DisparoGuardrail] = []

    texto, g1bis = sanitizar_salida_g1bis(texto)
    if g1bis:
        disparos.append(nuevo_disparo(
            "G1-bis", "El agente se resbaló a una recomendación de inversión concreta.", texto
        ))

    texto, g7 = sanitizar_salida_g7(texto)
    if g7:
        disparos.append(nuevo_disparo(
            "G7", "El agente prometió un rendimiento numérico; se añadió la nota de no-garantía.", texto
        ))

    texto, g5 = sanitizar_salida_g5(texto)
    if g5:
        disparos.append(nuevo_disparo(
            "G5", "La salida filtraba vocabulario interno (score/brief/bitácora).", texto
        ))

    if pidio_asesor is False and se_dispara_g4(texto, pidio_asesor):
        disparos.append(nuevo_disparo(
            "G4", "El agente pidió cédula/PII antes de tiempo (minimización de datos).", texto
        ))

    return texto, disparos


__all__ = [
    "evaluar_entrada_usuario",
    "evaluar_salida_agente",
    "se_dispara_g1", "respuesta_g1",
    "se_dispara_g1bis", "sanitizar_salida_g1bis",
    "se_dispara_g2", "respuesta_g2",
    "g3_puede_comunicar", "g3_puede_entrar_crm",
    "se_dispara_g4",
    "se_dispara_g5", "sanitizar_salida_g5",
    "se_dispara_g6", "respuesta_g6",
    "se_dispara_g7", "sanitizar_salida_g7",
    "DisparoGuardrail", "nuevo_disparo",
]
