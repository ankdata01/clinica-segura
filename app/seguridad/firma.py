"""
Strategy de firma digital.

Se usa RSA-PSS en lugar de PKCS#1 v1.5 porque PSS tiene una prueba de
seguridad formal en el modelo de oráculo aleatorio, mientras que PKCS#1 v1.5
tiene vulnerabilidades conocidas (p.ej. el ataque de Bleichenbacher).
PSS es el estándar recomendado por NIST SP 800-131A y ECRYPT.

Interfaz común (protocolo):
    firmar(llave_privada, hash_bytes) -> bytes
    verificar(llave_publica, hash_bytes, firma_bytes) -> bool

Implementaciones:
    FirmaRSA   — RSA-PSS con SHA-256 (producción)
    FirmaECDSA — ECDSA con SHA-256 (alternativa, no activa en la demo)
"""
import hashlib
import base64
from abc import ABC, abstractmethod

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, utils, ec
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.exceptions import InvalidSignature


# ---------------------------------------------------------------------------
# Canonicalización — fuente única de verdad
# Cualquier cambio aquí invalida TODAS las firmas existentes.
# ---------------------------------------------------------------------------
def canonicalizar_nota(
    paciente_id: str,
    personal_id: str,
    diagnostico: str,
    tratamiento: str,
    fecha_iso: str,
) -> str:
    """
    Concatena los campos de una nota con '|' como separador.
    Es la única definición de 'contenido canónico' en el sistema.
    Se usa al firmar y al verificar.
    """
    return "|".join([paciente_id, personal_id, diagnostico, tratamiento, fecha_iso])


def hash_de_contenido(contenido_canonico: str) -> bytes:
    """SHA-256 del contenido canónico. Devuelve bytes crudos."""
    return hashlib.sha256(contenido_canonico.encode("utf-8")).digest()


# ---------------------------------------------------------------------------
# Interfaz Strategy
# ---------------------------------------------------------------------------
class EstrategiaFirma(ABC):
    @abstractmethod
    def firmar(self, llave_privada, hash_bytes: bytes) -> bytes:
        """Firma hash_bytes con la llave privada. Devuelve bytes de firma."""

    @abstractmethod
    def verificar(self, llave_publica, hash_bytes: bytes, firma_bytes: bytes) -> bool:
        """True si la firma es válida; False si no."""


# ---------------------------------------------------------------------------
# Implementación RSA-PSS (activa por defecto)
# ---------------------------------------------------------------------------
class FirmaRSA(EstrategiaFirma):
    def firmar(self, llave_privada: RSAPrivateKey, hash_bytes: bytes) -> bytes:
        return llave_privada.sign(
            hash_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            utils.Prehashed(hashes.SHA256()),
        )

    def verificar(
        self, llave_publica: RSAPublicKey, hash_bytes: bytes, firma_bytes: bytes
    ) -> bool:
        try:
            llave_publica.verify(
                firma_bytes,
                hash_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                utils.Prehashed(hashes.SHA256()),
            )
            return True
        except InvalidSignature:
            return False


# ---------------------------------------------------------------------------
# Implementación ECDSA (alternativa — no activa en la demo)
# ---------------------------------------------------------------------------
class FirmaECDSA(EstrategiaFirma):
    def firmar(self, llave_privada: ec.EllipticCurvePrivateKey, hash_bytes: bytes) -> bytes:
        return llave_privada.sign(hash_bytes, ec.ECDSA(utils.Prehashed(hashes.SHA256())))

    def verificar(
        self, llave_publica: ec.EllipticCurvePublicKey, hash_bytes: bytes, firma_bytes: bytes
    ) -> bool:
        try:
            llave_publica.verify(
                firma_bytes, hash_bytes, ec.ECDSA(utils.Prehashed(hashes.SHA256()))
            )
            return True
        except InvalidSignature:
            return False


# ---------------------------------------------------------------------------
# Helpers de alto nivel (usan FirmaRSA por defecto)
# ---------------------------------------------------------------------------
_estrategia_activa: EstrategiaFirma = FirmaRSA()


def firmar_nota(llave_privada: RSAPrivateKey, hash_bytes: bytes) -> str:
    """Firma y devuelve la firma en base64 lista para guardar en BD."""
    firma_bytes = _estrategia_activa.firmar(llave_privada, hash_bytes)
    return base64.b64encode(firma_bytes).decode("utf-8")


def verificar_firma(llave_publica: RSAPublicKey, hash_bytes: bytes, firma_b64: str) -> bool:
    """Verifica una firma almacenada en base64."""
    firma_bytes = base64.b64decode(firma_b64)
    return _estrategia_activa.verificar(llave_publica, hash_bytes, firma_bytes)
