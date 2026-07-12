"""
validators.py — Validaciones de identidad ecuatoriana.

Reglas de negocio:
  - validar_cedula: módulo 10, tal cual viene en el spec. NO se modifica.
  - validar_ruc: 13 dígitos, tres tipos según el tercer dígito:
      0-5 → Persona natural (primeros 10 = cédula válida)
      9   → Persona jurídica privada (módulo 11, coef. [4,3,2,7,6,5,4,3,2])
      6   → Sector público (módulo 11, coef. [3,2,7,6,5,4,3,2])
"""


# ──────────────────────────────────────────────────────────────────────────────
# FUNCIÓN ORIGINAL DEL SPEC — NO MODIFICAR
# ──────────────────────────────────────────────────────────────────────────────

def validar_cedula(c: str) -> bool:
    if len(c) != 10 or not c.isdigit():
        return False
    provincia = int(c[:2])
    if provincia < 1 or provincia > 24:
        return False
    coef = [2,1,2,1,2,1,2,1,2]
    total = 0
    for i in range(9):
        v = int(c[i]) * coef[i]
        total += v - 9 if v > 9 else v
    verificador = (10 - total % 10) % 10
    return verificador == int(c[9])


# ──────────────────────────────────────────────────────────────────────────────
# VALIDACIÓN DE RUC ECUATORIANO
# ──────────────────────────────────────────────────────────────────────────────

def validar_ruc(r: str) -> bool:
    """Valida un RUC ecuatoriano (13 dígitos).

    Tipos según el tercer dígito (posición índice 2):
      0–5 → Persona natural: primeros 10 dígitos = cédula válida + 3 dígitos de
             establecimiento (>= 001).
      9   → Persona jurídica privada: módulo 11 con coeficientes [4,3,2,7,6,5,4,3,2];
             verificador en posición 10 (índice 9); últimas 3 posiciones = establecimiento.
      6   → Sector público: módulo 11 con coeficientes [3,2,7,6,5,4,3,2];
             verificador en posición 9 (índice 8); últimas 4 posiciones = establecimiento.
    """
    if len(r) != 13 or not r.isdigit():
        return False

    provincia = int(r[:2])
    if provincia < 1 or provincia > 24:
        return False

    tercer = int(r[2])

    if 0 <= tercer <= 5:
        # Persona natural: los primeros 10 dígitos deben ser una cédula válida
        # y el número de establecimiento (últimos 3) debe ser mayor a cero.
        return validar_cedula(r[:10]) and int(r[10:]) > 0

    elif tercer == 9:
        # Persona jurídica privada — módulo 11
        coef = [4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(r[i]) * coef[i] for i in range(9))
        residuo = total % 11
        verificador = 0 if residuo == 0 else (11 - residuo)
        return verificador == int(r[9]) and int(r[10:]) > 0

    elif tercer == 6:
        # Sector público — módulo 11 variante
        coef = [3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(r[i]) * coef[i] for i in range(8))
        residuo = total % 11
        verificador = 0 if residuo == 0 else (11 - residuo)
        return verificador == int(r[8]) and int(r[9:]) > 0

    else:
        return False


def clasificar_documento(doc: str) -> str:
    """Determina el tipo de documento a partir de su longitud y contenido.
    Retorna: 'cedula' | 'ruc_natural' | 'ruc_juridico' | 'ruc_publico' | 'invalido'
    """
    if len(doc) == 10 and validar_cedula(doc):
        return "cedula"
    if len(doc) == 13:
        tercer = int(doc[2]) if doc.isdigit() else -1
        if 0 <= tercer <= 5 and validar_ruc(doc):
            return "ruc_natural"
        if tercer == 9 and validar_ruc(doc):
            return "ruc_juridico"
        if tercer == 6 and validar_ruc(doc):
            return "ruc_publico"
    return "invalido"
