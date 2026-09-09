"""
Emisión y validación de JWT con RS256.

RS256 usa firma asimétrica: la llave privada del servidor firma,
cualquiera con la llave pública puede verificar.
Ventaja sobre HS256: no hay secreto compartido que filtrar; la llave pública
puede distribuirse sin riesgo.
"""
import uuid
from datetime import datetime, timezone, timedelta

import jwt

from app.config import (
    LLAVE_SERVIDOR_PRIVADA,
    LLAVE_SERVIDOR_PUBLICA,
    JWT_ALGORITMO,
    JWT_EXPIRACION_MINUTOS,
)


def emitir(usuario: dict) -> str:
    """
    Genera un JWT firmado con RS256.
    Claims: sub, nombre, rol, iat, exp, jti (UUID único por token).
    """
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub":    usuario["id"],
        "nombre": usuario["nombre"],
        "rol":    usuario["rol"],
        "iat":    ahora,
        "exp":    ahora + timedelta(minutes=JWT_EXPIRACION_MINUTOS),
        "jti":    str(uuid.uuid4()),
    }
    llave_privada = LLAVE_SERVIDOR_PRIVADA.read_bytes()
    return jwt.encode(payload, llave_privada, algorithm=JWT_ALGORITMO)


def validar(token: str) -> dict:
    """
    Verifica la firma y la expiración del token.
    Lanza jwt.InvalidTokenError (y subclases) si el token es inválido.
    """
    llave_publica = LLAVE_SERVIDOR_PUBLICA.read_bytes()
    return jwt.decode(token, llave_publica, algorithms=[JWT_ALGORITMO])
