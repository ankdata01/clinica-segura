# Marcos de seguridad y fuentes oficiales

**Sistema Seguro: Hospital v1.1.0**  
**Revisión documental:** 2026-09-28

Este archivo concentra el criterio de uso y las fuentes primarias de los marcos incorporados al proyecto. El análisis aplicado está en [`modelo-amenazas.md`](modelo-amenazas.md).

## Resumen

| Marco | Pregunta que responde | Aplicación en el proyecto |
|---|---|---|
| **STRIDE** | ¿Qué clases de amenaza pueden afectar activos y fronteras? | Seis categorías: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service y Elevation of Privilege |
| **MITRE ATT&CK** | ¿Qué comportamientos adversarios conocidos se parecen a nuestros escenarios? | Mapeo defensivo a técnicas Enterprise; no es checklist ni evidencia de ocurrencia |
| **CIA+** | ¿Qué propiedades de seguridad deben conservarse? | CIA + autenticidad + accountability/trazabilidad + no repudio |
| **ITU-T X.800** | ¿Qué servicios y mecanismos de seguridad estamos usando? | Cinco familias básicas de servicio y mecanismos específicos/pervasivos |
| **Defense in Depth** | ¿Existen barreras complementarias y no un único punto de defensa? | Capas de personas/gobierno, tecnología y operaciones |

## STRIDE — Microsoft

Microsoft documenta STRIDE como una forma de identificar amenazas durante el modelado. La correspondencia usada en este proyecto es:

- Spoofing → autenticación;
- Tampering → integridad;
- Repudiation → no repudio/accountability;
- Information Disclosure → confidencialidad;
- Denial of Service → disponibilidad;
- Elevation of Privilege → autorización.

Fuente oficial: https://learn.microsoft.com/en-us/azure/security/develop/secure-design

## MITRE ATT&CK — Enterprise

Técnicas mapeadas en esta revisión:

- T1078 — Valid Accounts
- T1110 — Brute Force
- T1539 — Steal Web Session Cookie
- T1552.004 — Unsecured Credentials: Private Keys
- T1565.001 — Stored Data Manipulation
- T1070 — Indicator Removal
- T1190 — Exploit Public-Facing Application
- T1005 — Data from Local System

Fuentes oficiales:

- https://attack.mitre.org/
- https://attack.mitre.org/techniques/T1078/
- https://attack.mitre.org/techniques/T1110/
- https://attack.mitre.org/techniques/T1539/
- https://attack.mitre.org/techniques/T1552/004/
- https://attack.mitre.org/techniques/T1565/001/
- https://attack.mitre.org/techniques/T1070/
- https://attack.mitre.org/techniques/T1190/
- https://attack.mitre.org/techniques/T1005/

## CIA+ — aclaración metodológica

NIST define la seguridad de la información alrededor de **confidencialidad, integridad y disponibilidad**, y reconoce que otras propiedades como autenticidad, accountability y no repudio pueden ser relevantes.

En este repositorio, **CIA+ es una extensión de ingeniería propia del análisis**, no el nombre de un estándar NIST independiente:

`CIA+ = Confidentiality + Integrity + Availability + Authenticity + Accountability/Traceability + Non-repudiation`

Fuentes NIST:

- Security: https://csrc.nist.gov/glossary/term/security
- Authenticity: https://csrc.nist.gov/glossary/term/authenticity
- Accountability: https://csrc.nist.gov/glossary/term/accountability
- Non-repudiation: https://csrc.nist.gov/glossary/term/non_repudiation

## ITU-T X.800 — servicios vs. mecanismos

La corrección más importante de esta revisión es conceptual: X.800 define cinco familias básicas de **servicios de seguridad**:

1. autenticación;
2. control de acceso;
3. confidencialidad de datos;
4. integridad de datos;
5. no repudio.

Además, X.800 describe mecanismos de seguridad específicos y pervasivos. **Detección de eventos, security audit trail y security recovery no se presentan aquí como familias de servicio adicionales**; se mapean como mecanismos/capacidades.

Fuente oficial: https://www.itu.int/rec/T-REC-X.800-199103-I/en

## Defense in Depth — NIST

NIST trata Defense in Depth como una estrategia que integra **personas, tecnología y capacidades operativas** mediante barreras en múltiples capas. Por ello, el análisis del proyecto incluye tanto controles implementados como brechas organizacionales y operativas.

Fuente oficial: https://csrc.nist.gov/glossary/term/defense_in_depth

## Alcance

Estos marcos ayudan a estructurar análisis y trazabilidad. No convierten al prototipo en un sistema clínico certificado ni sustituyen evaluación de riesgo formal, pentest, gestión de vulnerabilidades, continuidad de negocio, respuesta a incidentes o cumplimiento sanitario.
