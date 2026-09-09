"""
Cálculo del hash encadenado de la bitácora de auditoría.
Esta función es la única fuente de verdad para la fórmula de encadenamiento.
Usarla tanto al insertar como al verificar garantiza consistencia.
"""
import hashlib


def calcular_hash(
    hash_anterior: str,
    id: str,
    personal_id: str | None,
    entidad_afectada: str,
    entidad_id: str | None,
    accion: str,
    detalle: str | None,
    fecha_hora: str,
) -> str:
    """
    SHA-256 sobre la concatenación de todos los campos de la entrada.
    Si algún campo opcional es None, se trata como cadena vacía para
    que la fórmula sea determinista independientemente del motor de BD.
    """
    contenido = (
        hash_anterior
        + id
        + (personal_id or "")
        + entidad_afectada
        + (entidad_id or "")
        + accion
        + (detalle or "")
        + fecha_hora
    )
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()
