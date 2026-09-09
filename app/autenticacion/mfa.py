"""
Segundo factor TOTP con pyotp.
Ventana de ±1 intervalo (30 s) para tolerar pequeños desfases de reloj
sin abrir demasiado la ventana de ataque.
"""
import pyotp


def validar_totp(secret: str, codigo: str) -> bool:
    """True si el código TOTP de 6 dígitos es válido para el secreto dado."""
    totp = pyotp.TOTP(secret)
    return totp.verify(codigo.strip(), valid_window=1)


def codigo_actual(secret: str) -> str:
    """Devuelve el código TOTP vigente. Solo para el panel de demo."""
    return pyotp.TOTP(secret).now()
