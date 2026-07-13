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


# Números escritos con palabras ("diez mil", "quinientos")
_PALABRA_NUMERO = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "quince": 15,
    "veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
    "ochenta": 80, "cien": 100, "doscientos": 200, "trescientos": 300,
    "quinientos": 500,
}


def _extraer_cifras(texto: str) -> list[float]:
    """Todas las cantidades del texto, en cualquier formato ecuatoriano real:
    '10000', '10.000', '10,000', '10 000', '$10000', '10k', '10 mil',
    'diez mil', 'un millón'."""
    t = texto.lower().replace("$", " ").replace("usd", " ")
    cifras: list[float] = []

    # "10 mil", "10k", "diez mil", "un millón"
    for m in re.finditer(r"\b(\d{1,4}|[a-záéíóú]+)\s*(k\b|mil(?:es)?\b|millón|millon|millones)", t):
        base_crudo, mult_crudo = m.group(1), m.group(2)
        base = _PALABRA_NUMERO.get(base_crudo) if not base_crudo.isdigit() else float(base_crudo)
        if base is None:
            continue
        mult = 1_000_000 if mult_crudo.startswith("mill") else 1000
        cifras.append(float(base) * mult)

    # Dígitos con separador de miles (punto, coma o ESPACIO) o pelados
    for m in re.finditer(r"\b\d{1,3}(?:[ .,]\d{3})+\b|\b\d+\b", t):
        crudo = m.group(0).replace(".", "").replace(",", "").replace(" ", "")
        try:
            cifras.append(float(crudo))
        except ValueError:
            continue

    return cifras


def extraer_monto(texto: str) -> float | None:
    """Monto declarado en USD, para extracción GLOBAL (todo el historial junto).
    Exige contexto de dinero y descarta años (2026) para no adivinar."""
    if not any(p in texto for p in _PISTAS_DINERO):
        return None
    candidatos = [
        v for v in _extraer_cifras(texto)
        if 100 <= v <= 10_000_000 and not (1900 <= v <= 2100)
    ]
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


# ── Saludos y despedidas ─────────────────────────────────────────────────────
_SALUDOS = {
    "hola", "buenas", "buenos días", "buenos dias", "buenas tardes",
    "buenas noches", "hey", "qué tal", "que tal", "saludos", "hi", "holi",
}

_KW_FINANZAS = (
    "invertir", "inversión", "inversion", "ahorr", "aprender", "dinero",
    "finanz", "empresa", "capacitar", "fondo", "etf", "plazo", "presupuesto",
    "jubil", "meta", "casa", "negocio", "deuda", "riesgo", "económ", "econom",
    "asesor", "capital", "interés", "interes", "rendimiento", "bolsa",
)


def es_saludo(texto: str) -> bool:
    """True si el mensaje es un saludo (con o sin presentación de nombre)."""
    bajo = (texto or "").lower().strip(" .!¡?¿,")
    if not bajo:
        return False
    if bajo in _SALUDOS:
        return True
    empieza_saludando = any(bajo.startswith(s) for s in _SALUDOS)
    corto = len(bajo.split()) <= 8
    sin_sustancia = not any(k in bajo for k in _KW_FINANZAS)
    return empieza_saludando and corto and sin_sustancia


_DESPEDIDAS = (
    "eso es todo", "nada más", "nada mas", "chao", "chau", "adiós", "adios",
    "hasta luego", "bye", "me voy", "ya no necesito", "eso sería todo",
    "eso seria todo", "muchas gracias", "gracias por todo", "no gracias",
    "estoy bien así", "estoy bien asi",
)


def es_despedida(texto: str) -> bool:
    bajo = (texto or "").lower().strip(" .!¡?¿,")
    if bajo == "gracias":
        return True
    return any(d in bajo for d in _DESPEDIDAS)


# ── Nombre (identificación progresiva, Biblia §2.3) ──────────────────────────

_RECHAZOS_NOMBRE = (
    "no quiero", "prefiero no", "para qué", "para que", "no te digo", "paso",
    "anónimo", "anonimo", "sin nombre", "no gracias", "luego", "después",
    "despues", "mejor no", "no importa",
)

# Palabras que jamás son un nombre (respuestas comunes de una palabra)
_NO_ES_NOMBRE = {
    "si", "sí", "no", "ok", "hola", "gracias", "bueno", "dale", "claro",
    "invertir", "aprender", "ahorrar", "nada", "listo", "vale", "ya",
    "quiero", "empezar", "ayuda",
}

_PATRON_INTRO_NOMBRE = re.compile(
    r"(?:me llamo|mi nombre es|soy|ll[aá]mame|puedes llamarme|dime)\s+"
    r"([a-záéíóúñü]+(?:\s+[a-záéíóúñü]+)?)",
    re.IGNORECASE,
)


def extraer_nombre_intro(texto: str) -> str | None:
    """Nombre SOLO si viene presentado explícitamente ('me llamo Kenny')."""
    m = _PATRON_INTRO_NOMBRE.search(texto or "")
    if not m:
        return None
    candidato = m.group(1).strip()
    palabras = candidato.split()
    if any(p.lower() in _NO_ES_NOMBRE or p.lower() in _KW_FINANZAS for p in palabras):
        return None
    return " ".join(p.capitalize() for p in palabras)


