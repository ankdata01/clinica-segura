"""
Configuración centralizada del proyecto.
Todas las rutas de archivos y parámetros de seguridad viven aquí.
Ninguna otra capa debe hardcodear rutas ni constantes de configuración.
"""
from pathlib import Path
import os

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent

DB_PATH = BASE_DIR / "db" / "clinica.db"
ESQUEMA_SQL_PATH = BASE_DIR / "db" / "esquema.sql"
LLAVES_DIR = BASE_DIR / "llaves"
PLANTILLAS_DIR = Path(__file__).parent / "plantillas"
ESTATICOS_DIR = Path(__file__).parent / "estaticos"

LLAVE_SERVIDOR_PRIVADA = LLAVES_DIR / "servidor_privada.pem"
LLAVE_SERVIDOR_PUBLICA = LLAVES_DIR / "servidor_publica.pem"

# ---------------------------------------------------------------------------
# Modo demostración
# Solo cuando DEMO_MODE=true se montan /demo y sus subrutas.
# En un entorno real esto estaría en false desde el primer día.
# ---------------------------------------------------------------------------
DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

# ---------------------------------------------------------------------------
# JWT (RS256 — firma asimétrica, sin secreto compartido)
# ---------------------------------------------------------------------------
JWT_ALGORITMO = "RS256"
JWT_EXPIRACION_MINUTOS = 30

# ---------------------------------------------------------------------------
# Cookie del primer factor (itsdangerous) — antes de verificar TOTP
# Caduca en 5 minutos para reducir la ventana de ataque.
# ---------------------------------------------------------------------------
COOKIE_PREFACTOR_NOMBRE = "pre_auth"
COOKIE_PREFACTOR_SEGUNDOS = 300

# Cookie que transporta el JWT final
COOKIE_TOKEN_NOMBRE = "token"

# Clave para firmar la cookie temporal.
# En producción DEBE provenir de una variable de entorno.
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-not-for-production")
