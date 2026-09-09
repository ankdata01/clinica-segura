"""
Servicio clínico — lógica de negocio pura.

REGLA ARQUITECTÓNICA: este archivo no importa nada de seguridad, auditoría
ni HTTP. No hay hashlib, no hay firma, no hay INSERT en audit_log.
Si ves alguno de esos en este archivo, la arquitectura se rompió.

El Decorator (Fase 4) agrega la auditoría desde fuera, sin modificar este código.
La firma se calcula en la capa de presentación antes de llamar a crear_nota(),
porque requiere la contraseña del usuario que solo pasa por la petición HTTP.
"""
from app.clinico.modelos import Paciente, NotaClinica
from app.datos.repo_pacientes import RepoPacientes
from app.datos.repo_historial import RepoHistorial


# ---------------------------------------------------------------------------
# Excepciones de dominio
# ---------------------------------------------------------------------------
class PacienteNoEncontrado(Exception):
    """El paciente_id no existe en la base de datos."""


class RolSinPermiso(Exception):
    """El rol del usuario no tiene permiso para esta operación."""


# ---------------------------------------------------------------------------
# Servicio
# ---------------------------------------------------------------------------
class ServicioClinico:
    def __init__(
        self,
        repo_pacientes: RepoPacientes,
        repo_historial: RepoHistorial,
    ) -> None:
        self._pacientes = repo_pacientes
        self._historial = repo_historial

    def listar_pacientes(self) -> list[Paciente]:
        """Devuelve todos los pacientes ordenados por nombre."""
        filas = self._pacientes.listar_todos()
        return [
            Paciente(
                id=f["id"],
                nombre=f["nombre"],
                fecha_nacimiento=f["fecha_nacimiento"],
                contacto=f["contacto"],
            )
            for f in filas
        ]

    def obtener_historial(self, paciente_id: str) -> tuple[Paciente, list[NotaClinica]]:
        """
        Devuelve el paciente y su historial clínico.
        Lanza PacienteNoEncontrado si el id no existe.
        """
        fila_pac = self._pacientes.obtener_por_id(paciente_id)
        if fila_pac is None:
            raise PacienteNoEncontrado(paciente_id)

        paciente = Paciente(
            id=fila_pac["id"],
            nombre=fila_pac["nombre"],
            fecha_nacimiento=fila_pac["fecha_nacimiento"],
            contacto=fila_pac["contacto"],
        )

        notas = [
            NotaClinica(
                id=f["id"],
                paciente_id=f["paciente_id"],
                personal_id=f["personal_id"],
                diagnostico=f["diagnostico"],
                tratamiento=f["tratamiento"],
                fecha=f["fecha"],
                hash_registro=f["hash_registro"],
                firma_digital=f["firma_digital"],
                nombre_personal=f.get("nombre_personal", ""),
            )
            for f in self._historial.obtener_por_paciente(paciente_id)
        ]

        return paciente, notas

    def crear_nota(self, nota: NotaClinica) -> NotaClinica:
        """
        Persiste una nota clínica ya firmada.
        Recibe la nota con hash_registro y firma_digital precalculados
        (lo hace la capa de presentación antes de llamar aquí).
        Solo guarda — no firma, no audita.
        """
        self._historial.crear({
            "id":            nota.id,
            "paciente_id":   nota.paciente_id,
            "personal_id":   nota.personal_id,
            "diagnostico":   nota.diagnostico,
            "tratamiento":   nota.tratamiento,
            "fecha":         nota.fecha,
            "hash_registro": nota.hash_registro,
            "firma_digital": nota.firma_digital,
        })
        return nota
