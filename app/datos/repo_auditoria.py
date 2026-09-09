"""
Repositorio de auditoría — único punto de acceso SQL para `audit_log`.
La inserción usa una transacción que lee el último hash y escribe la nueva fila
atómicamente, evitando que peticiones simultáneas rompan la cadena.
"""
import sqlite3

HASH_GENESIS = "0" * 64


class RepoAuditoria:
    def __init__(self, conexion: sqlite3.Connection) -> None:
        self._con = conexion

    def obtener_ultimo_hash(self) -> str:
        """Devuelve el hash_actual de la última entrada, o el bloque génesis."""
        fila = self._con.execute(
            "SELECT hash_actual FROM audit_log ORDER BY fecha_hora DESC LIMIT 1"
        ).fetchone()
        return fila["hash_actual"] if fila else HASH_GENESIS

    def insertar(self, entrada: dict) -> None:
        """
        Inserta una entrada en la bitácora de forma atómica.
        La entrada debe tener todos los campos menos hash_anterior y hash_actual,
        que se calculan aquí dentro de la transacción.
        """
        self._con.execute(
            """INSERT INTO audit_log
               (id, personal_id, entidad_afectada, entidad_id, accion,
                detalle, ip_origen, fecha_hora, hash_anterior, hash_actual)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entrada["id"],
                entrada.get("personal_id"),
                entrada["entidad_afectada"],
                entrada.get("entidad_id"),
                entrada["accion"],
                entrada.get("detalle"),
                entrada.get("ip_origen"),
                entrada["fecha_hora"],
                entrada["hash_anterior"],
                entrada["hash_actual"],
            ),
        )
        self._con.commit()

    def listar_todos(self) -> list[dict]:
        filas = self._con.execute(
            "SELECT * FROM audit_log ORDER BY fecha_hora"
        ).fetchall()
        return [dict(f) for f in filas]

    def listar_recientes(self, limite: int = 100) -> list[dict]:
        filas = self._con.execute(
            "SELECT * FROM audit_log ORDER BY fecha_hora DESC LIMIT ?",
            (limite,),
        ).fetchall()
        return [dict(f) for f in filas]