def parse_nombre(texto: str) -> tuple[str | None, bool]:
    """Interpreta la respuesta a '¿cómo te llamas?'. Devuelve (nombre, rechazó).

    Es tolerante ('soy Kenny', 'Kenny Chung', 'kenny') pero nunca adivina: si la
    respuesta es una frase con contenido financiero, NO es un nombre y el flujo
    debe procesarla como mensaje normal.
    """
    crudo = (texto or "").strip()
    bajo = crudo.lower().strip(" .!¡?¿,")

    if not crudo:
        return None, False
    if any(r in bajo for r in _RECHAZOS_NOMBRE) or bajo == "no":
        return None, True

    explicito = extraer_nombre_intro(crudo)
    if explicito:
        return explicito, False

    # Respuesta corta y alfabética → es el nombre ("kenny", "Ana María")
    palabras = [p.strip(".,!¿?¡") for p in crudo.split()]
    if 1 <= len(palabras) <= 3 and all(
        p.replace("á", "a").replace("é", "e").replace("í", "i")
         .replace("ó", "o").replace("ú", "u").replace("ñ", "n").isalpha()
        for p in palabras
    ):
        if not any(p.lower() in _NO_ES_NOMBRE or p.lower() in _KW_FINANZAS for p in palabras):
            return " ".join(p.capitalize() for p in palabras), False

    return None, False   # frase con contenido → procesar como mensaje normal


# ── Parsers ATRIBUIDOS (la respuesta a UNA pregunta concreta) ────────────────
# Cuando sabemos QUÉ pregunta acaba de hacer el agente, la respuesta se parsea
# con tolerancia: '10 000' a la pregunta del monto ES un monto, y 'no' a
# '¿has invertido antes?' ES 'ninguna'.

_UNIDAD_TIEMPO = re.compile(
    r"(\d{1,3}|" + "|".join(_PALABRA_NUMERO) + r")\s*(día|dia|semana|mes|año|ano)",
    re.IGNORECASE,
)


def parse_monto_atribuido(texto: str) -> float | None:
    bajo = (texto or "").lower()
    # Si la respuesta habla de tiempo, NO es un monto ("3 meses").
    if _UNIDAD_TIEMPO.search(bajo) or any(
        u in bajo for u in ("mes", "año", "semana", "día", "dia")
    ):
        return None
    candidatos = [v for v in _extraer_cifras(bajo) if 0 <= v <= 50_000_000]
    return max(candidatos) if candidatos else None


def parse_horizonte_atribuido(texto: str) -> str | None:
    bajo = (texto or "").lower()
    if any(p in bajo for p in ("ya", "ahora", "inmediat", "hoy", "urgente", "cuanto antes", "esta semana")):
        return "inmediato"
    if "medio año" in bajo or "medio ano" in bajo:
        return "3-6m"
    if any(p in bajo for p in ("largo plazo", "varios años", "varios anos")):
        return "mas_6m"
    if "corto plazo" in bajo:
        return "1-3m"

    m = _UNIDAD_TIEMPO.search(bajo)
    if m:
        n_crudo, unidad = m.group(1), m.group(2)
        n = _PALABRA_NUMERO.get(n_crudo, None) if not n_crudo.isdigit() else int(n_crudo)
        if n is None:
            return None
        if unidad.startswith(("día", "dia")) or unidad.startswith("semana"):
            return "inmediato" if (unidad.startswith(("día", "dia")) or n <= 4) else "1-3m"
        if unidad.startswith("mes"):
            return "1-3m" if n <= 3 else "3-6m" if n <= 6 else "mas_6m"
        return "mas_6m"   # años
    # "un año", "un mes" sin dígito
    if "año" in bajo or "ano" in bajo:
        return "mas_6m"
    if "mes" in bajo:
        return "1-3m"
    return extraer_horizonte(bajo)


def parse_experiencia_atribuida(texto: str) -> str | None:
    bajo = (texto or "").lower().strip(" .!¡?¿,")
    explicita = extraer_experiencia(bajo)
    if explicita:
        return explicita
    if bajo in ("no", "nunca", "jamás", "jamas", "nada", "cero", "aún no", "aun no",
                "todavía no", "todavia no", "para nada", "no nunca"):
        return "ninguna"
    if bajo in ("sí", "si", "claro", "sip", "yes") or "un poco" in bajo or "algo" == bajo:
        return "basica"
    if any(p in bajo for p in ("varios años", "hace años", "bastante", "seguido", "frecuente")):
        return "intermedia"
    if any(p in bajo for p in ("profesional", "avanzad", "trader", "portafolio")):
        return "avanzada"
    return None


