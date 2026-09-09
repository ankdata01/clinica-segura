"""
Fábrica de conexiones SQLite.
Es el único lugar donde se configura row_factory y PRAGMA foreign_keys.
Ninguna otra capa abre conexiones directamente.
"""
import sqlite3
from app.config import DB_PATH


def obtener_conexion() -> sqlite3.Connection:
    """Devuelve una conexión configurada con foreign keys y row_factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
