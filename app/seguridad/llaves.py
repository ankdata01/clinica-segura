"""
Generación, cifrado y carga de llaves RSA.
Centralizar aquí evita que ninguna otra capa manipule PEM directamente.

Se usa RSA de 2048 bits porque cumple el estándar mínimo NIST para firmas
digitales en documentos médicos y es compatible con la mayoría de tokens HSM
en caso de que el proyecto escale a producción.
"""
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generar_par_rsa() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Genera un par RSA-2048. Devuelve (privada, publica)."""
    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return privada, privada.public_key()


def serializar_publica(publica: rsa.RSAPublicKey) -> str:
    """Convierte la llave pública a PEM en texto."""
    return publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def guardar_privada_cifrada(
    privada: rsa.RSAPrivateKey,
    ruta: Path,
    contrasena: str,
) -> None:
    """
    Serializa la llave privada y la cifra con la contraseña del usuario.
    BestAvailableEncryption usa AES-256-CBC con PBKDF2 (OpenSSL estándar).
    El servidor nunca puede descifrarla por sí solo: requiere la contraseña.
    """
    pem = privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.BestAvailableEncryption(
            contrasena.encode("utf-8")
        ),
    )
    ruta.write_bytes(pem)


def cargar_privada(ruta: Path, contrasena: str) -> rsa.RSAPrivateKey:
    """Descifra y carga la llave privada desde disco usando la contraseña del usuario."""
    pem = ruta.read_bytes()
    return serialization.load_pem_private_key(pem, password=contrasena.encode("utf-8"))


def cargar_publica_desde_pem(pem_str: str) -> rsa.RSAPublicKey:
    """Carga una llave pública desde su representación PEM en texto."""
    return serialization.load_pem_public_key(pem_str.encode("utf-8"))


def guardar_publica(publica: rsa.RSAPublicKey, ruta: Path) -> None:
    """Guarda la llave pública como PEM en la ruta indicada."""
    ruta.write_text(serializar_publica(publica), encoding="utf-8")


def guardar_privada_sin_cifrar(privada: rsa.RSAPrivateKey, ruta: Path) -> None:
    """Solo para la llave del servidor JWT — no contiene datos de pacientes."""
    pem = privada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    ruta.write_bytes(pem)
