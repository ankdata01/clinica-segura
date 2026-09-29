# Portada

**SISTEMA SEGURO: HOSPITAL v1.1.0**  
**Diseño e implementación de controles de ciberseguridad para un expediente clínico electrónico**

Proyecto académico de ciberseguridad  
Unidad de aprendizaje: **Seguridad Cibernética**  
Institución: **Universidad Autónoma del Estado de México — Facultad de Ingeniería**  
Fecha de revisión documental: **28 de septiembre de 2026**

**Versión funcional evaluada:** 1.1.0  
**Tecnologías principales:** Python 3.12, FastAPI, Jinja2, SQLite, Argon2id, TOTP, JWT RS256, RSA-PSS, SHA-256 y AES-256-GCM.

> **Nota de alcance.** Sistema Seguro: Hospital es un prototipo académico. Demuestra controles técnicos y un proceso de ingeniería de seguridad, pero no constituye por sí mismo una plataforma clínica certificada ni acredita cumplimiento legal o normativo para expedientes reales.

# Resumen

Sistema Seguro: Hospital v1.1.0 es un prototipo de expediente clínico electrónico diseñado para demostrar de forma verificable autenticidad, integridad, control de acceso, no repudio y trazabilidad. Utiliza autenticación multifactor con Argon2id y TOTP, sesiones JWT RS256, autorización basada en roles, firma RSA-PSS de notas clínicas, hashes SHA-256 y una bitácora encadenada protegida contra modificaciones y eliminaciones por la propia aplicación.

La revisión de seguridad de v1.1.0 eliminó secretos embebidos, cifró secretos TOTP en reposo con AES-256-GCM, cifró la llave privada del servidor, endureció JWT, revalidó cuentas en cada petición protegida, incorporó IP a la cadena de auditoría, fortaleció cookies/cabeceras HTTP, restringió funciones de demostración y conservó la verificabilidad de firmas históricas de médicos desactivados.

La revisión documental de 2026-09-28 estructura el análisis con **STRIDE, MITRE ATT&CK, CIA+, ITU-T X.800 y Defense in Depth**, conforme a fuentes oficiales. Corrige además la clasificación X.800 de auditoría/detección/recuperación como mecanismos o capacidades y no como familias adicionales de servicios de seguridad.

# Introducción

Los sistemas clínicos requieren proteger identidad, autorización, integridad, autoría, confidencialidad, disponibilidad y auditoría. Un control aislado no cubre todos estos objetivos: una contraseña fuerte no evita la manipulación directa de una base de datos, una firma digital no controla quién puede leer un expediente y una bitácora local no equivale a un registro remoto inmutable.

La pregunta de ingeniería es: **¿cómo demostrar que una nota clínica fue creada por un médico autorizado, que su contenido no fue alterado sin detección y que los eventos relevantes dejan evidencia auditable?**

La respuesta se implementa mediante autenticación multifactor, autorización por roles, firmas RSA-PSS, hashes SHA-256, auditoría encadenada y pruebas automatizadas. El análisis se apoya en STRIDE, MITRE ATT&CK, CIA+, X.800 y Defense in Depth, complementados con RFC 6238, RFC 7519, RFC 8017, NIST SP 800-63B-4 y OWASP ASVS.

# Descripción del sistema

## Propósito y alcance funcional

Sistema Seguro: Hospital gestiona usuarios internos, pacientes, historial clínico, creación de notas firmadas, auditoría y un panel controlado para demostrar ataques de integridad. Se ejecuta localmente y no depende de servicios externos para la demostración.

Activos principales: expedientes y notas; credenciales y hashes; secretos TOTP; JWT; llaves RSA; hashes y firmas; eventos de auditoría; `SECRET_KEY`; base SQLite y archivos criptográficos.

## Roles y permisos

| Acción | Administrador | Doctor | Enfermero | Administrativo |
|---|:---:|:---:|:---:|:---:|
| Consultar expedientes | — | Sí | Sí | Sí |
| Crear y firmar nota clínica | — | Sí | — | — |
| Consultar auditoría | Sí | Sí | — | Sí |
| Verificar integridad | Sí | Sí | — | Sí |
| Gestionar usuarios | Sí | — | — | — |
| Ejecutar panel de ataque de demo | Sí | Sí | — | — |

