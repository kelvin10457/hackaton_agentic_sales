"""
tools/inferir_senales.py — Extracción DETERMINISTA de señales del historial.

CÓDIGO PURO. Cero LLM, cero dependencias externas. Mismo historial → mismas
señales, siempre. Es lo que hace el score reproducible.

Regla de la Biblia §4.2: **sin evidencia → None. PROHIBIDO ADIVINAR.**
Si el prospecto no dijo cuánto tiene, no nos lo inventamos: es `None` y el
score simplemente no suma esa dimensión.

Lo usan dos capas (por eso vive en tools/, no en un router):
  · app/routers/chat.py     → para poblar senales_lead al entrar al CRM
  · core/servicio_agente.py → para saber qué preguntas de config/ ya están
                              respondidas y no repetirlas (Biblia §7)
"""
import re

# ── Pistas de dinero ─────────────────────────────────────────────────────────
_PISTAS_DINERO = (
    "usd", "dólar", "dolar", "$", "monto", "ahorr", "invertir", "inversión",
    "inversion", "presupuesto", "capital", "plata", "dinero", "tengo",
)


def extraer_monto(texto: str) -> float | None:
    """Monto declarado en USD. Solo si el texto habla de dinero, y nunca
    confundiendo un año (2026) con un monto."""
    if not any(p in texto for p in _PISTAS_DINERO):
        return None

    candidatos: list[float] = []
    for m in re.finditer(r"\b(\d{1,3}(?:[.,]\d{3})+|\d{3,7})\b", texto):
        crudo = m.group(1).replace(".", "").replace(",", "")
        try:
            valor = float(crudo)
        except ValueError:
            continue
        if 1900 <= valor <= 2100:      # es un año, no un monto
            continue
        if 100 <= valor <= 10_000_000:
            candidatos.append(valor)
    for m in re.finditer(r"\b(\d{1,3})\s*mil\b", texto):
        candidatos.append(float(m.group(1)) * 1000)

    return max(candidatos) if candidatos else None


def extraer_experiencia(texto: str) -> str | None:
    """experiencia_inversion. Sin evidencia → None."""
    if any(p in texto for p in (
        "nunca he invertido", "no he invertido", "sin experiencia", "desde cero",
        "primera vez", "soy nuevo", "soy nueva", "principiante", "no sé nada",
        "no se nada", "no tengo experiencia",
    )):
        return "ninguna"
    if any(p in texto for p in ("poca experiencia", "algo de experiencia", "básico", "basico")):
        return "basica"
    if any(p in texto for p in ("varios años invirtiendo", "experiencia intermedia", "llevo años")):
        return "intermedia"
    if any(p in texto for p in ("soy inversionista", "experiencia avanzada", "manejo un portafolio")):
        return "avanzada"
    return None


def extraer_horizonte(texto: str) -> str | None:
    if any(p in texto for p in ("ya", "ahora", "urgente", "inmediato", "hoy", "cuanto antes")):
        return "inmediato"
    if any(p in texto for p in ("este mes", "próximo mes", "proximo mes", "pronto", "unos meses", "próximos meses")):
        return "1-3m"
    if any(p in texto for p in ("medio año", "6 meses", "seis meses", "este año")):
        return "3-6m"
    if any(p in texto for p in ("largo plazo", "varios años", "más de un año", "mas de un año", "5 años")):
        return "mas_6m"
    return None


# ── Objeciones (criterio 3.1 — Carlos NECESITA saberlas antes de llamar) ─────
# Cada patrón se traduce a una objeción legible. No se inventa ninguna: si no
# hay frase que la respalde, la lista queda vacía.
_OBJECIONES = [
    (("miedo a perder", "perder mi dinero", "perder dinero", "y si pierdo",
      "me da miedo", "temo perder"), "Le preocupa perder dinero"),
    (("no confío", "no confio", "desconfío", "desconfio", "es una estafa",
      "suena a estafa"), "Desconfía de los productos de inversión"),
    (("muy arriesgado", "es riesgoso", "mucho riesgo", "demasiado riesgo"),
     "Percibe la inversión como demasiado riesgosa"),
    (("prefiero el banco", "plazo fijo", "póliza", "poliza", "en el banco"),
     "Compara con alternativas bancarias tradicionales (plazo fijo/póliza)"),
    (("no tengo tiempo", "no me da el tiempo", "estoy muy ocupad"),
     "Falta de tiempo para dedicarle"),
    (("es caro", "muy costoso", "no me alcanza", "no tengo tanto"),
     "Percibe el costo como una barrera"),
    (("no entiendo", "es complicado", "muy complejo", "no sé por dónde",
      "no se por donde"), "Siente que el tema es complejo y no sabe por dónde empezar"),
    (("solo para expertos", "no soy experto", "eso es para ricos"),
     "Cree que invertir es solo para expertos"),
    (("mala experiencia", "ya me estafaron", "me fue mal"),
     "Tuvo una mala experiencia previa"),
    (("no quiero que me llamen", "no me llamen", "sin vendedores",
      "que no me contacten"), "No quiere ser contactado por vendedores"),
    (("tengo deudas", "debo dinero", "pagar mis deudas"),
     "Prioriza pagar deudas antes de invertir"),
    (("necesito el dinero", "liquidez", "disponible en cualquier momento"),
     "Necesita mantener liquidez inmediata"),
]


