"""
Decorator de auditoría — patrón Decorator sobre ServicioClinico.

Envuelve al servicio con la misma interfaz pública y agrega el registro
en la bitácora después de cada operación, sin que ServicioClinico lo sepa.
La Factory es quien decide envolverlo; ninguna ruta instancia este decorador
directamente.

Los métodos del decorador aceptan personal_id e ip además de los parámetros
normales del servicio; esos datos extra son solo para la auditoría y nunca
llegan al servicio interno.
"""
from datetime import datetime, timezone

from app.clinico.modelos import Paciente, NotaClinica
from app.clinico.servicio_clinico import ServicioClinico
from app.datos.repo_auditoria import RepoAuditoria


class AuditoriaDecorator:
    def __init__(
        self,
        servicio: ServicioClinico,
        repo_auditoria: RepoAuditoria,
    ) -> None:
        self._svc = servicio
        self._audit = repo_auditoria

    # ------------------------------------------------------------------
    # Métodos del servicio clínico — misma interfaz, auditoría agregada
    # ------------------------------------------------------------------

    def listar_pacientes(self) -> list[Paciente]:
        """Listar pacientes no genera entrada de auditoría (no es acceso a expediente)."""
        return self._svc.listar_pacientes()

    def obtener_historial(
        self,
        paciente_id: str,
        personal_id: str,
        ip: str,
    ) -> tuple[Paciente, list[NotaClinica]]:
        """
        Consultar un historial sí se audita: saber quién leyó un expediente
        importa tanto como saber quién lo escribió (requisito NOM-024).
        """
        resultado = self._svc.obtener_historial(paciente_id)
        self._auditar(
            personal_id=personal_id,
            entidad_afectada="historial_clinico",
            entidad_id=paciente_id,
            accion="CONSULTAR_HISTORIAL",
            detalle=None,
            ip=ip,
        )
        return resultado

    def crear_nota(
        self,
        nota: NotaClinica,
        personal_id: str,
        ip: str,
    ) -> NotaClinica:
        resultado = self._svc.crear_nota(nota)
        self._auditar(
            personal_id=personal_id,
            entidad_afectada="historial_clinico",
            entidad_id=nota.id,
            accion="CREAR_NOTA",
            detalle=f"Paciente {nota.paciente_id[:8]}…",
            ip=ip,
        )
        return resultado

    # ------------------------------------------------------------------
    # Auditoría interna
    # ------------------------------------------------------------------
    def _auditar(
        self,
        personal_id: str,
        entidad_afectada: str,
        entidad_id: str | None,
        accion: str,
        detalle: str | None,
        ip: str,
    ) -> None:
        fecha_hora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._audit.insertar_encadenado(
            personal_id=personal_id,
            entidad_afectada=entidad_afectada,
            entidad_id=entidad_id,
            accion=accion,
            detalle=detalle,
            ip_origen=ip,
            fecha_hora=fecha_hora,
        )
