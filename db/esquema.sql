PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- Personal de la clínica (médicos, enfermeros, administrativos)
-- Cada miembro tiene su propio par RSA para firma digital (no repudio).
-- La llave privada NO se guarda aquí; solo la pública.
-- ----------------------------------------------------------------------------
CREATE TABLE personal (
    id              TEXT PRIMARY KEY,          -- uuid4
    nombre          TEXT NOT NULL,
    rol             TEXT NOT NULL,             -- 'doctor' | 'enfermero' | 'administrativo'
    especialidad    TEXT,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,             -- Argon2id
    mfa_secret      TEXT NOT NULL,             -- base32 para TOTP
    llave_publica   TEXT NOT NULL,             -- PEM
    activo          INTEGER NOT NULL DEFAULT 1
);

-- ----------------------------------------------------------------------------
-- Pacientes — sin credenciales: no inician sesión en este sistema.
-- ----------------------------------------------------------------------------
CREATE TABLE pacientes (
    id                  TEXT PRIMARY KEY,
    nombre              TEXT NOT NULL,
    fecha_nacimiento    TEXT NOT NULL,
    contacto            TEXT
);

-- ----------------------------------------------------------------------------
-- Citas — la tabla existe en el modelo ER entregado, pero la interfaz
-- de agenda no está en el alcance del proyecto.
-- ----------------------------------------------------------------------------
CREATE TABLE citas (
    id              TEXT PRIMARY KEY,
    paciente_id     TEXT NOT NULL REFERENCES pacientes(id),
    personal_id     TEXT NOT NULL REFERENCES personal(id),
    fecha           TEXT NOT NULL,
    estado          TEXT NOT NULL,             -- 'agendada' | 'atendida' | 'cancelada'
    es_emergencia   INTEGER NOT NULL DEFAULT 0 -- 1 = la fecha es la hora de llegada
);

-- ----------------------------------------------------------------------------
-- Historial clínico — cada nota lleva firma RSA-PSS del médico.
-- hash_registro = SHA-256 del contenido canónico.
-- firma_digital  = RSA-PSS sobre el hash, codificado en base64.
-- Ambos permiten detectar alteraciones y probar no repudio.
-- ----------------------------------------------------------------------------
CREATE TABLE historial_clinico (
    id              TEXT PRIMARY KEY,
    paciente_id     TEXT NOT NULL REFERENCES pacientes(id),
    personal_id     TEXT NOT NULL REFERENCES personal(id),
    diagnostico     TEXT NOT NULL,
    tratamiento     TEXT NOT NULL,
    fecha           TEXT NOT NULL,             -- ISO 8601 UTC
    hash_registro   TEXT NOT NULL,             -- SHA-256 del contenido canónico
    firma_digital   TEXT NOT NULL              -- RSA-PSS sobre el hash, en base64
);

-- ----------------------------------------------------------------------------
-- Bitácora de auditoría — inmutable por diseño.
-- hash_anterior + hash_actual forman la cadena; cualquier modificación
-- rompe la secuencia y es detectable por el verificador.
-- ----------------------------------------------------------------------------
CREATE TABLE audit_log (
    id                  TEXT PRIMARY KEY,
    personal_id         TEXT REFERENCES personal(id),  -- NULL en acciones del sistema
    entidad_afectada    TEXT NOT NULL,   -- 'historial_clinico' | 'paciente' | 'sesion'
    entidad_id          TEXT,
    accion              TEXT NOT NULL,   -- 'LOGIN_OK' | 'CREAR_NOTA' | 'CONSULTAR_HISTORIAL' | ...
    detalle             TEXT,
    ip_origen           TEXT,
    fecha_hora          TEXT NOT NULL,   -- ISO 8601 UTC
    hash_anterior       TEXT NOT NULL,
    hash_actual         TEXT NOT NULL
);

CREATE INDEX idx_historial_paciente ON historial_clinico(paciente_id);
CREATE INDEX idx_audit_fecha        ON audit_log(fecha_hora);

-- ----------------------------------------------------------------------------
-- Inmutabilidad de la bitácora.
-- SQLite no soporta permisos de solo inserción; se logra con triggers que
-- abortan cualquier intento de UPDATE o DELETE.
-- ----------------------------------------------------------------------------
CREATE TRIGGER audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'La bitacora de auditoria es inmutable: UPDATE no permitido');
END;

CREATE TRIGGER audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, 'La bitacora de auditoria es inmutable: DELETE no permitido');
END;