La autorización se aplica en servidor. Una cuenta desactivada pierde autorización en la siguiente petición protegida porque el sistema vuelve a consultar su estado. La verificación histórica conserva la llave pública de médicos inactivos.

## Flujos principales

### Inicio de sesión

1. Correo y contraseña.
2. Verificación Argon2id.
3. Preautenticación breve.
4. Código TOTP de seis dígitos.
5. Descifrado del secreto TOTP sólo en memoria.
6. Emisión de JWT RS256 con emisor, audiencia, tiempos y `jti`.
7. En cada petición se verifica JWT y estado/rol vigentes.

### Creación de una nota clínica

1. Doctor autenticado accede al expediente.
2. Se valida CSRF y RBAC.
3. Se canonicaliza la nota.
4. Se calcula SHA-256.
5. La contraseña descifra temporalmente la llave privada del médico.
6. Se firma mediante RSA-PSS con SHA-256.
7. Se persisten nota, hash y firma.
8. La operación se registra en auditoría.

### Auditoría e integridad

El hash de cada evento cubre hash anterior, identificador, usuario, entidad, acción, detalle, IP y fecha/hora con separador canónico. Triggers de SQLite rechazan `UPDATE` y `DELETE` sobre `audit_log`. El verificador recalcula cadena, hashes de notas y firmas de forma independiente.

## Límites del prototipo

No cifra integralmente los campos clínicos de SQLite, no ofrece alta disponibilidad, rate limiting distribuido, HSM/KMS, SIEM ni backup inmutable. Son limitaciones explícitas.

# Arquitectura

## Vista lógica

| Área | Ubicación | Responsabilidad |
|---|---|---|
| Presentación | `app/presentacion/` | Rutas HTTP, formularios, cookies, CSRF, Jinja2 |
| Autenticación | `app/autenticacion/` | Argon2id, TOTP, preauth, JWT y contraseña |
| Dominio clínico | `app/clinico/` | Modelos y operaciones clínicas |
| Seguridad | `app/seguridad/` | Firmas, llaves, cifrado, hash chain, verificación, rate limiting, headers |
| Datos | `app/datos/` | SQLite y repositorios parametrizados |
| Ensamblado | `app/fabrica.py` | Construcción de repositorios, servicios y decoradores |

La separación es modular dentro de un mismo proceso FastAPI y no debe confundirse con aislamiento físico.

## Patrones de diseño

**Repository:** encapsula SQL.  
**Factory:** centraliza ensamblado.  
**Decorator:** agrega auditoría a operaciones clínicas.  
**Strategy:** desacopla el algoritmo de firma; RSA-PSS es la estrategia activa.

## Fronteras de confianza

1. Navegador → FastAPI: entrada no confiable.
2. Aplicación → SQLite: persistencia y transacciones.
3. Aplicación → sistema de archivos: llaves y QR.
4. Entorno → aplicación: secretos de runtime.
5. Host → red: en producción requiere TLS/reverse proxy.

# Modelo STRIDE

STRIDE se aplica conforme al enfoque de modelado de amenazas de Microsoft: se identifican activos, componentes, flujos y fronteras, y se revisan seis categorías. El objetivo es descubrir escenarios de abuso y relacionarlos con controles verificables, no declarar riesgo cero.

| Categoría | Propiedad asociada | Amenaza | Controles | Riesgo residual |
|---|---|---|---|---|
| Spoofing | Autenticación | contraseña/cuenta válida robada | Argon2id, TOTP, rate limiting, JWT, revalidación | phishing TOTP y robo de sesión |
| Tampering | Integridad | modificación directa de nota/bitácora | SHA-256, RSA-PSS, hash chain con IP, triggers, verificador | control total del host |
| Repudiation | No repudio/accountability | negar autoría/acción | RSA-PSS + auditoría encadenada | sin TSA/HSM/tercero confiable |
| Information Disclosure | Confidencialidad | robo de TOTP, PEM, JWT o BD | AES-GCM, PEM cifrado, RBAC, cookies y no-store | BD clínica no cifrada integralmente |
| Denial of Service | Disponibilidad | fuerza bruta/bloqueo SQLite | rate limiting, transacciones breves | no distribuido/HA |
| Elevation of Privilege | Autorización | uso indebido de rol/sesión | RBAC, denegaciones auditadas, revalidación | políticas locales a la app |

