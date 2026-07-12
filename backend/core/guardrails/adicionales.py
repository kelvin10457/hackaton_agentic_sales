"""
Guardrails G3–G6 — mallas de apoyo del núcleo agéntico.

El Manual R1 §9 detalla a fondo G1, G1-bis, G2 y G7 (los que mueven el 25 % de
antialucinación). G3–G6 son las mallas restantes que sostienen los 5 principios
de diseño del producto. Son deterministas y no llaman al LLM.

  G3 · Consentimiento por finalidad — no se ejecuta ninguna acción comercial sin
       el consentimiento correspondiente. En el backend se impone con HTTP 403
       (routers/consola.py); aquí se ofrece el checker que consume el orquestador.
  G4 · Minimización de datos — el agente no pide la cédula/PII antes de tiempo.
       La identificación es progresiva (nombre → email tras el quiz → cédula solo
       si pide asesor). Detecta si la SALIDA del agente pide cédula prematuramente.
  G5 · Segregación de superficies — el prospecto NUNCA ve su score, banda, brief
       ni bitácora. Detecta fugas de vocabulario interno en la salida del agente.
  G6 · Alcance temático — el asistente se mantiene en educación financiera; no
       responde temas fuera de dominio (política, medicina, código, etc.).
"""
import re


# ── G3 · Consentimiento por finalidad ────────────────────────────────────────

def g3_puede_comunicar(consentimiento_comunicaciones: bool) -> bool:
    """True solo si el lead consintió comunicaciones comerciales.
    El bloqueo duro vive en la API (403); esta es la comprobación reutilizable.
    """
    return bool(consentimiento_comunicaciones)


def g3_puede_entrar_crm(consentimiento_tratamiento_datos: bool, estado_identificacion: str) -> bool:
    """True solo si hay consentimiento de datos y el lead no es anónimo (LOPDP)."""
    return bool(consentimiento_tratamiento_datos) and estado_identificacion != "anonimo"


# ── G4 · Minimización de datos ───────────────────────────────────────────────

_PIDE_CEDULA = re.compile(
    r"\b(c[eé]dula|n[uú]mero de identificaci[oó]n|documento de identidad|ruc)\b",
    re.IGNORECASE,
)


def se_dispara_g4(texto_agente: str, pidio_asesor: bool) -> bool:
    """True si el agente pide la cédula/RUC sin que el usuario haya pedido asesor.
    Pedir PII antes de tiempo viola la minimización de datos.
    """
    if pidio_asesor:
        return False
    return bool(_PIDE_CEDULA.search(texto_agente or ""))


# ── G5 · Segregación de superficies ──────────────────────────────────────────

# Vocabulario interno que jamás debe aparecer en el chat del prospecto.
_TERMINOS_INTERNOS = [
    "tu score", "su score", "puntaje de lead", "lead score",
    "banda caliente", "banda tibia", "banda fría", "banda fria",
    "tu brief", "bitácora", "bitacora", "pipeline",
    "consola del ejecutivo", "score total",
]


def se_dispara_g5(texto_agente: str) -> bool:
    """True si la salida del agente filtra información comercial interna al prospecto."""
    bajo = (texto_agente or "").lower()
    return any(t in bajo for t in _TERMINOS_INTERNOS)


def sanitizar_salida_g5(texto_agente: str) -> tuple[str, bool]:
    """Si hay fuga de vocabulario interno, sustituye por un mensaje neutro."""
    if se_dispara_g5(texto_agente):
        seguro = (
            "Sigo aquí para ayudarte a aprender sobre finanzas. "
            "¿Sobre qué tema te gustaría que avancemos?"
        )
        return seguro, True
    return texto_agente, False


# ── G6 · Alcance temático ────────────────────────────────────────────────────

_FUERA_DE_DOMINIO = [
    "quién va a ganar", "resultado del partido", "receta de", "diagnóstico médico",
    "escríbeme un poema", "código python", "programa en", "hackear",
    "quién ganó las elecciones", "por quién voto",
]


def se_dispara_g6(mensaje_usuario: str) -> bool:
    """True si el usuario pide algo claramente fuera de la educación financiera."""
    bajo = (mensaje_usuario or "").lower()
    return any(t in bajo for t in _FUERA_DE_DOMINIO)


_RESPUESTA_G6 = (
    "Me especializo en educación financiera de Futuro Academy, así que ese tema "
    "se me escapa. Pero con gusto te ayudo a entender inversiones, ahorro o cómo "
    "empezar a invertir. ¿Por dónde te gustaría empezar?"
)


def respuesta_g6() -> str:
    return _RESPUESTA_G6
