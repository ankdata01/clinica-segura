# Arquitectura de Clínica Segura

## 1. Propósito

La arquitectura busca separar presentación, autenticación, lógica clínica, controles de seguridad y acceso a datos para que cada responsabilidad pueda revisarse y probarse de manera independiente.

El sistema se ejecuta localmente con **FastAPI + Jinja2 + SQLite** y no necesita servicios externos para la demostración.

## 2. Vista general

```mermaid
flowchart LR
    B[Navegador] --> HTTP[FastAPI / Presentación]
    HTTP --> AUTH[Autenticación]
    HTTP --> CLIN[Clínico]
    HTTP --> SEC[Seguridad]
    AUTH --> DATA[Datos / Repositorios]
    CLIN --> DATA
    SEC --> DATA
    DATA --> DB[(SQLite)]
```

## 3. Capas y módulos

| Área | Directorio | Responsabilidad |
|---|---|---|
| Presentación | `app/presentacion/` | Rutas HTTP, formularios, cookies, redirecciones y renderizado Jinja2 |
| Autenticación | `app/autenticacion/` | Contraseñas Argon2id, TOTP, emisión y validación JWT |
| Clínica | `app/clinico/` | Modelos y operaciones del dominio clínico |
| Seguridad | `app/seguridad/` | RSA-PSS, SHA-256, auditoría, verificador, llaves y rate limiting |
| Datos | `app/datos/` | Conexión SQLite y repositorios con SQL parametrizado |
| Ensamblado | `app/fabrica.py` | Construcción principal de servicios y repositorios |
| Persistencia | `db/` | Esquema, triggers y datos de demostración |

## 4. Patrones de diseño

### Repository

Los repositorios encapsulan el acceso SQL:

- `RepoPersonal`
- `RepoPacientes`
- `RepoHistorial`
- `RepoAuditoria`

Su propósito es impedir que la lógica de dominio dependa directamente de consultas SQL dispersas.

### Factory

`Fabrica` centraliza la composición principal de repositorios y servicios por conexión.

> Nota de implementación: la versión de demo conserva algunos accesos directos desde rutas de presentación hacia repositorios o funciones de seguridad. Se considera una deuda técnica conocida y no se presenta como una frontera de capas estricta.

### Decorator

`AuditoriaDecorator` agrega trazabilidad a operaciones clínicas sin modificar la lógica clínica base.

### Strategy

El módulo de firma define una estrategia intercambiable. La demo utiliza **RSA-PSS con SHA-256**; el código incluye una alternativa ECDSA no activa.

## 5. Flujo de autenticación

```mermaid
sequenceDiagram
    participant U as Usuario
    participant R as Rutas Auth
    participant A as Servicio Auth
    participant DB as RepoPersonal

    U->>R: POST /login
    R->>A: validar credenciales
    A->>DB: obtener usuario por email
    A->>A: verificar Argon2id
    A-->>R: primer factor válido
    R-->>U: pre_auth HttpOnly / SameSite=Strict
    U->>R: POST /login/mfa
    R->>A: validar TOTP
    A->>A: emitir JWT RS256
    R-->>U: token de sesión
```

El JWT contiene `sub`, `nombre`, `rol`, `iat`, `exp` y `jti`, y expira a los **30 minutos**.

## 6. Flujo de creación de una nota

```mermaid
flowchart TD
    A[Doctor autenticado] --> B[Formulario nueva nota]
    B --> C[Validar RBAC y CSRF]
    C --> D[Descifrar llave privada del médico]
    D --> E[Canonicalizar campos]
    E --> F[SHA-256]
    F --> G[Firma RSA-PSS]
    G --> H[Guardar nota]
    H --> I[Registrar evento de auditoría]
```

La llave privada personal se almacena cifrada y la contraseña del médico se utiliza para descifrarla al firmar.

## 7. Flujo de auditoría

```mermaid
flowchart LR
    E1[Evento n-1] --> H1[hash_actual n-1]
    H1 --> P[hash_anterior n]
    P --> F[Campos del evento n]
    F --> SHA[SHA-256]
    SHA --> H2[hash_actual n]
```

La fórmula actual incluye:

```text
hash_anterior
+ id
+ personal_id
+ entidad_afectada
+ entidad_id
+ accion
+ detalle
+ fecha_hora
```

SQLite incluye triggers que rechazan `UPDATE` y `DELETE` sobre `audit_log`. La escritura encadenada usa una transacción `BEGIN IMMEDIATE` para serializar la obtención del hash previo y la inserción del siguiente eslabón.

## 8. Fronteras de confianza

```mermaid
flowchart TD
    U[Entrada no confiable\nformularios HTTP] --> V[Validación HTTP + CSRF + RBAC]
    V --> S[Servicios de aplicación]
    S --> Q[Repositorios parametrizados]
    Q --> DB[(SQLite local)]
    S --> K[Material criptográfico local]
```

Elementos que deben considerarse sensibles incluso en una demo:

- `SECRET_KEY`
- llaves privadas PEM
- secretos TOTP
- códigos QR de enrolamiento
- base `db/clinica.db`
- cookies/JWT activos

Estos elementos no deben formar parte del historial Git.
