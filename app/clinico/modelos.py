"""
Modelos de dominio clínico — dataclasses puros.
Sin lógica de BD, sin seguridad, sin HTTP.
Son los objetos que viajan entre capas.
"""
from dataclasses import dataclass


@dataclass
class Paciente:
    id: str
    nombre: str
    fecha_nacimiento: str
    contacto: str | None = None


@dataclass
class NotaClinica:
    id: str
    paciente_id: str
    personal_id: str
    diagnostico: str
    tratamiento: str
    fecha: str
    hash_registro: str = ""
    firma_digital: str = ""
    # Campo extra para mostrar en UI — no se persiste en historial_clinico
    nombre_personal: str = ""
