# Modelo de amenazas y objetivos de seguridad — Sistema Seguro: Hospital v1.1.0

> **Revisión documental:** 2026-09-28.  
> Este documento aplica **STRIDE**, **MITRE ATT&CK**, **CIA+**, **ITU-T X.800** y **Defense in Depth** como marcos complementarios. Los mapeos describen el prototipo y sus riesgos residuales; **no constituyen certificación, conformidad regulatoria ni evidencia de que una técnica ATT&CK haya ocurrido**.

## 0. Fuentes oficiales y criterio de uso

| Marco | Fuente primaria | Uso en el proyecto |
|---|---|---|
| STRIDE | Microsoft Learn, *Design secure applications on Azure* | Clasificar amenazas sobre activos, flujos y fronteras de confianza |
| MITRE ATT&CK | MITRE ATT&CK Enterprise | Relacionar escenarios del prototipo con comportamientos adversarios documentados |
| CIA / CIA+ | NIST CSRC Glossary | Evaluar objetivos de confidencialidad, integridad y disponibilidad y propiedades adicionales |
| X.800 | ITU-T Recommendation X.800 | Separar familias de servicios de seguridad y mecanismos |
| Defense in Depth | NIST CSRC Glossary | Revisar barreras complementarias en personas, tecnología y operaciones |

**CIA+ no es el nombre de un estándar NIST independiente.** En este proyecto se usa como extensión de ingeniería de la tríada CIA. El signo `+` agrupa **autenticidad, accountability/trazabilidad y no repudio**. NIST define seguridad alrededor de confidencialidad, integridad y disponibilidad y reconoce que propiedades adicionales, como autenticidad, accountability y no repudio, pueden ser relevantes.

## 1. Activos y fronteras de confianza

**Activos críticos:** expedientes y notas clínicas, credenciales, secretos TOTP, JWT, llaves RSA privadas y públicas, hashes y firmas, bitácora, `SECRET_KEY`, base SQLite y archivos criptográficos.

**Fronteras principales:**

1. navegador → FastAPI;
2. presentación → servicios;
3. servicios → repositorios;
4. aplicación → SQLite;
5. aplicación → material criptográfico;
6. entorno → aplicación;
7. host local → red.

Los datos del navegador se consideran no confiables. La separación por capas es modular dentro de un mismo proceso FastAPI y no equivale a aislamiento físico.

## 2. STRIDE

Microsoft usa STRIDE para razonar sobre seis clases de amenaza. En este proyecto se mantiene además la correspondencia con la propiedad de seguridad que cada categoría pone en riesgo.

| Categoría STRIDE | Propiedad asociada | Escenario en Hospital | Controles implementados | Riesgo residual |
|---|---|---|---|---|
| **S — Spoofing** | Autenticación | Suplantar identidad o abusar de una cuenta válida | Argon2id, TOTP, rate limiting, JWT RS256 y revalidación de cuenta | TOTP puede ser capturado por phishing en tiempo real; una sesión robada puede reutilizarse mientras siga vigente |
| **T — Tampering** | Integridad | Alterar notas, hashes o auditoría | SHA-256, RSA-PSS, cadena de hashes con IP, triggers y verificador | Con control total del host se podrían sustituir código, BD o evidencia local |
| **R — Repudiation** | No repudio / accountability | Negar una acción o la autoría de una nota | Llave privada individual, firma RSA-PSS y auditoría encadenada | Sin HSM, TSA ni tercero confiable, el no repudio es demostrativo y no una garantía jurídica absoluta |
| **I — Information Disclosure** | Confidencialidad | Exponer TOTP, PEM, JWT o expediente | TOTP/PEM cifrados, RBAC, cookies HttpOnly/SameSite y archivos fuera de estáticos | El contenido clínico de SQLite no tiene cifrado aplicativo integral |
| **D — Denial of Service** | Disponibilidad | Fuerza bruta, agotamiento o bloqueo de SQLite | Rate limiting y transacciones acotadas | Rate limiter en memoria, proceso único y SQLite limitan disponibilidad y escalabilidad |
| **E — Elevation of Privilege** | Autorización | Ejecutar funciones de un rol superior o conservar privilegios obsoletos | RBAC, auditoría de denegaciones y revalidación de rol/estado | Las políticas siguen acopladas a la aplicación y requieren gobierno centralizado en producción |

