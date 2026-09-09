# Guion técnico de demostración

## Objetivo

Demostrar, en aproximadamente 10–12 minutos, tres principios del proyecto en este orden:

1. **Autenticidad**
2. **No repudio**
3. **Trazabilidad**

La aplicación debe ejecutarse únicamente en un entorno local/controlado con `DEMO_MODE=true`.

## Preparación previa

Desde la raíz del proyecto:

```powershell
$env:DEMO_MODE = "true"
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
python -m db.semilla
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abrir:

```text
http://127.0.0.1:8000
```

Credencial recomendada para la exposición:

```text
Usuario:     laura.mendez@clinica.mx
Contraseña: Demo2026!
```

El TOTP actual puede obtenerse en otra pestaña mediante:

```text
http://127.0.0.1:8000/demo/codigos
```

> `/demo/codigos` existe exclusivamente para la exposición.

---

## Escena 1 — Autenticidad mediante MFA

### Acción

1. Abrir `/login`.
2. Ingresar correo y contraseña.
3. Mostrar que el sistema **no concede una sesión completa todavía**.
4. Introducir el TOTP de seis dígitos.
5. Acceder al panel.

### Explicación

La identidad se valida mediante:

```text
algo que sabes  -> contraseña protegida con Argon2id
algo que tienes -> TOTP
sesión          -> JWT firmado con RS256
```

### Mensaje para la presentación

> La contraseña por sí sola no es suficiente. El sistema exige un segundo factor antes de emitir el JWT de sesión.

---

## Escena 2 — Crear una nota clínica firmada

### Acción

1. Ir a **Pacientes**.
2. Abrir el historial de un paciente.
3. Seleccionar **Nueva nota**.
4. Capturar diagnóstico y tratamiento.
5. Introducir la contraseña para descifrar la llave privada del médico.
6. Guardar la nota.

### Qué mostrar

En el historial, señalar:

- hash SHA-256 de la nota;
- firma RSA-PSS;
- médico asociado;
- fecha.

### Explicación

```text
contenido de nota
       ↓
canonicalización
       ↓
SHA-256
       ↓
RSA-PSS con llave privada del médico
       ↓
firma digital
```

### Mensaje para la presentación

> La firma está ligada tanto al médico como al contenido. Si cambia un campo de la nota, el hash recalculado deja de coincidir con el hash firmado.

---

## Escena 3 — Simular alteración directa

### Acción

1. Ir a **Demo**.
2. Ejecutar la acción de modificación directa de una nota.
3. Explicar que la operación evita deliberadamente las capas normales de la aplicación.

### Mensaje

> La demostración representa a un atacante o administrador con acceso directo al almacenamiento y permite comprobar si los controles criptográficos detectan la alteración.

---

## Escena 4 — Verificar integridad

### Acción

1. Ir a **Auditoría**.
2. Seleccionar **Verificar integridad**.
3. Mostrar el resultado de `contenido_alterado` o firma inválida correspondiente a la nota manipulada.

### Explicación

El verificador:

1. recalcula el contenido canónico;
2. recalcula SHA-256;
3. compara con `hash_registro`;
4. verifica RSA-PSS con la llave pública del médico;
5. valida la cadena de auditoría.

### Mensaje

> La aplicación no necesita confiar únicamente en el contenido almacenado: puede volver a calcular y verificar criptográficamente la evidencia.

---

## Escena 5 — Intentar eliminar la bitácora

### Acción

1. Volver a **Demo**.
2. Ejecutar **Intentar DELETE** sobre la bitácora.
3. Mostrar el rechazo producido por el trigger de SQLite.

### Mensaje

> Incluso el intento de borrar evidencia es rechazado por la capa de persistencia. En una solución de producción se requerirían controles adicionales como WORM o SIEM, pero aquí el trigger permite demostrar el concepto de inmutabilidad lógica.

---

## Escena 6 — Mostrar trazabilidad de sesión

### Acción

Abrir **Sesiones** y mostrar acciones relevantes, por ejemplo:

```text
LOGIN_OK
LOGIN_FALLIDO
MFA_FALLIDO
LOGOUT
ACCESO_DENEGADO
```

### Mensaje de cierre

> Clínica Segura combina identidad, firma digital y auditoría para demostrar que la seguridad no depende de un único control: autenticidad, no repudio y trazabilidad se complementan.

---

## Restaurar la demo

Para devolver el proyecto a su estado inicial puede utilizarse el botón **Restaurar demo**.

La restauración regenera:

- base SQLite;
- UUID de usuarios;
- pares de llaves;
- secretos TOTP;
- códigos QR.

Por ello, la sesión anterior se invalida y el sistema redirige de nuevo al login.

## Plan B durante la presentación

Si una acción de interfaz falla:

1. conservar la presentación Canva como hilo principal;
2. mostrar `README.md` y `docs/seguridad.md` en GitHub;
3. mostrar el resultado previo de `python -m pytest -q`;
4. reinicializar con `python -m db.semilla` si la base fue alterada.

El repositorio debe ser evidencia de respaldo, no un punto único de fallo de la exposición.
