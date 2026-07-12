"""
G2 · Negativa honesta — Biblia §10, Manual R1 §9.

Si la búsqueda en el corpus aprobado (T6 · buscar_conocimiento) devuelve
vacío, está PROHIBIDO responder con el conocimiento del modelo. Prohibido
"aproximar". El agente dice, con todas sus letras, que no sabe.

Esta es la escena que gana el criterio 3 (antialucinación). La respuesta es
una plantilla FIJA — el LLM nunca la redacta, así nunca se resbala.
"""

_RESPUESTA_G2 = (
    "Eso no está cubierto en el material aprobado de Futuro Academy, y prefiero "
    "no darte un dato que no pueda respaldar. Si quieres, puedo explicarte alguno "
    "de los temas que sí tengo verificados, o conectarte con un asesor."
)


def se_dispara_g2(documentos_encontrados: int) -> bool:
    """True si el RAG no encontró ningún documento aprobado que respalde la respuesta."""
    return documentos_encontrados <= 0


def respuesta_g2() -> str:
    """Respuesta FIJA de negativa honesta. Nunca la genera el LLM."""
    return _RESPUESTA_G2