STRIDE **no asigna por sí mismo una puntuación de riesgo**. Aquí se usa para descubrir escenarios de abuso y enlazarlos con controles verificables y riesgos residuales.

## 3. MITRE ATT&CK

ATT&CK se usa como base de conocimiento de comportamientos adversarios, no como checklist de cumplimiento. El mapeo es una **analogía defensiva**: describe qué técnicas son relevantes para el escenario y qué controles locales reducen o detectan parte del riesgo.

| Técnica ATT&CK | Escenario aplicado | Cobertura del prototipo | Limitación |
|---|---|---|---|
| **T1078 — Valid Accounts** | Abuso de una cuenta legítima | MFA, RBAC, revalidación y auditoría | Una cuenta y segundo factor comprometidos siguen siendo utilizables |
| **T1110 — Brute Force** | Password guessing, spraying o intentos repetidos | Argon2id y rate limiting por IP/cuenta/MFA | Cobertura local al proceso; no distribuida |
| **T1539 — Steal Web Session Cookie** | Robo o reutilización de la cookie JWT | HttpOnly, `Secure` configurable, SameSite=Strict, expiración y revalidación | Un endpoint comprometido o robo de sesión sigue siendo riesgo residual |
| **T1552.004 — Unsecured Credentials: Private Keys** | Descubrir o exfiltrar PEM privados | PEM cifrados, fuera de estáticos y excluidos de Git | Las llaves continúan residiendo en el host |
| **T1565.001 — Stored Data Manipulation** | Alterar datos clínicos o evidencia en SQLite | Hash, firma, cadena de auditoría y verificador | Detectar no equivale a impedir a un administrador del host |
| **T1070 — Indicator Removal** | Eliminar o modificar artefactos de evidencia | Triggers anti-`UPDATE`/`DELETE` y hash chain | La sub-técnica exacta depende del artefacto; un administrador del host puede superar controles locales |
| **T1190 — Exploit Public-Facing Application** | Explotar entradas web si la app se expone a red | SQL parametrizado, autoescape, CSRF, CSP y docs deshabilitables | La técnica cobra plena relevancia sólo si el servicio deja de estar limitado a loopback/red controlada |
| **T1005 — Data from Local System** | Extraer BD, PEM u otros archivos locales | Separación de archivos y cifrado de secretos | Riesgo alto frente a compromiso total del endpoint |

En una implantación real, los eventos deberían enviarse a un SIEM remoto y correlacionarse con fallos de autenticación, cambios de privilegio, sesiones anómalas y verificaciones de integridad.

## 4. CIA+

CIA resume tres objetivos clásicos: **Confidencialidad, Integridad y Disponibilidad**. Para este proyecto se añade una capa explícita de propiedades necesarias para el caso clínico.

| Propiedad | Controles del proyecto | Evaluación |
|---|---|---|
| **Confidencialidad** | RBAC; TOTP y PEM cifrados; cookies seguras; TLS previsto en despliegue | **Parcial:** la base clínica SQLite no está cifrada integralmente a nivel de aplicación |
| **Integridad** | SHA-256, RSA-PSS, canonicalización, cadena de auditoría, triggers y verificador | Implementada para notas y evidencia dentro del alcance local |
| **Disponibilidad** | Rate limiting, transacciones acotadas y restauración reproducible de demo | **Parcial:** sin HA, rate limiting distribuido, DR ni base escalable |
| **Autenticidad** | Argon2id + TOTP, JWT RS256 y firma RSA-PSS por médico | Implementada en los flujos de identidad y autoría del prototipo |
| **Accountability / trazabilidad** | Eventos con usuario, acción, entidad, IP, fecha/hora y cadena hash | Implementada localmente; no resiste control total del host |
| **No repudio** | Firma individual RSA-PSS + llave pública histórica + auditoría | **Parcial/demostrativo:** sin TSA, HSM ni tercero confiable |

