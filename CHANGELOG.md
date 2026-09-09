# Changelog

Todos los cambios relevantes del proyecto de demostración se documentan en este archivo.

## [1.0.0] - 2026-09-09

### Added

- Aplicación FastAPI/Jinja2 para expediente clínico simplificado.
- Autenticación con Argon2id y TOTP.
- Sesiones JWT firmadas con RS256.
- Firma de notas clínicas con RSA-PSS y SHA-256.
- Llaves privadas personales cifradas con contraseña.
- Control de acceso basado en roles.
- Bitácora SHA-256 encadenada con triggers SQLite contra `UPDATE` y `DELETE`.
- Panel de auditoría, verificación de integridad y exportación CSV.
- Panel de administración de usuarios.
- Panel de ataques simulados para la presentación.
- Pruebas automatizadas con Pytest.
- Workflow de GitHub Actions para Python 3.12.
- Documentación de arquitectura, seguridad, demo y revisión técnica.

### Security hardening incorporated before repository release

- Autorización aplicada a la exportación de auditoría.
- Matriz RBAC clínica alineada con la documentación.
- Validación CSRF en logout.
- Bloqueo de 15 minutos después de cinco fallos en la ventana definida.
- Validación de `hash_anterior` en el verificador.
- Escrituras de auditoría serializadas con `BEGIN IMMEDIATE`.
- Manejo seguro de firmas Base64 dañadas.
- Prevención de duplicados de email para cuentas inactivas.
- Restauración de demo con invalidación de sesión anterior.
