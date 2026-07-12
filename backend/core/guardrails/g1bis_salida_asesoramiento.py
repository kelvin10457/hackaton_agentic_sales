"""
G1-bis · No-asesoramiento sobre la SALIDA del agente — Biblia §10, Manual R1 §9.

Agujero clásico: G1 vigila el mensaje del USUARIO, pero nadie vigila lo que el
AGENTE redacta. Si el tutor o el borrador de acción (T11) escribe
"dado tu perfil moderado, te recomendamos nuestro fondo conservador", acaba de
dar asesoría de inversión — aunque un humano lo apruebe después.

FIJO (Manual R1 §9): el texto del agente puede proponer *hablar con alguien* o
*leer algo*. NUNCA nombrar un producto financiero concreto ni recomendar una
asignación. Se valida ANTES de que la respuesta llegue al usuario o de que la
propuesta llegue a la consola de R4.

Esta malla es determinista (regex/keywords). No llama al LLM: es el freno que
no se puede "convencer".
"""
import re

# Frases que implican una recomendación de asignación o de compra concreta.
_PATRONES_RECOMENDACION = [
    r"\bte recomiendo (?:comprar|invertir|poner|meter)\b",
    r"\bte recomendamos (?:comprar|invertir|el fondo|la acci[oó]n)\b",
    r"\bdeber[ií]as (?:comprar|invertir en|poner tu dinero)\b",
    r"\blo mejor para ti es (?:comprar|invertir en|el fondo)\b",
    r"\bpon(?:er)? tu dinero en\b",
    r"\bte conviene (?:comprar|el fondo|la acci[oó]n)\b",
    r"\binvierte en\b",
    r"\bcompra (?:acciones de|el etf|el fondo)\b",
]

# Nombres de instrumentos/productos concretos que el agente NUNCA debe recetar.
# (Hablar del CONCEPTO "qué es un ETF" es educación y sí está permitido; el
#  guardrail busca la RECOMENDACIÓN de uno concreto, ver _parece_recomendacion.)
_PALABRAS_PRODUCTO_CONCRETO = [
    "bitcoin", "ethereum", "tesla", "apple", "nvidia", "s&p 500", "sp500",
    "nasdaq", "bono del tesoro", "fondo conservador de", "fondo agresivo de",
]

_regex_reco = re.compile("|".join(_PATRONES_RECOMENDACION), re.IGNORECASE)


def se_dispara_g1bis(texto_agente: str) -> bool:
    """True si el texto redactado por el agente cruza a asesoría concreta."""
    if not texto_agente:
        return False
    bajo = texto_agente.lower()
    if _regex_reco.search(bajo):
        return True
    # Recomendación explícita + nombre de producto concreto en la misma frase
    if any(p in bajo for p in _PALABRAS_PRODUCTO_CONCRETO) and (
        "recomiend" in bajo or "deberías" in bajo or "deberias" in bajo
        or "te conviene" in bajo or "invierte" in bajo
    ):
        return True
    return False


_REEMPLAZO_G1BIS = (
    "Puedo darte el marco para que tomes esa decisión con criterio, pero la "
    "recomendación puntual sobre dónde invertir corresponde a un asesor "
    "habilitado de Futuro Academy. ¿Quieres que te conecte con uno o prefieres "
    "que sigamos con el material educativo?"
)


def sanitizar_salida_g1bis(texto_agente: str) -> tuple[str, bool]:
    """Devuelve (texto_seguro, se_disparo).

    Si el agente se resbaló a asesoría concreta, reemplaza TODO el mensaje por
    una reconducción fija a educación/asesor. No intenta "editar" la frase: la
    sustituye, que es lo seguro.
    """
    if se_dispara_g1bis(texto_agente):
        return _REEMPLAZO_G1BIS, True
    return texto_agente, False