La **fiabilidad** puede considerarse una propiedad adicional en ciertos marcos. En este prototipo se trata operacionalmente junto con disponibilidad y resiliencia; no se declara una garantía independiente.

## 5. ITU-T X.800

X.800 distingue **cinco familias básicas de servicios de seguridad**. Esta distinción corrige una versión anterior de la documentación que presentaba auditoría/detección y recuperación como si fueran familias de servicio adicionales.

| Familia de servicio X.800 | Implementación en Hospital | Evaluación |
|---|---|---|
| **Autenticación** | Peer-entity: Argon2id + TOTP + sesión JWT; data-origin: firmas y validaciones criptográficas | Implementada en el alcance del prototipo |
| **Control de acceso** | RBAC, rol vigente y cuenta activa revalidada | Implementado |
| **Confidencialidad de datos** | TOTP/PEM cifrados, cookies seguras y TLS previsto en despliegue | Parcial por contenido clínico SQLite sin cifrado aplicativo integral |
| **Integridad de datos** | SHA-256, RSA-PSS, cadena de auditoría y verificación | Implementada para notas y evidencia local |
| **No repudio** | Firma individual del médico + auditoría | Parcial; principalmente evidencia de origen, sin HSM/TSA/tercero confiable |

### Mecanismos X.800 relevantes

X.800 también describe **mecanismos específicos** como cifrado, firma digital, control de acceso, mecanismos de integridad, intercambio de autenticación y notarización, además de **mecanismos pervasivos** como detección de eventos, *security audit trail* y *security recovery*.

En el proyecto:

- **cifrado:** AES-256-GCM para TOTP y PEM cifrados; TLS queda en la capa de despliegue;
- **firma digital:** RSA-PSS para notas;
- **integridad:** SHA-256, canonicalización y hash chain;
- **intercambio de autenticación:** contraseña + TOTP y emisión de sesión firmada;
- **control de acceso:** RBAC y revalidación de cuenta/rol;
- **detección / audit trail:** bitácora encadenada, eventos de sesión, IP y verificador;
- **security recovery:** restauración reproducible de la demo.

**Auditoría, detección y recuperación se documentan como mecanismos/capacidades, no como familias de servicio X.800.** La disponibilidad se evalúa en CIA+ y en la arquitectura operativa, no como una sexta familia básica de X.800.

## 6. Defense in Depth

NIST define Defense in Depth como una estrategia que integra **personas, tecnología y capacidades operativas** para establecer barreras en múltiples capas. Por tanto, el análisis no se limita a controles de software.

| Dimensión / capa | Controles actuales | Brecha principal |
|---|---|---|
| **Gobierno / personas** | Roles y mínimo privilegio documentados | Capacitación, segregación formal de funciones, gobierno y responsabilidades operativas quedan pendientes |
| **Repositorio / SDLC** | `.gitignore`, `.env.example` sin secretos, CI y pruebas | Faltan controles empresariales de supply chain y revisión obligatoria |
| **Host / archivos** | PEM fuera de estáticos, privados cifrados y permisos restrictivos | Sin EDR ni KMS/HSM |
| **Transporte / navegador** | Secure/HttpOnly/SameSite, CSP, HSTS configurable, anti-framing y `nosniff` | TLS administrado/reverse proxy/WAF no forman parte de la demo |
| **Identidad / sesión** | Argon2id, TOTP, preauth, rate limiting, JWT y revalidación | Sin IdP central ni autenticación resistente a phishing |
| **Aplicación** | RBAC, CSRF, autoescape de Jinja2 y SQL parametrizado | Políticas centralizadas y pruebas de seguridad continuas limitadas |
| **Datos / criptografía** | AES-GCM, SHA-256 y RSA-PSS | Sin cifrado integral de BD/volumen ni gestión externa de llaves |
| **Auditoría / validación** | Hash chain, triggers, IP incluida, verificador, pytest y compilación | Sin SIEM remoto/inmutable |
| **Operaciones / resiliencia** | Restauración reproducible de demo | Sin IR formal, backups inmutables probados, HA, DR, EDR ni monitoreo empresarial |

