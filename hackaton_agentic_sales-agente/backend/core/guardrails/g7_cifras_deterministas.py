"""
G7 · Cifras deterministas — Biblia §10, Manual R1 §9.

Regla de oro #1: "El LLM extrae. El código calcula." Ninguna cifra que ve el
usuario sale del texto del modelo. Los números con peso de decisión (score,
perfil de riesgo, montos) se calculan con código puro (tools/calcular_score.py,
tools/obtener_quiz.py) y se inyectan en plantilla.

En el chat educativo, el riesgo concreto es que el LLM PROMETA un rendimiento
("este fondo rinde 12% anual", "vas a ganar 20%"). Eso es a la vez una
alucinación y una infracción regulatoria. Esta malla determinista detecta
promesas de rendimiento en el texto libre del tutor y las neutraliza.
"""
import re

# "rinde 12% anual", "ganarás un 15%", "retorno del 20 por ciento"
# verbo/sustantivo de retorno  →  … cifra + %/por ciento
_PATRON_RENDIMIENTO = re.compile(
    r"(rinde|rendimiento|retorno|gana\w*|inter[eé]s)[^.]{0,40}?"
    r"\d{1,3}\s?(?:%|por\s?ciento)",
    re.IGNORECASE,
)
# Forma inversa: "un 15% de rendimiento anual", "12% garantizado"
_PATRON_RENDIMIENTO_INV = re.compile(
    r"\d{1,3}\s?(?:%|por\s?ciento)[^.]{0,25}?"
    r"(anual|de rendimiento|de retorno|de ganancia|garantizad)",
    re.IGNORECASE,
)

_NOTA_G7 = (
    "Ningún producto serio garantiza un rendimiento fijo, y no puedo darte cifras "
    "de retorno: dependen del mercado y del riesgo. Lo que sí puedo explicarte es "
    "cómo funcionan los instrumentos para que evalúes el riesgo con criterio."
)


def se_dispara_g7(texto: str) -> bool:
    """True si el texto promete un rendimiento numérico concreto."""
    if not texto:
        return False
    return bool(_PATRON_RENDIMIENTO.search(texto) or _PATRON_RENDIMIENTO_INV.search(texto))


def sanitizar_salida_g7(texto: str) -> tuple[str, bool]:
    """Devuelve (texto_seguro, se_disparo).

    Si el LLM prometió un rendimiento, añade la nota de no-garantía y elimina la
    afirmación numérica del cierre para que no quede como promesa.
    """
    if se_dispara_g7(texto):
        return f"{texto.strip()}\n\n{_NOTA_G7}", True
    return texto, False


def numero_es_determinista(origen: str) -> bool:
    """Contrato de código: solo se muestran al usuario números cuyo origen es
    una tool de cálculo determinista, nunca el texto libre del LLM.
    """
    return origen in {
        "tools.calcular_score",
        "tools.obtener_quiz",
        "tools.calcular_ruta",
    }
