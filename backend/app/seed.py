"""Carga datos de demostración idempotentes para las tareas #9 del Manual R2.

Ejecutar desde ``backend/``:
    PYTHONPATH=app .venv/bin/python app/seed.py
"""
from datetime import datetime, timezone

from database import Base, SessionLocal, engine
from models import Consentimiento, LeadV2, SenalesLead, ScoreLead
from scoring import upsert_score


SEMILLAS = [
    # Cada score se calcula exclusivamente desde ``senales`` con scoring.py.
    {"nombre": "María Villacís", "email": "maria.villacis@ejemplo.ec", "telefono": "+593991234567", "cedula": "1713175071", "empresa": "", "cargo": "", "segmento": "b2c", "estado": "verificado", "etapa": "listo_para_asesor", "consentimiento": (True, True), "senales": {"pidio_asesor": True, "completo_quiz": True, "mensajes_intercambiados": 11, "objetivo": "invertir", "monto_declarado_usd": 10000, "experiencia_inversion": "ninguna", "documento_valido": True, "email_valido": True, "horizonte": "1-3m"}},
    {"nombre": "Andrés Cordero", "email": "andres.cordero@acme.ec", "telefono": "+593987654321", "empresa": "Acme Ecuador", "cargo": "Gerente de Operaciones", "segmento": "b2b", "estado": "identificado", "etapa": "calificado", "consentimiento": (True, True), "senales": {"mensajes_intercambiados": 9, "objetivo": "capacitar_equipo", "num_colaboradores": 120, "presupuesto_capacitacion_usd": 8000, "es_decisor": True, "ruc_valido": True, "email_corporativo": True, "horizonte": "3-6m"}},
    {"nombre": "Sofía Andrade", "email": "sofia.andrade@ejemplo.ec", "telefono": "+593998765432", "empresa": "", "cargo": "", "segmento": "b2c", "estado": "identificado", "etapa": "listo_para_asesor", "consentimiento": (True, False), "senales": {"pidio_asesor": True, "completo_quiz": True, "mensajes_intercambiados": 5, "objetivo": "invertir", "monto_declarado_usd": 3000, "experiencia_inversion": "basica", "email_valido": True, "horizonte": "1-3m"}},
    {"nombre": "Carlos Mena", "email": "carlos.mena@nova.ec", "telefono": "+593991100001", "empresa": "Nova Labs", "cargo": "CTO", "segmento": "b2b", "estado": "identificado", "etapa": "en_calificacion", "consentimiento": (True, True), "senales": {"mensajes_intercambiados": 2, "num_colaboradores": 10, "presupuesto_capacitacion_usd": 1000, "horizonte": "mas_6m"}},
    {"nombre": "Lucía Torres", "email": "lucia.torres@ejemplo.ec", "telefono": "+593991100002", "empresa": "", "cargo": "", "segmento": "b2c", "estado": "identificado", "etapa": "calificado", "consentimiento": (True, True), "senales": {"completo_quiz": True, "mensajes_intercambiados": 8, "objetivo": "aprender", "monto_declarado_usd": 1000, "experiencia_inversion": "basica", "email_valido": True, "horizonte": "3-6m"}},
    {"nombre": "Diego Paredes", "email": "diego.paredes@andes.ec", "telefono": "+593991100003", "empresa": "Andes Logística", "cargo": "Compras", "segmento": "b2b", "estado": "identificado", "etapa": "listo_para_asesor", "consentimiento": (True, True), "senales": {"solicito_propuesta": True, "mensajes_intercambiados": 8, "objetivo": "capacitar_equipo", "num_colaboradores": 250, "presupuesto_capacitacion_usd": 12000, "es_decisor": True, "ruc_valido": True, "email_corporativo": True, "horizonte": "inmediato"}},
    {"nombre": "Valentina Ruiz", "empresa": "", "cargo": "", "segmento": "b2c", "estado": "anonimo", "etapa": "nuevo", "consentimiento": (False, False), "senales": {"mensajes_intercambiados": 1, "horizonte": "mas_6m"}},
    {"nombre": "Mateo Silva", "email": "mateo.silva@faro.ec", "telefono": "+593991100005", "empresa": "Faro Digital", "cargo": "Fundador", "segmento": "b2b", "estado": "identificado", "etapa": "educando", "consentimiento": (True, True), "senales": {"solicito_propuesta": True, "mensajes_intercambiados": 4, "objetivo": "capacitar_equipo", "num_colaboradores": 60, "presupuesto_capacitacion_usd": 6000, "es_decisor": True, "email_corporativo": True, "horizonte": "3-6m"}},
    {"nombre": "Elena Cevallos", "email": "elena.cevallos@ejemplo.ec", "telefono": "+593991100006", "empresa": "", "cargo": "", "segmento": "b2c", "estado": "identificado", "etapa": "educando", "consentimiento": (True, False), "senales": {"pidio_asesor": True, "completo_quiz": True, "mensajes_intercambiados": 4, "objetivo": "invertir", "monto_declarado_usd": 500, "experiencia_inversion": "basica", "email_valido": True, "horizonte": "3-6m"}},
    {"nombre": "Jorge Lema", "email": "jorge.lema@quipo.ec", "telefono": "+593991100007", "empresa": "Quipo", "cargo": "Director Comercial", "segmento": "b2b", "estado": "verificado", "etapa": "derivado", "consentimiento": (True, True), "senales": {"solicito_propuesta": True, "mensajes_intercambiados": 9, "objetivo": "capacitar_equipo", "num_colaboradores": 300, "presupuesto_capacitacion_usd": 15000, "es_decisor": True, "ruc_valido": True, "email_corporativo": True, "horizonte": "1-3m"}},
    {"nombre": "Natalia Vega", "email": "natalia.vega@ejemplo.ec", "telefono": "+593991100008", "empresa": "", "cargo": "", "segmento": "b2c", "estado": "identificado", "etapa": "nutricion", "consentimiento": (True, True), "senales": {"mensajes_intercambiados": 2, "horizonte": "mas_6m"}},
    {"nombre": "Ricardo Freire", "email": "ricardo.freire@altitud.ec", "telefono": "+593991100009", "empresa": "Altitud", "cargo": "CEO", "segmento": "b2b", "estado": "identificado", "etapa": "listo_para_asesor", "consentimiento": (True, True), "senales": {"solicito_propuesta": True, "mensajes_intercambiados": 10, "objetivo": "capacitar_equipo", "num_colaboradores": 220, "presupuesto_capacitacion_usd": 10000, "es_decisor": True, "ruc_valido": True, "email_corporativo": True, "horizonte": "inmediato"}},
]