def parse_objetivo_atribuido(texto: str) -> str | None:
    bajo = (texto or "").lower()
    if any(p in bajo for p in ("capacitar", "equipo", "colaboradores", "empleados", "mi empresa")):
        return "capacitar_equipo"
    if any(p in bajo for p in ("invertir", "inversión", "inversion", "rendimiento", "crecer mi dinero", "multiplicar")):
        return "invertir"
    if any(p in bajo for p in ("aprender", "entender", "educar", "saber", "conocer", "ahorrar", "ahorro")):
        return "aprender"
    return None


def parse_colaboradores_atribuido(texto: str) -> int | None:
    cifras = [int(v) for v in _extraer_cifras(texto or "") if 1 <= v <= 100_000]
    return max(cifras) if cifras else None


# Señal → parser tolerante. Las claves son los `senal:` de config/preguntas_*.yaml.
PARSERS_ATRIBUIDOS = {
    "objetivo": parse_objetivo_atribuido,
    "monto_declarado_usd": parse_monto_atribuido,
    "horizonte": parse_horizonte_atribuido,
    "experiencia_inversion": parse_experiencia_atribuida,
    "num_colaboradores": parse_colaboradores_atribuido,
    "presupuesto_capacitacion_usd": parse_monto_atribuido,
}


def parsear_respuesta(senal: str, texto: str):
    """Parsea `texto` como respuesta a la pregunta de `senal`. None si no calza."""
    parser = PARSERS_ATRIBUIDOS.get(senal)
    return parser(texto) if parser else None


def cross_parse(texto: str, excluir: str | None = None) -> dict:
    """La respuesta no calzó con SU pregunta — ¿calza con OTRA señal?
    Caso real: responder '3 meses' cuando se preguntó el monto. El dato no se
    pierde: se guarda como horizonte y se re-pregunta el monto."""
    hallazgos: dict = {}
    for senal, parser in PARSERS_ATRIBUIDOS.items():
        if senal == excluir:
            continue
        valor = parser(texto)
        if valor is not None:
            hallazgos[senal] = valor
    return hallazgos


# ── Acuses de recibo por plantilla (G7: cero LLM en los números) ─────────────

_HORIZONTE_LEGIBLE = {
    "inmediato": "de inmediato",
    "1-3m": "en 1 a 3 meses",
    "3-6m": "en 3 a 6 meses",
    "mas_6m": "a más de 6 meses",
}

_EXPERIENCIA_LEGIBLE = {
    "ninguna": "empezamos desde cero — justo para eso existe Futuro Academy",
    "basica": "con una base ya ganada",
    "intermedia": "con buena experiencia previa",
    "avanzada": "con experiencia avanzada",
}


def acuse_de_recibo(senal: str, valor, nombre: str | None = None) -> str:
    """Frase corta de acuse, 100 % determinista. El valor viene del parser,
    nunca del LLM (G7)."""
    n = f", {nombre}" if nombre else ""
    if senal in ("monto_declarado_usd", "presupuesto_capacitacion_usd"):
        cifra = f"{valor:,.0f}".replace(",", ".")   # miles con punto (es-EC)
        return f"Anotado{n}: USD {cifra}."
    if senal == "horizonte":
        return f"Perfecto{n}: {_HORIZONTE_LEGIBLE.get(valor, valor)}."
    if senal == "experiencia_inversion":
        return f"Entendido{n}: {_EXPERIENCIA_LEGIBLE.get(valor, valor)}."
    if senal == "objetivo":
        detalle = {
            "invertir": "Empezar a invertir es una gran decisión.",
            "aprender": "Aprender es el mejor primer paso.",
            "capacitar_equipo": "Formar a tu equipo es una gran inversión.",
        }.get(valor, "Buen punto de partida.")
        return f"¡Perfecto{n}! {detalle}"
    if senal == "num_colaboradores":
        return f"Anotado{n}: {int(valor)} colaboradores."
    return f"Anotado{n}."


# ── Necesidad (criterio 3.1) ─────────────────────────────────────────────────

def extraer_necesidad(mensajes_usuario: list[str]) -> str | None:
    """Lo que el prospecto dijo que quiere, CON SUS PALABRAS.

    No se resume con un LLM ni se inventa. Se toma el primer mensaje con
    sustancia REAL: se descartan saludos (aunque traigan nombre), respuestas
    sueltas y texto sin relación con finanzas — mejor un brief vacío que
    'hola mi nombre es kenny' como necesidad.
    """
    for crudo in mensajes_usuario:
        texto = crudo.strip()
        if not texto or es_saludo(texto):
            continue
        bajo = texto.lower()
        con_finanzas = any(k in bajo for k in _KW_FINANZAS)
        sustancioso = len(texto.split()) >= 4
        if not (con_finanzas and sustancioso):
            continue
        # Limpia la presentación ("hola, me llamo kenny, quiero...")
        limpio = re.sub(
            r"^(hola|buenas(?:\s+\w+)?|hey)[,.!\s]+", "", texto, flags=re.IGNORECASE
        )
        limpio = re.sub(
            r"(?:me llamo|mi nombre es|soy)\s+[a-záéíóúñü]+[,.\s]*", "",
            limpio, flags=re.IGNORECASE,
        ).strip(" ,.")
        if len(limpio.split()) >= 3:
            return limpio[:280]
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
