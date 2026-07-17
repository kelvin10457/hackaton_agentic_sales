"""
tools/buscar_conocimiento.py — RAG simple sobre la carpeta knowledge/.

Estrategia: recuperación léxica TOLERANTE (sin embeddings). Suficiente para ~15
documentos y —a diferencia de la versión anterior de intersección exacta— ya no
exige que la palabra esté escrita tal cual en la fuente:

  · normaliza tildes/diacríticos ("inflación" ≡ "inflacion"),
  · tokeniza quitando signos (¿?¡!:.,) — "ETF?" ≡ "etf",
  · empareja por raíz/prefijo — "riesgos" encuentra "riesgo",
    "comisiones" → "comisión", "diversificar" → "diversificación",
  · puentes de sinónimos acotados al dominio (riesgo↔perfil, tema↔índice…),
  · pondera más los aciertos en el TÍTULO que en el cuerpo.

Sigue siendo determinista y sin LLM: si de verdad no hay respaldo en el corpus,
devuelve vacío y el agente dispara la negativa honesta (G2). PROHIBIDO inventar.

Cada archivo FA-*.md tiene este formato:
    id: FA-001
    titulo: "..."
    cita_visible: "..."
    publico: "B2C" | "B2B" | "ambos"
    (línea vacía)
    Contenido del artículo...
"""
import re
import unicodedata
from pathlib import Path
from typing import Optional

# Ruta a la carpeta knowledge (dentro de backend/)
_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

# Palabras que no aportan relevancia (stop words + verbos de relleno educativos,
# para que "explícame X" no empareje por el verbo sino por el sustantivo X).
_STOP_WORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "en", "con", "por", "para", "que", "es", "son", "se", "su", "sus",
    "al", "a", "y", "o", "pero", "como", "que", "cual", "cuales", "cuanto",
    "cuanta", "cuantos", "cuantas", "cuando", "donde", "quien", "me",
    "mi", "tu", "te", "le", "nos", "yo", "si", "no", "mas", "muy",
    "tambien", "hay", "esta", "este", "esto", "eso", "esa", "sobre",
    "explica", "explicame", "explicarme", "explicar", "dime", "dame",
    "cuentame", "hablame", "habla", "quiero", "puedes", "puede", "podrias",
    "profundiza", "profundizame", "entender", "saber", "conocer", "sirve",
}

# Puentes conceptuales del dominio (acotados: no deben provocar falsos positivos
# con preguntas fuera de tema). Se aplican en ambos sentidos donde tiene sentido.
_SINONIMOS: dict[str, set[str]] = {
    "riesgo": {"perfil", "conservador", "moderado", "agresivo", "tolerancia", "volatilidad"},
    "perfil": {"riesgo", "conservador", "moderado", "agresivo"},
    "tema": {"indice", "aprender", "contenido", "catalogo", "cubre"},
    "aprender": {"tema", "educacion", "contenido", "curso"},
    "objetivo": {"futuro", "academy", "mision", "proposito", "meta"},
    "meta": {"objetivo", "futuro", "proposito"},
    "invertir": {"inversion", "inversiones"},
    "inversion": {"invertir", "inversiones"},
}


def _plegar(texto: str) -> str:
    """minúsculas + sin tildes/diacríticos."""
    base = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in base if not unicodedata.combining(c))


def _tokenizar(texto: str) -> set[str]:
    """Palabras significativas: sin tildes, sin signos, ≥3 letras, sin stop-words."""
    plano = _plegar(texto)
    palabras = re.split(r"[^a-z0-9]+", plano)
    return {p for p in palabras if len(p) >= 3 and p not in _STOP_WORDS}


def _raiz(palabra: str) -> str:
    """Stemming muy ligero para español (plurales y algunas terminaciones)."""
    for suf in ("ciones", "siones", "aciones"):
        if len(palabra) > len(suf) + 2 and palabra.endswith(suf):
            return palabra[: -len(suf)] + "cion"
    if len(palabra) > 4 and palabra.endswith("es"):
        return palabra[:-2]
    if len(palabra) > 3 and palabra.endswith("s"):
        return palabra[:-1]
    return palabra


def _prefijo_comun(a: str, b: str) -> int:
    n = 0
    for ca, cb in zip(a, b):
        if ca != cb:
            break
        n += 1
    return n


def _empareja(q: str, tokens: set[str], raices: set[str]) -> bool:
    """True si el término de búsqueda `q` corresponde a algún token del documento
    por igualdad, raíz común, prefijo, o prefijo común largo (para emparejar
    familias como 'diversificar' ↔ 'diversificación')."""
    if q in tokens:
        return True
    if _raiz(q) in raices:
        return True
    if len(q) >= 4:
        for dk in tokens:
            if len(dk) >= 4 and (dk.startswith(q) or q.startswith(dk)):
                return True
            if len(q) >= 7 and len(dk) >= 7 and _prefijo_comun(q, dk) >= 6:
                return True
    return False


