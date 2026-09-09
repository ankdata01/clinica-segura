"""
Dependencias compartidas entre rutas protegidas.

usuario_actual: valida el JWT en cada petición protegida.
dep_conexion:   abre y cierra la conexión SQLite por petición.
Utilidades CSRF: patrón double-submit cookie.
"""
import secrets

import jwt
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.autenticacion import tokens
from app.config import COOKIE_TOKEN_NOMBRE
from app.datos.conexion import obtener_conexion


# ---------------------------------------------------------------------------
# Excepción de autenticación — capturada por el handler en main.py
# ---------------------------------------------------------------------------
class NoAutenticado(Exception):
    pass


# ---------------------------------------------------------------------------
# Dependencia de conexión SQLite (generador para FastAPI Depends)
# ---------------------------------------------------------------------------
def dep_conexion():
    """Una conexión por petición HTTP; se cierra automáticamente al terminar."""
    con = obtener_conexion()
    try:
        yield con
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Dependencia de usuario autenticado
# ---------------------------------------------------------------------------
async def usuario_actual(request: Request) -> dict:
    """
    Extrae el JWT de la cookie, verifica firma y expiración.
    Lanza NoAutenticado si falta, expiró o fue alterado.
    La capa de presentación nunca toca jwt directamente.
    """
    token = request.cookies.get(COOKIE_TOKEN_NOMBRE)
    if not token:
        raise NoAutenticado()
    try:
        return tokens.validar(token)
    except jwt.ExpiredSignatureError:
        raise NoAutenticado()
    except jwt.InvalidTokenError:
        raise NoAutenticado()


# ---------------------------------------------------------------------------
# Utilidades CSRF — patrón double-submit cookie
# ---------------------------------------------------------------------------
COOKIE_CSRF = "csrf_token"


def generar_csrf() -> str:
    """Token aleatorio de 32 bytes en hex."""
    return secrets.token_hex(32)


def validar_csrf(request: Request, token_formulario: str | None) -> bool:
    """
    Compara el token del formulario con el de la cookie.
    SameSite=Strict en la cookie ya mitiga CSRF; este check es la segunda capa.
    """
    token_cookie = request.cookies.get(COOKIE_CSRF)
    if not token_cookie or not token_formulario:
        return False
    return secrets.compare_digest(token_cookie, token_formulario)


def set_csrf_cookie(response, token: str) -> None:
    """Adjunta el token CSRF en la cookie de respuesta."""
    response.set_cookie(
        COOKIE_CSRF,
        token,
        httponly=False,   # JS no lo necesita; False para poder leerlo en tests
        samesite="strict",
        max_age=3600,
    )