def extraer_objeciones(texto: str) -> list[str]:
    """Frenos declarados por el prospecto. Lista vacía si no dijo ninguno."""
    encontradas: list[str] = []
    for patrones, etiqueta in _OBJECIONES:
        if any(p in texto for p in patrones) and etiqueta not in encontradas:
            encontradas.append(etiqueta)
    return encontradas


# ── Necesidad (criterio 3.1) ─────────────────────────────────────────────────
_SALUDOS = {
    "hola", "buenas", "buenos días", "buenos dias", "buenas tardes",
    "buenas noches", "hey", "qué tal", "que tal", "saludos", "hi",
}


def extraer_necesidad(mensajes_usuario: list[str]) -> str | None:
    """Lo que el prospecto dijo que quiere, CON SUS PALABRAS.

    No se resume con un LLM ni se inventa: se toma su primer mensaje con
    contenido real (descartando saludos). Si solo saludó, es None.
    """
    for crudo in mensajes_usuario:
        texto = crudo.strip()
        limpio = texto.lower().strip(" .!¡?¿,")
        if limpio in _SALUDOS or len(texto.split()) < 4:
            continue
        return texto[:280]
    return None


# ── Entrada principal ────────────────────────────────────────────────────────

def inferir_senales(mensajes_usuario: list[str], quiz_perfil: str | None = None) -> dict:
    """Deriva las señales del contrato desde los mensajes del prospecto.

    `mensajes_usuario`: solo lo que ESCRIBIÓ el prospecto, en orden.
    `quiz_perfil`: el perfil del quiz determinista, si ya lo completó.
    """
    texto = " ".join(m.lower() for m in mensajes_usuario)
    n_mensajes = len(mensajes_usuario)

    es_b2b = any(p in texto for p in (
        "empresa", "mi negocio", "equipo", "colaboradores", "empleados",
        "capacitar", "corporativ", "somos una", "recursos humanos", "rrhh",
    ))
    segmento = "b2b" if es_b2b else "b2c"

    if "invertir" in texto or "inversión" in texto or "inversion" in texto:
        objetivo = "invertir"
    elif es_b2b and any(p in texto for p in ("capacitar", "equipo", "colaboradores")):
        objetivo = "capacitar_equipo"
    elif any(p in texto for p in ("aprender", "entender", "educación", "educacion", "saber")):
        objetivo = "aprender"
    else:
        objetivo = None      # sin evidencia → None

    pidio_asesor = any(p in texto for p in (
        "asesor", "hablar con alguien", "contactar", "reunión", "reunion",
        "cotización", "cotizacion", "propuesta", "que me llamen", "llamada",
    ))

    num_colaboradores = None
    if es_b2b:
        m = re.search(r"\b(\d{1,5})\s*(?:colaboradores|empleados|personas|trabajadores)", texto)
        if m:
            num_colaboradores = int(m.group(1))

    monto = extraer_monto(texto)

    return {
        "segmento": segmento,
        "objetivo": objetivo,
        "horizonte": extraer_horizonte(texto),
        "pidio_asesor": pidio_asesor,
        "mensajes_intercambiados": n_mensajes,
        "completo_quiz": quiz_perfil is not None,
        "perfil_riesgo": quiz_perfil,
        "monto_declarado_usd": None if es_b2b else monto,
        "experiencia_inversion": None if es_b2b else extraer_experiencia(texto),
        "num_colaboradores": num_colaboradores,
        "presupuesto_capacitacion_usd": monto if es_b2b else None,
        "es_decisor": es_b2b and any(
            p in texto for p in ("soy el", "soy la", "gerente", "jefe", "director", "dueño")
        ),
        "solicito_propuesta": es_b2b and any(
            p in texto for p in ("propuesta", "cotización", "cotizacion")
        ),
        # ── Brief (viven en el Lead, no en Senales — Biblia §4.1) ────────────
        "necesidad": extraer_necesidad(mensajes_usuario),
        "objeciones": extraer_objeciones(texto),
    }
