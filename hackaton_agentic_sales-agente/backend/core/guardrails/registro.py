"""
G8 · Auditoría de guardrails — Biblia §10, Manual R1 §9.

FIJO: "Todo guardrail que se dispara genera un EventoAuditoria. Sin excepción."

Regla arquitectónica sagrada: core/ NO importa nada de app/ (la bitácora vive
en app/auditoria.py). Por eso core NO escribe en la BD directamente: emite un
objeto `DisparoGuardrail` y la capa de API (routers/chat.py, que sí puede
importar app/ y core/) lo persiste como EventoAuditoria. Así la dirección de
dependencia se mantiene: api → core → tools → schemas.
"""
from dataclasses import dataclass, field


@dataclass
class DisparoGuardrail:
    """Un evento de guardrail listo para auditar (lo persiste la capa API)."""
    guardrail: str          # "G1" | "G1-bis" | "G2" | "G5" | "G6" | "G7" ...
    motivo: str             # descripción legible del disparo
    consulta: str = ""      # fragmento del mensaje/salida que lo activó
    metadato: dict = field(default_factory=dict)

    def a_payload(self) -> dict:
        """Forma serializable para el payload del EventoAuditoria."""
        return {
            "guardrail": self.guardrail,
            "motivo": self.motivo,
            "consulta": self.consulta[:200],
            **self.metadato,
        }


def nuevo_disparo(guardrail: str, motivo: str, consulta: str = "", **metadato) -> DisparoGuardrail:
    return DisparoGuardrail(guardrail=guardrail, motivo=motivo, consulta=consulta, metadato=metadato)
