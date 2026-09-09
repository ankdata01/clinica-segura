"""
Rate limiting en memoria para login y MFA.

Política:
- Se observan fallos dentro de una ventana de 5 minutos.
- Al alcanzar 5 fallos, la clave queda bloqueada 15 minutos completos.
- Se puede usar una clave por IP, email o user_id.

Diseñado para un único proceso de Uvicorn. Con múltiples workers debe
sustituirse por un almacén compartido (por ejemplo, Redis).
"""
import time
from collections import defaultdict
from threading import Lock

VENTANA_SEG = 300
MAX_INTENTOS = 5
BLOQUEO_SEG = 900

_intentos: dict[str, list[float]] = defaultdict(list)
_bloqueado_hasta: dict[str, float] = {}
_lock = Lock()


def _limpiar_fallos(clave: str, ahora: float) -> list[float]:
    recientes = [t for t in _intentos[clave] if ahora - t < VENTANA_SEG]
    if recientes:
        _intentos[clave] = recientes
    else:
        _intentos.pop(clave, None)
    return recientes


def _limpiar_bloqueo_expirado(clave: str, ahora: float) -> None:
    hasta = _bloqueado_hasta.get(clave)
    if hasta is not None and hasta <= ahora:
        _bloqueado_hasta.pop(clave, None)
        _intentos.pop(clave, None)


def esta_bloqueado(clave: str) -> bool:
    with _lock:
        ahora = time.time()
        _limpiar_bloqueo_expirado(clave, ahora)
        return _bloqueado_hasta.get(clave, 0.0) > ahora


def registrar_fallo(clave: str) -> None:
    with _lock:
        ahora = time.time()
        _limpiar_bloqueo_expirado(clave, ahora)
        recientes = _limpiar_fallos(clave, ahora)
        recientes.append(ahora)
        _intentos[clave] = recientes
        if len(recientes) >= MAX_INTENTOS:
            _bloqueado_hasta[clave] = ahora + BLOQUEO_SEG


def limpiar_exito(clave: str) -> None:
    with _lock:
        _intentos.pop(clave, None)
        _bloqueado_hasta.pop(clave, None)


def segundos_restantes(clave: str) -> int:
    """Segundos restantes del bloqueo activo, redondeados hacia abajo."""
    with _lock:
        ahora = time.time()
        _limpiar_bloqueo_expirado(clave, ahora)
        hasta = _bloqueado_hasta.get(clave)
        if hasta is None:
            return 0
        return max(0, int(hasta - ahora))