Correspondencia usada: Spoofing→autenticación, Tampering→integridad, Repudiation→no repudio/accountability, Information Disclosure→confidencialidad, Denial of Service→disponibilidad y Elevation of Privilege→autorización.

# MITRE ATT&CK

ATT&CK se emplea como base de conocimiento de comportamientos adversarios. El mapeo describe escenarios plausibles y controles del prototipo; no representa certificación, prueba de ocurrencia ni checklist de cumplimiento.

| Técnica | Aplicación al prototipo | Mitigación/cobertura |
|---|---|---|
| T1078 — Valid Accounts | abuso de credenciales legítimas | MFA, RBAC, revalidación y auditoría |
| T1110 — Brute Force | guessing/spraying/intentos repetidos | Argon2id + rate limiting |
| T1539 — Steal Web Session Cookie | robo/reutilización de cookie JWT | HttpOnly, Secure configurable, SameSite=Strict, expiración y revalidación |
| T1552.004 — Unsecured Credentials: Private Keys | búsqueda/exfiltración de PEM | exclusión Git, cifrado, archivos no estáticos |
| T1565.001 — Stored Data Manipulation | manipulación de expedientes/evidencia | SHA-256, RSA-PSS, hash chain y verificador |
| T1070 — Indicator Removal | borrar/modificar evidencia | triggers + hash chain; producción requiere SIEM remoto |
| T1190 — Exploit Public-Facing Application | explotar entrada web si se expone a red | SQL parametrizado, autoescape, CSRF, CSP |
| T1005 — Data from Local System | extraer BD/llaves | separación/cifrado de secretos; residual alto con host comprometido |

# CIA+

NIST sitúa confidencialidad, integridad y disponibilidad en el núcleo de la seguridad y reconoce que otras propiedades pueden ser relevantes. En este documento, **CIA+ es una extensión de ingeniería del proyecto, no un estándar NIST independiente**. El signo `+` representa autenticidad, accountability/trazabilidad y no repudio.

| Propiedad | Controles del proyecto | Evaluación |
|---|---|---|
| Confidencialidad | RBAC; TOTP/PEM cifrados; cookies seguras; TLS previsto | Parcial: SQLite clínico sin cifrado aplicativo integral |
| Integridad | SHA-256, RSA-PSS, canonicalización, hash chain y verificador | Implementada en alcance local |
| Disponibilidad | rate limiting, transacciones acotadas, restauración de demo | Parcial: sin HA, DR ni rate limiting distribuido |
| Autenticidad | Argon2id+TOTP, JWT RS256, firma RSA-PSS | Implementada en identidad y autoría del prototipo |
| Accountability/trazabilidad | usuario, acción, entidad, IP, tiempo y cadena hash | Implementada localmente |
| No repudio | firma individual + llave pública histórica + auditoría | Parcial/demostrativo: sin TSA/HSM/tercero confiable |

La fiabilidad se trata como consideración operativa ligada a disponibilidad y resiliencia; el prototipo no declara una garantía independiente.

# ITU-T X.800

X.800 se usa como taxonomía conceptual y distingue **cinco familias básicas de servicios de seguridad**:

| Servicio X.800 | Implementación | Estado |
|---|---|---|
| Authentication | Argon2id + TOTP + sesión JWT; firmas para origen de datos | Implementado en el alcance del prototipo |
| Access control | RBAC + revalidación de cuenta/rol | Implementado |
| Data confidentiality | cookies seguras, TOTP/PEM cifrados, TLS previsto | Parcial |
| Data integrity | SHA-256, RSA-PSS, hash chain | Implementado en alcance local |
| Non-repudiation | firma del médico + auditoría | Parcial/demostrativo |

