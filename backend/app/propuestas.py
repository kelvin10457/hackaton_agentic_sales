"""
propuestas.py — Generación DETERMINISTA de la AccionPropuesta (T11).

El agente PROPONE; nunca envía. La acción nace siempre en 'pendiente' y solo
Carlos, desde la consola, puede aprobarla. No existe ninguna función que envíe
nada: la línea roja es la AUSENCIA de la herramienta (Biblia §10 · G8).

Cero LLM: el borrador sale de plantillas fijas. Así el agente no puede
"resbalarse" y recomendar un producto financiero concreto. Aun así, el texto
pasa por G1-bis antes de llegar a la consola (Biblia §10 · G1-bis).

Lo usan DOS sitios, por eso vive aquí y no en un router:
  · routers/chat.py → cuando un prospecto real consiente y entra al CRM
  · seed.py         → para que los leads sembrados tengan su propuesta
"""
from sqlalchemy.orm import Session

from app.models import AccionPropuesta as AccionPropuestaModel, ScoreLead, SenalesLead
from core.guardrails import evaluar_salida_agente

# La ruta la calcula código determinista (T12) → de ahí sale el tipo de acción.
# Los tipos son los de la Biblia §4.6.
ACCION_POR_RUTA = {
    "ventas_corporativas": "derivar_a_ventas_corporativas",
    "asesoria_inversion": "agendar_reunion",
    "programa_inicial": "enviar_material",
    "nutricion_educativa": "enviar_material",
    "automatico": "enviar_material",
}


def redactar_borrador(
    tipo_accion: str,
    nombre: str,
    perfil_riesgo: str | None = None,
) -> tuple[str, str]:
    """Devuelve (asunto, cuerpo). Plantillas FIJAS — nunca las redacta el LLM.

    G1-bis: el borrador puede proponer HABLAR con alguien o LEER algo. Jamás
    nombra un producto financiero concreto ni recomienda una asignación.
    """
    if tipo_accion == "agendar_reunion":
        asunto = f"{nombre}, agendemos 20 minutos con un asesor"
        cuerpo = (
            f"Hola {nombre},\n\n"
            "Vi que quieres dar el siguiente paso con tus finanzas. Te propongo una "
            "sesión de 20 minutos con un asesor de Futuro Academy para revisar tu "
            "situación y resolver tus dudas, sin ningún compromiso.\n\n"
            "¿Te va bien esta semana?\n\n"
            "Saludos,\nEquipo Futuro Academy"
        )
    elif tipo_accion == "derivar_a_ventas_corporativas":
        asunto = f"{nombre}, propuesta corporativa de Futuro Academy"
        cuerpo = (
            f"Hola {nombre},\n\n"
            "Gracias por tu interés en formar a tu equipo. Derivo tu caso al área "
            "corporativa para preparar una propuesta ajustada al tamaño de tu "
            "organización.\n\n"
            "¿Cuándo te viene bien que te contactemos?\n\n"
            "Saludos,\nEquipo Futuro Academy"
        )
    else:  # enviar_material
        detalle = (
            f" Como tu perfil salió {perfil_riesgo}, incluí el material que mejor "
            "encaja contigo."
            if perfil_riesgo
            else ""
        )
        asunto = f"{nombre}, tu ruta de aprendizaje en Futuro Academy"
        cuerpo = (
            f"Hola {nombre},\n\n"
            f"Te comparto la ruta de aprendizaje de 3 pasos que preparamos para que "
            f"empieces con buen pie.{detalle}\n\n"
            "Cuando quieras profundizar, un asesor puede acompañarte.\n\n"
            "Saludos,\nEquipo Futuro Academy"
        )
    return asunto, cuerpo


def construir_razonamiento(
    score: ScoreLead,
    ruta: str,
    senales: SenalesLead,
) -> str:
    """El texto que Carlos lee ANTES de aprobar (criterio 3.2).

    Se arma por PLANTILLA desde cifras deterministas (G7): ningún número aquí
    proviene del texto del LLM.
    """
    partes = [
        f"Score {score.total:.0f}/100 ({score.banda}). Ruta determinista: {ruta}.",
        score.justificacion,
    ]
    if senales.perfil_riesgo:
        partes.append(f"Perfil de riesgo (quiz determinista): {senales.perfil_riesgo}.")
    if senales.pidio_asesor:
        partes.append("El prospecto pidió hablar con un asesor.")
    if senales.monto_declarado_usd:
        partes.append(f"Monto declarado: USD {senales.monto_declarado_usd:,.0f}.")
    if senales.num_colaboradores:
        partes.append(f"Empresa de {senales.num_colaboradores} colaboradores.")
    return " ".join(partes)


def generar_accion_propuesta(
    db: Session,
    lead_id: int,
    nombre: str,
    email: str,
    senales: SenalesLead,
    score: ScoreLead,
    ruta: str,
) -> tuple[AccionPropuestaModel | None, list]:
    """Crea la AccionPropuesta 'pendiente' del lead. Devuelve (accion, disparos).

    IDEMPOTENTE: si el lead ya tiene una propuesta pendiente, no crea otra
    (evita duplicados al reejecutar el seed o al volver a consentir).

    Se genera AUNQUE falte el consentimiento comercial: así la consola puede
    mostrar el bloqueo del botón "Aprobar" con su motivo (Biblia §4.5). Aprobar
    sin consentimiento devuelve 403 en la API — el bloqueo es real, no cosmético.
    """
    ya_existe = (
        db.query(AccionPropuestaModel)
        .filter(
            AccionPropuestaModel.lead_id == lead_id,
            AccionPropuestaModel.estado == "pendiente",
        )
        .first()
    )
    if ya_existe:
        return None, []

    tipo_accion = ACCION_POR_RUTA.get(ruta, "enviar_material")
    asunto, cuerpo = redactar_borrador(tipo_accion, nombre, senales.perfil_riesgo)

    # G1-bis · el borrador se valida ANTES de llegar a la consola de R4.
    cuerpo, disparos = evaluar_salida_agente(cuerpo)

    accion = AccionPropuestaModel(
        lead_id=lead_id,
        tipo=tipo_accion,
        destinatario={"email": email or "", "nombre": nombre},
        asunto=asunto,
        mensaje_sugerido=cuerpo,
        razonamiento=construir_razonamiento(score, ruta, senales),
        fuentes_consultadas=["FA-003 §1"] if senales.perfil_riesgo else [],
        snapshot_senales={
            "objetivo": senales.objetivo,
            "horizonte": senales.horizonte,
            "pidio_asesor": senales.pidio_asesor,
            "mensajes_intercambiados": senales.mensajes_intercambiados,
            "completo_quiz": senales.completo_quiz,
            "perfil_riesgo": senales.perfil_riesgo,
            "monto_declarado_usd": senales.monto_declarado_usd,
            "experiencia_inversion": senales.experiencia_inversion,
            "num_colaboradores": senales.num_colaboradores,
        },
        generado_por="agente:cv5",
        estado="pendiente",   # nace SIEMPRE pendiente. Nadie envía nada.
    )
    db.add(accion)
    db.flush()
    return accion, disparos
