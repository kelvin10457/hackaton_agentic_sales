"""
G1 · No-asesoramiento de inversión — Biblia §10, Manual R1 §9.

Detección por patrones (primera malla). El Manual R1 también menciona una
segunda malla con un clasificador LLM para casos ambiguos — se puede
agregar después; esta primera malla ya cubre los casos directos y es
determinista (rápida, sin gastar cuota de Gemini).

FIJO: la respuesta de G1 es una plantilla FIJA. El LLM NUNCA redacta esta
respuesta — así se garantiza que el agente jamás "se resbale" y dé una
recomendación real, ni siquiera por accidente de fraseo.
"""

_PATRONES = [
    "en qué invierto", "en que invierto",
    "me conviene",
    "debería comprar", "deberia comprar",
    "cuál es mejor", "cual es mejor",
    "recomiéndame", "recomiendame",
    "dónde pongo mi dinero", "donde pongo mi dinero",
    "es buen momento",
    "qué acción compro", "que accion compro",
    "en qué fondo", "en que fondo",
]

_RESPUESTA_G1 = (
    "Entiendo la pregunta, y es la más común. Pero no puedo decirte dónde invertir: "
    "la asesoría de inversión personalizada está reservada a asesores habilitados, y yo no lo soy. "
    "Lo que sí puedo hacer es darte las herramientas para que esa decisión la tomes con criterio "
    "— o conectarte con un asesor de Futuro Academy. ¿Seguimos entendiendo tu situación?"
)


def se_dispara_g1(mensaje: str) -> bool:
    """True si el mensaje del usuario pide una recomendación concreta de inversión."""
    texto = mensaje.lower()
    return any(patron in texto for patron in _PATRONES)


def respuesta_g1() -> str:
    """Respuesta FIJA. Nunca la genera el LLM."""
    return _RESPUESTA_G1
