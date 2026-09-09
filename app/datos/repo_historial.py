"""
Repositorio de historial clínico — único punto de acceso SQL para `historial_clinico`.
"""
import sqlite3


class RepoHistorial:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._con = conexion

    def obtener_por_paciente(self, paciente_id: str) -> list[dict]:
        filas = self._con.execute(
            """SELECT h.*, p.nombre AS nombre_personal
               FROM historial_clinico h
               JOIN personal p ON h.personal_id = p.id
               WHERE h.paciente_id = ?
               ORDER BY h.fecha DESC""",
            (paciente_id,),
        ).fetchall()
        return [dict(f) for f in filas]

    def obtener_por_id(self, id: str) -> dict | None:
        fila = self._con.execute(
            "SELECT * FROM historial_clinico WHERE id = ?",
            (id,),
        ).fetchone()
        return dict(fila) if fila else None

    def obtener_todos(self) -> list[dict]:
        """Para el verificador: recorre todos los registros en orden cronológico."""
        filas = self._con.execute(
            "SELECT * FROM historial_clinico ORDER BY fecha"
        ).fetchall()
        return [dict(f) for f in filas]

    def crear(self, nota: dict) -> None:
        """
        Inserta una nota clínica ya firmada.
        El dict debe tener todas las columnas de historial_clinico.
        """
        self._con.execute(
            """INSERT INTO historial_clinico
               (id, paciente_id, personal_id, diagnostico, tratamiento,
                fecha, hash_registro, firma_digital)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                nota["id"],
                nota["paciente_id"],
                nota["personal_id"],
                nota["diagnostico"],
                nota["tratamiento"],
                nota["fecha"],
                nota["hash_registro"],
                nota["firma_digital"],
            ),
        )
        self._con.commit()