La defensa en profundidad del prototipo es **principalmente tecnológica** y tiene soporte operativo limitado mediante CI, pruebas y restauración. No debe confundirse con un programa de seguridad organizacional completo.

## 7. Trazabilidad cruzada de marcos

| Objetivo | STRIDE | ATT&CK relacionado | CIA+ / X.800 | Controles observables |
|---|---|---|---|---|
| Identidad auténtica | Spoofing | T1078, T1110 | Autenticidad / Autenticación | Argon2id, TOTP, JWT, rate limiting |
| Integridad clínica | Tampering | T1565.001 | Integridad / Integridad de datos | SHA-256, RSA-PSS, verificador |
| Evidencia y autoría | Repudiation | T1070 | Accountability + No repudio / No repudio | Firma individual, auditoría encadenada |
| Confidencialidad | Information Disclosure | T1005, T1552.004, T1539 | Confidencialidad / Confidencialidad de datos | RBAC, cifrado de secretos, cookies |
| Disponibilidad | Denial of Service | T1110 (abuso de autenticación) | Disponibilidad | Rate limiting, transacciones acotadas |
| Privilegios correctos | Elevation of Privilege | T1078 | Accountability / Control de acceso | RBAC, cuenta activa, denegaciones auditadas |

## 8. Riesgos residuales y transición a producción

Las brechas principales permanecen fuera del alcance académico:

- compromiso total del host;
- cifrado integral de almacenamiento/BD;
- KMS/HSM y rotación gestionada de llaves;
- TLS administrado, reverse proxy/WAF y segmentación;
- SIEM/log remoto inmutable;
- backups probados, alta disponibilidad y recuperación ante desastres;
- EDR, monitoreo y respuesta a incidentes;
- gestión centralizada de identidad;
- capacitación, gobierno, segregación de funciones y evaluación normativa específica.

## 9. Referencias oficiales

- Microsoft Learn — STRIDE / secure design: https://learn.microsoft.com/en-us/azure/security/develop/secure-design
- MITRE ATT&CK Enterprise: https://attack.mitre.org/
- MITRE T1078: https://attack.mitre.org/techniques/T1078/
- MITRE T1110: https://attack.mitre.org/techniques/T1110/
- MITRE T1539: https://attack.mitre.org/techniques/T1539/
- MITRE T1552.004: https://attack.mitre.org/techniques/T1552/004/
- MITRE T1565.001: https://attack.mitre.org/techniques/T1565/001/
- MITRE T1070: https://attack.mitre.org/techniques/T1070/
- MITRE T1190: https://attack.mitre.org/techniques/T1190/
- MITRE T1005: https://attack.mitre.org/techniques/T1005/
- NIST CSRC — Security: https://csrc.nist.gov/glossary/term/security
- NIST CSRC — Authenticity: https://csrc.nist.gov/glossary/term/authenticity
- NIST CSRC — Accountability: https://csrc.nist.gov/glossary/term/accountability
- NIST CSRC — Non-repudiation: https://csrc.nist.gov/glossary/term/non_repudiation
- NIST CSRC — Defense in Depth: https://csrc.nist.gov/glossary/term/defense_in_depth
- ITU-T Recommendation X.800: https://www.itu.int/rec/T-REC-X.800-199103-I/en