def _parsear_documento(ruta: Path) -> Optional[dict]:
    """Lee un archivo FA-*.md y extrae metadatos + contenido + índices de búsqueda."""
    try:
        texto = ruta.read_text(encoding="utf-8")
    except Exception:
        return None

    lineas = texto.splitlines()
    meta: dict[str, str] = {}
    contenido_inicio = 0

    for i, linea in enumerate(lineas):
        if linea.strip() == "":
            contenido_inicio = i + 1
            break
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            meta[clave.strip()] = valor.strip().strip('"')

    contenido = "\n".join(lineas[contenido_inicio:]).strip()
    titulo = meta.get("titulo", "")

    tok_titulo = _tokenizar(titulo)
    tok_cont = _tokenizar(contenido)
    return {
        "id": meta.get("id", ruta.stem),
        "titulo": titulo,
        "cita_visible": meta.get("cita_visible", meta.get("id", ruta.stem)),
        "publico": meta.get("publico", ""),
        "contenido": contenido,
        "tok_titulo": tok_titulo,
        "tok_contenido": tok_cont,
        "raices_titulo": {_raiz(t) for t in tok_titulo},
        "raices_contenido": {_raiz(t) for t in tok_cont},
    }


def _score_relevancia(doc: dict, q_tokens: set[str]) -> int:
    """Suma ponderada: acierto en título vale 2, en cuerpo 1. Cada término de la
    búsqueda cuenta una sola vez (con su mejor acierto) para no inflar."""
    total = 0
    for q in q_tokens:
        expand = {q} | _SINONIMOS.get(q, set()) | _SINONIMOS.get(_raiz(q), set())
        if any(_empareja(e, doc["tok_titulo"], doc["raices_titulo"]) for e in expand):
            total += 2
        elif any(_empareja(e, doc["tok_contenido"], doc["raices_contenido"]) for e in expand):
            total += 1
    return total


# Cache en memoria — se carga una sola vez al arrancar
_docs_cache: list[dict] = []


def _cargar_documentos() -> list[dict]:
    """Carga todos los FA-*.md en memoria (con cache)."""
    global _docs_cache
    if _docs_cache:
        return _docs_cache

    docs = []
    if not _KNOWLEDGE_DIR.exists():
        return docs

    for ruta in sorted(_KNOWLEDGE_DIR.glob("FA-*.md")):
        doc = _parsear_documento(ruta)
        if doc:
            docs.append(doc)

    _docs_cache = docs
    return docs


def buscar_conocimiento(pregunta: str, top_k: int = 3) -> list[dict]:
    """
    Busca los documentos más relevantes para la pregunta del usuario.

    Devuelve una lista de hasta `top_k` documentos con:
        - id, titulo, cita_visible, contenido (truncado para el prompt)

    Si ningún documento alcanza relevancia mínima, devuelve lista vacía (→ G2).
    """
    docs = _cargar_documentos()
    if not docs:
        return []

    q_tokens = _tokenizar(pregunta)
    if not q_tokens:
        return []

    con_score = [(doc, _score_relevancia(doc, q_tokens)) for doc in docs]
    relevantes = [(doc, s) for doc, s in con_score if s > 0]
    relevantes.sort(key=lambda x: x[1], reverse=True)

    resultado = []
    for doc, _ in relevantes[:top_k]:
        resultado.append({
            "id": doc["id"],
            "titulo": doc["titulo"],
            "cita_visible": doc["cita_visible"],
            "contenido": doc["contenido"][:800],  # truncamos para el prompt
        })
    return resultado


def listar_temas(publico: Optional[str] = None) -> list[dict]:
    """Catálogo de temas disponibles (para responder '¿qué temas puedes explicar?').
    No expone el índice a sí mismo. `publico` opcional filtra por B2C/B2B."""
    docs = _cargar_documentos()
    temas = []
    for d in docs:
        if d["id"].startswith("FA-000"):
            continue
        if not d["titulo"]:
            continue
        pub = (d.get("publico") or "").lower()
        if publico and pub not in (publico.lower(), "ambos", ""):
            continue
        temas.append({"id": d["id"], "titulo": d["titulo"], "publico": pub})
    return temas


def formatear_documentos_para_prompt(docs: list[dict]) -> str:
    """Formatea los documentos encontrados para incluirlos en el prompt del tutor."""
    if not docs:
        return "(No se encontraron documentos relevantes en la base de conocimiento)"

    partes = []
    for doc in docs:
        partes.append(
            f"[{doc['id']}] {doc['titulo']}\n"
            f"Fuente: {doc['cita_visible']}\n"
            f"{doc['contenido']}"
        )
    return "\n\n---\n\n".join(partes)
