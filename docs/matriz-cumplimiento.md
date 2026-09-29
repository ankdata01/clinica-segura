# Matriz de cumplimiento de la entrega

Esta matriz relaciona los requisitos académicos de la actualización con los artefactos de **Sistema Seguro: Hospital v1.1.0**.

## Estructura del documento

| Requisito | Ubicación | Estado |
|---|---|---|
| Portada | Informe académico corregido (entregable DOCX externo) | Cumplido |
| Resumen | Informe académico corregido | Cumplido |
| Introducción | Informe académico corregido | Cumplido |
| Descripción del sistema | Informe académico corregido | Cumplido |
| Arquitectura | Informe + `docs/arquitectura.md` | Cumplido |
| Modelo STRIDE | Informe + `docs/modelo-amenazas.md` | Cumplido |
| MITRE ATT&CK | Informe + `docs/modelo-amenazas.md` | Cumplido |
| CIA+ | Informe + `docs/modelo-amenazas.md` + `docs/marcos-seguridad.md` | Cumplido |
| ITU-T X.800 | Informe + `docs/modelo-amenazas.md` | Cumplido; corregida distinción servicio/mecanismo |
| Defense in Depth | Informe + `docs/modelo-amenazas.md` | Cumplido; cobertura de personas, tecnología y operaciones |
| Implementación de controles | Informe + `docs/seguridad.md` + código | Cumplido |
| Pruebas y validación | Informe + `TESTING.md` + `tests/` | Cumplido |
| Resultados | Informe + `evidencias/` | Cumplido |
| Conclusiones | Informe académico corregido | Cumplido |
| Referencias | Informe + `docs/marcos-seguridad.md` | Cumplido |

## Repositorio GitHub

| Requisito | Evidencia | Estado |
|---|---|---|
| Anexos/código o carpeta de código | `app/`, `db/`, `tests/`, `docs/anexos-codigo.md` | Cumplido |
| Código comentado | Docstrings y comentarios en módulos críticos | Cumplido |
| README con instrucciones para ejecutar | `README.md` | Cumplido |
| Configuración sin contraseñas ni claves reales | `.env.example`, `.gitignore`, secretos efímeros de CI | Cumplido |
| Evidencias de pruebas | `evidencias/resultado-validacion.txt`, CI y `tests/test_smoke.py` | Cumplido |
| Fuentes oficiales de marcos | `docs/marcos-seguridad.md` | Cumplido |
| Informe técnico alineado | `docs/informe-tecnico-extendido.md` | Cumplido |

## Correcciones documentales de 2026-09-28

- CIA+ se incorporó explícitamente y se aclaró que es una extensión de ingeniería del proyecto, no un estándar NIST independiente.
- STRIDE quedó alineado con las seis categorías y su propiedad de seguridad asociada.
- MITRE ATT&CK usa nombres e identificadores oficiales de las técnicas mapeadas e incorpora T1539 para robo de cookie de sesión.
- X.800 se corrigió para conservar cinco familias básicas de servicios; auditoría/detección y recuperación se clasifican como mecanismos/capacidades, no como servicios adicionales.
- Defense in Depth se amplió a personas, tecnología y operaciones.
- El informe elimina referencias no reproducibles de una ejecución local anterior y conserva como evidencia versionada `12 passed`.

## Controles adicionales incorporados en v1.1.0

Se endurecieron secretos, TOTP, llaves JWT, claims, revalidación de sesiones, cadena de auditoría, cookies/CSRF, cabeceras HTTP, rutas de demo, manejo de contraseñas, auditoría de denegaciones y verificación histórica de firmas. El detalle está en `docs/revision-seguridad.md`.

El reporte académico corregido se entrega como artefacto DOCX separado. El código de ejecución continúa siendo **v1.1.0**; esta revisión del repositorio es documental y no introduce cambios de comportamiento en runtime.
