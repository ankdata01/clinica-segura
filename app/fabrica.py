"""
Factory — único punto de ensamblado de dependencias.

Ninguna ruta instancia repositorios ni servicios directamente.
Todo pasa por aquí, lo que hace que cambiar una implementación
(p. ej. sustituir FirmaRSA por FirmaECDSA) sea un cambio de una línea.

Uso típico en una ruta FastAPI:
    fab = Fabrica(con)
    paciente, notas = fab.servicio_clinico().obtener_historial(id, personal_id, ip)
"""
import sqlite3

from app.autenticacion.servicio_auth import ServicioAuth
from app.clinico.servicio_clinico import ServicioClinico
from app.datos.repo_auditoria import RepoAuditoria
from app.datos.repo_historial import RepoHistorial
from app.datos.repo_pacientes import RepoPacientes
from app.datos.repo_personal import RepoPersonal
from app.seguridad.decorador_auditoria import AuditoriaDecorator
from app.seguridad.verificador import verificar_todo


class Fabrica:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._con = conexion
        # Los repos se crean una sola vez por petición para compartir conexión
        self._repo_personal   = RepoPersonal(conexion)
        self._repo_pacientes  = RepoPacientes(conexion)
        self._repo_historial  = RepoHistorial(conexion)
        self._repo_auditoria  = RepoAuditoria(conexion)

    def servicio_clinico(self) -> AuditoriaDecorator:
        """Devuelve el ServicioClinico envuelto con el Decorator de auditoría."""
        svc = ServicioClinico(self._repo_pacientes, self._repo_historial)
        return AuditoriaDecorator(svc, self._repo_auditoria)

    def servicio_auth(self) -> ServicioAuth:
        """Devuelve el ServicioAuth con sus repositorios inyectados."""
        return ServicioAuth(self._repo_personal, self._repo_auditoria)

    def repo_personal(self) -> RepoPersonal:
        """Acceso directo al repo de personal (para rutas de demo y verificación)."""
        return self._repo_personal

    def repo_auditoria(self) -> RepoAuditoria:
        """Acceso directo al repo de auditoría (para la vista de bitácora)."""
        return self._repo_auditoria

    def ejecutar_verificacion(self) -> dict:
        """Atajo para verificar cadena + firmas desde cualquier ruta."""
        return verificar_todo(
            self._repo_auditoria,
            self._repo_historial,
            self._repo_personal,
        )