X.800 también contempla mecanismos específicos —como cifrado, firma digital, control de acceso, integridad, intercambio de autenticación y notarización— y mecanismos pervasivos, entre ellos detección de eventos, *security audit trail* y *security recovery*. Por ello, la bitácora, el verificador y la restauración se documentan como **mecanismos/capacidades**, no como familias adicionales de servicio X.800.

# Defense in Depth

NIST define Defense in Depth como una estrategia que integra personas, tecnología y capacidades operativas para establecer barreras en múltiples capas.

| Capa/dimensión | Controles clave | Brecha |
|---|---|---|
| Gobierno/personas | roles y mínimo privilegio documentados | capacitación, segregación formal y gobierno pendientes |
| Repositorio/SDLC | `.gitignore`, placeholders, CI, pruebas | controles empresariales de supply chain limitados |
| Host/archivos | PEM fuera de estáticos, privados cifrados | sin EDR/KMS/HSM |
| Transporte/navegador | HTTPS/HSTS previsto, Secure/HttpOnly/SameSite, CSP | TLS gestionado/WAF fuera de la demo |
| Identidad/sesión | Argon2id, TOTP, rate limiting, JWT, revalidación | sin IdP central ni factor resistente a phishing |
| Aplicación | RBAC, CSRF, validación, autoescape, SQL parametrizado | política centralizada limitada |
| Datos/criptografía | SHA-256, RSA-PSS, AES-GCM | sin cifrado integral de BD/volumen |
| Auditoría/validación | hash chain, IP, triggers, verificador, pytest | sin SIEM remoto/inmutable |
| Operaciones/resiliencia | restauración reproducible de demo | sin IR, HA/DR, backups inmutables ni monitoreo empresarial |

# Implementación de controles

## Contraseñas y MFA

Argon2id protege hashes de contraseña. Los secretos TOTP se almacenan como `enc:v1:<blob>` usando AES-256-GCM; la clave se deriva de `SECRET_KEY` mediante HKDF-SHA256. Los códigos se verifican con RFC 6238.

## Sesión JWT

RS256 separa firma y verificación. Los tokens exigen `sub`, `iss`, `aud`, `iat`, `nbf`, `exp` y `jti`. La cuenta y el rol se revalidan contra la base en cada petición protegida.

## Firma de notas

La canonicalización fija orden de paciente, médico, diagnóstico, tratamiento y fecha. SHA-256 produce el digest y RSA-PSS firma ese digest. La llave privada del médico permanece cifrada en disco.

## Auditoría encadenada

`RepoAuditoria.insertar_encadenado()` ejecuta `BEGIN IMMEDIATE`, obtiene el hash previo, calcula el nuevo hash incluyendo `ip_origen` e inserta dentro de la misma transacción. Triggers bloquean UPDATE/DELETE.

## CSRF, cookies y cabeceras

Los POST utilizan double-submit CSRF. Cookies de sesión/preauth son HttpOnly, SameSite=Strict y Secure configurable. Middleware agrega CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, no-store y HSTS cuando corresponde.

## Configuración y repositorio

`.env.example` sólo contiene placeholders. `.gitignore` excluye `.env`, bases, PEM, llaves, QR y caches. CI genera secretos efímeros.

# Pruebas y validación

La suite `tests/test_smoke.py` contiene doce pruebas que cubren: semilla/integridad inicial, RBAC, CSRF, rate limiting, concurrencia de auditoría, manipulación de hash, restauración, cifrado de secretos, manipulación de IP, revocación al desactivar usuario, headers/visor demo y firmas históricas.

Se ejecutó:

```bash
python -m compileall -q app db tests
python -m pytest -q
```

Evidencia versionada:

```text
Compilación: sin errores
Suite: 12 passed
```

La evidencia se conserva en `evidencias/resultado-validacion.txt`. Las pruebas destructivas recrean previamente la semilla y están destinadas al entorno de demostración.

# Resultados

