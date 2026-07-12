"""Motor determinista de scoring comercial (cuatro bloques de 0 a 25)."""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from models import SenalesLead, ScoreLead, AccionPropuesta as AccionPropuestaModel, Oportunidad


def _segmento(senales: SenalesLead, segmento: str | None = None) -> str:
    return (segmento or getattr(senales, "segmento", None) or "b2c").lower()


def ruta_sugerida(segmento: str, total: float, pidio_asesor: bool) -> str:
    if segmento.lower() == "b2b":
        return "ventas_corporativas"
    if total >= 70:
        return "asesoria_inversion" if pidio_asesor else "programa_inicial"
    if total >= 40:
        return "nutricion_educativa"
    return "automatico"


def calcular_score(senales: SenalesLead, segmento: str | None = None) -> dict[str, Any]:
    """Aplica la fórmula del contrato, sin LLM ni ponderaciones porcentuales."""
    tipo = _segmento(senales, segmento)
    mensajes = senales.mensajes_intercambiados or 0

    interes = 0
    if senales.pidio_asesor:
        interes += 12
    if (tipo == "b2b" and senales.solicito_propuesta) or (tipo != "b2b" and senales.completo_quiz):
        interes += 7
    interes += 4 if mensajes >= 8 else 2 if mensajes >= 4 else 0
    if senales.objetivo == "invertir":
        interes += 6
    elif senales.objetivo == "aprender":
        interes += 2
    elif tipo == "b2b" and senales.objetivo == "capacitar_equipo":
        # Caso de referencia B2B del contrato: interés del equipo.
        interes += 6
    interes = min(interes, 25)

    if tipo == "b2b":
        colaboradores = senales.num_colaboradores or 0
        presupuesto = senales.presupuesto_capacitacion_usd or 0
        presupuesto_bloque = 15 if colaboradores >= 200 else 10 if colaboradores >= 50 else 6 if colaboradores >= 10 else 2
        presupuesto_bloque += 10 if presupuesto >= 5000 else 5 if presupuesto > 0 else 0
        perfil = 15 if senales.es_decisor else 4
        perfil += 6 if senales.ruc_valido else 0
        perfil += 4 if senales.email_corporativo else 0
    else:
        monto = senales.monto_declarado_usd or 0
        presupuesto_bloque = 25 if monto >= 25000 else 20 if monto >= 10000 else 14 if monto >= 3000 else 8 if monto >= 500 else 3 if monto > 0 else 0
        experiencia = senales.experiencia_inversion or ""
        perfil = 15 if experiencia in ("ninguna", "basica") else 10 if experiencia == "intermedia" else 5 if experiencia == "avanzada" else 0
        perfil += 6 if senales.documento_valido else 0
        perfil += 4 if senales.email_valido else 0

    presupuesto_bloque = min(presupuesto_bloque, 25)
    perfil = min(perfil, 25)
    urgencia = {"inmediato": 25, "1-3m": 18, "3-6m": 10, "mas_6m": 4}.get(senales.horizonte or "", 0)
    total = min(100, interes + presupuesto_bloque + perfil + urgencia)
    banda = "caliente" if total >= 70 else "tibio" if total >= 40 else "frio"
    justificacion = (
        f"Interés {interes}/25; presupuesto {presupuesto_bloque}/25; perfil {perfil}/25; "
        f"urgencia {urgencia}/25. Total {total}/100: {banda}."
    )
    return {
        "dimension_interes": float(interes), "dimension_capacidad": float(presupuesto_bloque),
        "dimension_fit": float(perfil), "dimension_urgencia": float(urgencia),
        "total": float(total), "banda": banda, "justificacion": justificacion,
    }


def upsert_score(db: Session, lead_id: int, senales: SenalesLead, segmento: str | None = None) -> ScoreLead:
    resultado = calcular_score(senales, segmento)
    score = db.query(ScoreLead).filter(ScoreLead.lead_id == lead_id).first()
    if score:
        for clave, valor in resultado.items():
            setattr(score, clave, valor)
        score.calculado_en = datetime.now(timezone.utc)
    else:
        score = ScoreLead(lead_id=lead_id, **resultado, calculado_en=datetime.now(timezone.utc))
        db.add(score)
    oportunidad = db.query(Oportunidad).filter(Oportunidad.lead_id == lead_id).first()
    if oportunidad:
        oportunidad.ruta_sugerida = ruta_sugerida(_segmento(senales, segmento), score.total, bool(senales.pidio_asesor))
        oportunidad.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(score)
    return score


def marcar_acciones_obsoletas(db: Session, lead_id: int) -> int:
    acciones = db.query(AccionPropuestaModel).filter(AccionPropuestaModel.lead_id == lead_id, AccionPropuestaModel.estado == "pendiente").all()
    for accion in acciones:
        accion.estado = "obsoleta"
        accion.updated_at = datetime.now(timezone.utc)
    db.commit()
    return len(acciones)


def recalcular_con_obsolescencia(db: Session, lead_id: int, senales: SenalesLead, segmento: str | None = None) -> tuple[ScoreLead, int]:
    score = upsert_score(db, lead_id, senales, segmento)
    return score, marcar_acciones_obsoletas(db, lead_id)
