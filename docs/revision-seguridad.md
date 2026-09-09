# Revisión de seguridad y hardening

## Propósito

Este documento resume ajustes incorporados durante la revisión técnica previa a la creación del repositorio de demostración.

No representa una auditoría formal de conformidad ni certifica el sistema para uso clínico real.

## Correcciones incorporadas

| Área | Corrección |
|---|---|
| Autorización | Se protegió la exportación `/auditoria/exportar.csv` con la misma política RBAC de auditoría |
| RBAC clínico | Se alineó el acceso a expedientes: doctor, enfermero y administrativo pueden consultar; admin no |
| Manejo de rutas | Se corrigió el uso de `RedirectResponse` en auditoría |
| CSRF | Logout valida el token CSRF antes de invalidar la sesión |
| Rate limiting | Cinco fallos dentro de cinco minutos producen un bloqueo completo de 15 minutos |
| Cadena hash | El verificador comprueba explícitamente el `hash_anterior` almacenado |
| Concurrencia | Las inserciones de auditoría utilizan `BEGIN IMMEDIATE` para encadenar de forma serializada |
| Orden de auditoría | La verificación usa orden de inserción en lugar de depender únicamente del timestamp |
| Firma | Una firma Base64 corrupta se informa como inválida en vez de provocar una excepción no controlada |
| Usuarios | El alta detecta emails duplicados incluso cuando la cuenta previa está inactiva |
| Restauración | Restaurar la demo invalida la sesión previa porque la semilla regenera identidad y claves |
| SQLite/Windows | La restauración evita mantener una conexión innecesaria mientras sustituye la base de datos |

## Pruebas asociadas

`tests/test_smoke.py` verifica actualmente:

1. creación de la semilla e integridad inicial;
2. MFA y emisión de sesión;
3. matriz de autorización crítica;
4. CSRF en logout;
5. bloqueo de 15 minutos;
6. 20 escrituras concurrentes de auditoría;
7. detección de `hash_anterior` manipulado;
8. invalidación de sesión tras restaurar la demo.

## Riesgos aceptados para la demostración

Los siguientes puntos permanecen deliberadamente fuera del hardening actual:

- `DEMO_MODE=true` puede exponer TOTP vigentes mediante `/demo/codigos`.
- La clave privada RSA del servidor se almacena localmente sin cifrar.
- HTTP local implica cookies sin atributo `Secure`.
- Existe un `SECRET_KEY` de desarrollo como fallback si no se configura el entorno.
- SQLite + triggers demuestra inmutabilidad lógica, no inmutabilidad física.
- Nota clínica y auditoría no comparten todavía una única transacción atómica.
- `ip_origen` no participa en el hash actual de auditoría.
- El rate limiter es local al proceso y no es adecuado para un despliegue multi-worker.
- Algunas rutas de presentación aún construyen repositorios o llaman primitivas de seguridad directamente, por lo que la Factory es el punto principal, pero no exclusivo, de composición.

## Criterio de presentación

Durante la exposición estos puntos deben comunicarse como **límites de una demo académica**, no como capacidades de producción. La transparencia sobre el alcance forma parte del análisis de seguridad.
