"""
Rate limiting en memoria para el endpoint de login.
Bloquea por IP y por email después de MAX_INTENTOS fallos en VENTANA_SEG segundos.
Diseñado para un proceso único (uvicorn sin workers múltiples).
"""
import time
from collections import defaultdict
from threading import Lock

VENTANA_SEG  = 300   # ventana de observación: 5 minutos
MAX_INTENTOS = 5     # fallos antes de bloquear
BLOQUEO_SEG  = 900   # tiempo de bloqueo: 15 minutos

_intentos: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def _limpiar(clave: str, ahora: float) -> list[float]:
    recientes = [t for t in _intentos[clave] if ahora - t < VENTANA_SEG]
    _intentos[clave] = recientes
    return recientes


def esta_bloqueado(clave: str) -> bool:
    with _lock:
        recientes = _limpiar(clave, time.time())
        return len(recientes) >= MAX_INTENTOS


def registrar_fallo(clave: str) -> None:
    with _lock:
        _limpiar(clave, time.time())
        _intentos[clave].append(time.time())


def limpiar_exito(clave: str) -> None:
    with _lock:
        _intentos.pop(clave, None)


def segundos_restantes(clave: str) -> int:
    """Segundos hasta que se libere el bloqueo (aprox)."""
    with _lock:
        ahora = time.time()
        recientes = _limpiar(clave, ahora)
        if not recientes or len(recientes) < MAX_INTENTOS:
            return 0
        return max(0, int(VENTANA_SEG - (ahora - recientes[0])))
