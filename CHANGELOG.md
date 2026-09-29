# Changelog

## Unreleased — 2026-09-28

### Documentación y modelado de seguridad
- Revisión de STRIDE conforme al enfoque de modelado de amenazas de Microsoft.
- Mapeo MITRE ATT&CK corregido con nombres/IDs oficiales e incorporación de `T1539 — Steal Web Session Cookie`.
- Añadido **CIA+** como evaluación explícita de confidencialidad, integridad, disponibilidad, autenticidad, accountability/trazabilidad y no repudio; se documenta que CIA+ es una extensión de ingeniería del proyecto, no un estándar NIST independiente.
- Corregido **ITU-T X.800**: se conservan cinco familias básicas de servicios; detección de eventos, *security audit trail* y *security recovery* se clasifican como mecanismos/capacidades y no como servicios adicionales.
- Ampliado **Defense in Depth** conforme al enfoque NIST de personas, tecnología y operaciones.
- Añadidos `docs/marcos-seguridad.md` y fuentes oficiales.
- Actualizado `docs/modelo-amenazas.md`, `docs/seguridad.md`, `docs/matriz-cumplimiento.md` e informe técnico.
- Esta revisión es documental: **no cambia el comportamiento de runtime ni la versión funcional v1.1.0**.

## 1.1.0 — 2026-09-13

### Seguridad
- `DEMO_MODE` ahora es `false` por defecto.
- Eliminado el fallback de `SECRET_KEY`; el arranque falla con menos de 32 caracteres.
- TOTP cifrado en SQLite mediante AES-256-GCM con clave derivada por HKDF-SHA256.
- Llave privada JWT almacenada cifrada en PEM; permisos `0600` cuando el SO lo permite.
- Cookies de sesión, preautenticación y CSRF con endurecimiento configurable `Secure` y `SameSite=Strict`.
- Middleware de CSP, HSTS configurable, anti-framing, `nosniff`, `Referrer-Policy`, `Permissions-Policy` y `no-store`.
- JWT valida `iss`, `aud`, `nbf`, `exp` y claims obligatorios.
- Cada petición autenticada revalida que la cuenta siga activa y conserve el rol emitido.
- La cadena de auditoría incorpora `ip_origen` y usa delimitador canónico.
- `PASSWORD_OK` y `LOGIN_OK` separan primer factor de autenticación completa.
- Accesos denegados a administración/auditoría/demo quedan auditados.
- Panel de ataque demo limitado a doctor/admin.
- Visor TOTP deshabilitado por defecto y restringido a loopback.
- Contraseñas de semilla dejan de estar codificadas en el repositorio; se generan o inyectan por entorno.
- Contraseñas de alta no se vuelven a mostrar después del POST; mínimo 12 caracteres.
- Verificación de firmas históricas conserva validez aunque el firmante esté inactivo.

### Repositorio y documentación
- Añadidos STRIDE, MITRE ATT&CK, X.800 y Defense in Depth.
- Añadidos `SECURITY.md`, documentación técnica extendida y carpeta `evidencias/`.
- CI genera secretos efímeros; no contiene claves estáticas.
- Suite ampliada a 12 pruebas de integración/seguridad.

## 1.0.0
- Versión base de demostración con MFA, RSA-PSS, cadena de hashes, RBAC y pruebas smoke.