def cargar_semillas() -> tuple[int, int]:
    """Upsert idempotente de los 12 leads de demo. Retorna creados/existentes."""
    Base.metadata.create_all(bind=engine)
    creados = existentes = 0
    with SessionLocal() as db:
        for item in SEMILLAS:
            email = item.get("email")
            email_normalizado = email.strip().lower() if email else None
            lead = (
                db.query(LeadV2).filter(LeadV2.email_normalizado == email_normalizado).first()
                if email_normalizado
                else db.query(LeadV2).filter(
                    LeadV2.nombre == item["nombre"],
                    LeadV2.estado_identificacion == "anonimo",
                ).first()
            )
            if not lead:
                lead = LeadV2(nombre=item["nombre"], email=email, email_normalizado=email_normalizado,
                              telefono=item.get("telefono"), empresa=item["empresa"] or None, cargo=item["cargo"] or None,
                              cedula=item.get("cedula"), estado_identificacion=item["estado"],
                              etapa_embudo=item["etapa"], segmento=item["segmento"])
                db.add(lead)
                db.flush()
                tratamiento, comunicaciones = item["consentimiento"]
                db.add(Consentimiento(lead_id=lead.id, tratamiento_datos_otorgado=tratamiento,
                                      comunicaciones_otorgado=comunicaciones,
                                      tratamiento_datos_fecha=datetime.now(timezone.utc) if tratamiento else None,
                                      comunicaciones_fecha=datetime.now(timezone.utc) if comunicaciones else None,
                                      version_politica="v1"))
                creados += 1
            else:
                existentes += 1
                lead.nombre = item["nombre"]
                lead.email = email
                lead.email_normalizado = email_normalizado
                lead.telefono = item.get("telefono")
                lead.cedula = item.get("cedula")
                lead.empresa = item["empresa"] or None
                lead.cargo = item["cargo"] or None
                lead.estado_identificacion = item["estado"]
                lead.etapa_embudo = item["etapa"]
                lead.segmento = item["segmento"]
                consentimiento = db.query(Consentimiento).filter(Consentimiento.lead_id == lead.id).first()
                tratamiento, comunicaciones = item["consentimiento"]
                if consentimiento:
                    consentimiento.tratamiento_datos_otorgado = tratamiento
                    consentimiento.comunicaciones_otorgado = comunicaciones
                else:
                    db.add(Consentimiento(lead_id=lead.id,
                                          tratamiento_datos_otorgado=tratamiento,
                                          comunicaciones_otorgado=comunicaciones,
                                          tratamiento_datos_fecha=datetime.now(timezone.utc) if tratamiento else None,
                                          comunicaciones_fecha=datetime.now(timezone.utc) if comunicaciones else None,
                                          version_politica="v1"))

            senales = db.query(SenalesLead).filter(SenalesLead.lead_id == lead.id).first()
            if senales:
                for campo, valor in item["senales"].items():
                    setattr(senales, campo, valor)
            else:
                senales = SenalesLead(lead_id=lead.id, **item["senales"])
                db.add(senales)
            db.flush()
            upsert_score(db, lead.id, senales, lead.segmento)
    return creados, existentes


if __name__ == "__main__":
    creados, existentes = cargar_semillas()
    print(f"Semillas listas: {creados} creados, {existentes} ya existentes.")