| Área | Estado v1.1.0 | Evidencia |
|---|---|---|
| Secretos versionables | Mejorado | `.env.example` + `.gitignore` |
| MFA | Implementado/endurecido | TOTP + secreto cifrado |
| JWT | Endurecido | RS256, claims, issuer/audience y revalidación |
| RBAC | Implementado | rutas y pruebas |
| Firma de notas | Implementado | RSA-PSS + verificador |
| Auditoría | Implementado localmente | SHA-256, IP, concurrencia, triggers |
| CSRF | Implementado | formularios POST y logout |
| Cabeceras HTTP | Implementado | middleware + pruebas |
| CIA+ | Parcial según propiedad | confidencialidad/disponibilidad mantienen brechas productivas |
| X.800 | Mapeado a cinco familias básicas | mecanismos y servicios separados |
| CI / pruebas | Implementado | workflow sin secretos estáticos, 12 pruebas |
| Cifrado integral BD clínica | Pendiente productivo | recomendación |
| Log remoto/WORM | Pendiente productivo | recomendación |
| KMS/HSM | Pendiente productivo | recomendación |

El riesgo residual principal es el compromiso total del host. También permanecen riesgos de disponibilidad/escalabilidad por SQLite/rate limiter en memoria y de confidencialidad de datos clínicos en reposo.

# Conclusiones

Sistema Seguro: Hospital v1.1.0 demuestra que la seguridad requiere controles complementarios y evidencia verificable, no un único algoritmo. STRIDE estructura amenazas por categoría; MITRE ATT&CK relaciona escenarios con comportamientos adversarios; CIA+ hace visibles objetivos y brechas de confidencialidad/disponibilidad; X.800 separa servicios de mecanismos; y Defense in Depth evidencia que una solución productiva debe cubrir personas, tecnología y operaciones.

El prototipo cumple su propósito académico, pero para producción serían imprescindibles alta disponibilidad, TLS administrado, cifrado de almacenamiento/BD, KMS/HSM, logs remotos inmutables, backups, monitoreo continuo, gestión centralizada de identidad, respuesta a incidentes, capacitación y evaluación normativa formal.

# Referencias

1. International Telecommunication Union. (1991). *Recommendation X.800: Security architecture for Open Systems Interconnection for CCITT applications*. https://www.itu.int/rec/T-REC-X.800-199103-I/en
2. National Institute of Standards and Technology. (2025). *Digital Identity Guidelines: Authentication and Authenticator Management (NIST SP 800-63B-4)*. https://doi.org/10.6028/NIST.SP.800-63b-4
3. National Institute of Standards and Technology. (2015). *Secure Hash Standard (FIPS PUB 180-4)*. https://doi.org/10.6028/NIST.FIPS.180-4
4. M'Raihi, D., Machani, S., Pei, M., & Rydell, J. (2011). *TOTP: Time-Based One-Time Password Algorithm (RFC 6238)*. https://doi.org/10.17487/RFC6238
5. Jones, M., Bradley, J., & Sakimura, N. (2015). *JSON Web Token (JWT) (RFC 7519)*. https://doi.org/10.17487/RFC7519
6. Moriarty, K., Kaliski, B., Jonsson, J., & Rusch, A. (2016). *PKCS #1: RSA Cryptography Specifications Version 2.2 (RFC 8017)*. https://doi.org/10.17487/RFC8017
7. MITRE. *MITRE ATT&CK Enterprise*. https://attack.mitre.org/
8. OWASP Foundation. (2025). *OWASP Application Security Verification Standard 5.0.0*. https://owasp.org/www-project-application-security-verification-standard/
9. Microsoft Learn. *Design secure applications on Azure: threat modeling and STRIDE*. https://learn.microsoft.com/en-us/azure/security/develop/secure-design
10. NIST CSRC. *Security*. https://csrc.nist.gov/glossary/term/security
11. NIST CSRC. *Defense in Depth*. https://csrc.nist.gov/glossary/term/defense_in_depth

# Artefactos relacionados

- `docs/modelo-amenazas.md`
- `docs/marcos-seguridad.md`
- `docs/seguridad.md`
- `docs/matriz-cumplimiento.md`
- `evidencias/resultado-validacion.txt`
