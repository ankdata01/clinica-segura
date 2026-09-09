"""
Repositorio de pacientes — único punto de acceso SQL para la tabla `pacientes`.
"""
import sqlite3


class RepoPacientes:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._con = conexion

    def listar_todos(self) -> list[dict]:
        filas = self._con.execute(
            "SELECT * FROM pacientes ORDER BY nombre"
        ).fetchall()
        return [dict(f) for f in filas]

    def obtener_por_id(self, id: str) -> dict | None:
        fila = self._con.execute(
            "SELECT * FROM pacientes WHERE id = ?",
            (id,),
        ).fetchone()
        return dict(fila) if fila else None
