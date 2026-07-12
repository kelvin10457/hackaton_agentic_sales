"""
tools/buscar_conocimiento.py — RAG simple sobre la carpeta knowledge/.

Estrategia: búsqueda por keywords (sin embeddings). Suficiente para 14
documentos. Si el corpus crece, se puede migrar a embeddings después.

Cada archivo FA-*.md tiene este formato:
    id: FA-001
    titulo: "..."
    cita_visible: "..."
    (línea vacía)
    Contenido del artículo...
"""
from pathlib import Path
from typing import Optional

# Ruta a la carpeta knowledge (dentro de backend/)
_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

# Palabras que no aportan relevancia (stop words en español)
_STOP_WORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "en", "con", "por", "para", "que", "es", "son", "se", "su", "sus",
    "al", "a", "y", "o", "pero", "como", "qué", "cuál", "cómo", "me",
    "mi", "tu", "te", "le", "nos", "yo", "si", "no", "más", "muy",
    "también", "hay", "esta", "este", "esto", "eso", "esa",
}


def _parsear_documento(ruta: Path) -> Optional[dict]:
    """Lee un archivo FA-*.md y extrae metadatos + contenido."""
    try:
        texto = ruta.read_text(encoding="utf-8")
    except Exception:
        return None

    lineas = texto.splitlines()
    meta = {}
    contenido_inicio = 0

    # Las primeras líneas son metadatos clave:valor hasta la primera línea vacía
    for i, linea in enumerate(lineas):
        if linea.strip() == "":
            contenido_inicio = i + 1
            break
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            meta[clave.strip()] = valor.strip().strip('"')

    contenido = "\n".join(lineas[contenido_inicio:]).strip()

    return {
        "id": meta.get("id", ruta.stem),
        "titulo": meta.get("titulo", ""),
        "cita_visible": meta.get("cita_visible", meta.get("id", ruta.stem)),
        "publico": meta.get("publico", ""),
        "contenido": contenido,
        "keywords": _extraer_keywords(meta.get("titulo", "") + " " + contenido),
    }


def _extraer_keywords(texto: str) -> set[str]:
    """Extrae palabras significativas del texto para búsqueda."""
    palabras = texto.lower().replace(",", " ").replace(".", " ").split()
    return {p for p in palabras if len(p) > 3 and p not in _STOP_WORDS}


def _score_relevancia(doc: dict, keywords_busqueda: set[str]) -> int:
    """Cuenta cuántas keywords de la búsqueda aparecen en el documento."""
    return len(doc["keywords"] & keywords_busqueda)


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
        - id, titulo, cita_visible, contenido (truncado a 600 chars para el prompt)

    Si ningún documento tiene relevancia mínima, devuelve lista vacía.
    """
    docs = _cargar_documentos()
    if not docs:
        return []

    keywords_busqueda = _extraer_keywords(pregunta)
    if not keywords_busqueda:
        return []

    # Calcular score de relevancia para cada documento
    con_score = [
        (doc, _score_relevancia(doc, keywords_busqueda))
        for doc in docs
    ]

    # Filtrar los que tienen al menos 1 keyword en común
    relevantes = [(doc, score) for doc, score in con_score if score > 0]

    # Ordenar por score descendente y tomar los top_k
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
