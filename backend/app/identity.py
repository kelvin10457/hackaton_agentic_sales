"""Puerto de identidad para intercambiar el proveedor sin tocar los routers.

El adaptador local valida formato y dígitos verificadores; un proveedor real
(Registro Civil/SRI) puede implementar el mismo ``IdentityPort`` después.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from validators import clasificar_documento


@dataclass(frozen=True)
class ResolucionIdentidad:
    documento: str
    valido: bool
    tipo: str
    mensaje: str


class IdentityPort(ABC):
    """Puerto 1: resuelve y valida la identidad asociada a un documento."""

    @abstractmethod
    def resolver(self, documento: str) -> ResolucionIdentidad:
        """Devuelve el resultado de resolver una cédula o RUC."""


class IdentityLocal(IdentityPort):
    """Adaptador de demo, sin consultas externas ni datos personales remotos."""

    def resolver(self, documento: str) -> ResolucionIdentidad:
        documento = documento.strip()
        tipo = clasificar_documento(documento)
        valido = tipo != "invalido"
        mensajes = {
            "cedula": "Cédula ecuatoriana válida (módulo 10).",
            "ruc_natural": "RUC de persona natural válido.",
            "ruc_juridico": "RUC de persona jurídica privada válido.",
            "ruc_publico": "RUC de entidad pública válido.",
            "invalido": "Documento inválido. Verifica dígito verificador y provincia.",
        }
        return ResolucionIdentidad(documento, valido, tipo, mensajes[tipo])


_identity_port: IdentityPort = IdentityLocal()


def get_identity_port() -> IdentityPort:
    """Dependency factory; sustituible en tests o por un adaptador externo."""
    return _identity_port
