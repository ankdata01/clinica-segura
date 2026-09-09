# Pruebas locales

## Objetivo

Validar que la demo conserva sus propiedades principales antes de una presentación o después de un cambio en el código.

> [!WARNING]
> Las pruebas son destructivas para `db/clinica.db` y regeneran los archivos de `llaves/`. No utilizar datos reales en este proyecto.

## Entorno de presentación actual — Windows

Repositorio local:

```text
D:\sc_project
```

Entorno Python 3.12:

```text
D:\envs_shared\py312-torch-cu128
```

En PowerShell:

```powershell
Set-Location D:\sc_project

$PY = if (Test-Path "D:\envs_shared\py312-torch-cu128\Scripts\python.exe") {
    "D:\envs_shared\py312-torch-cu128\Scripts\python.exe"
}
elseif (Test-Path "D:\envs_shared\py312-torch-cu128\python.exe") {
    "D:\envs_shared\py312-torch-cu128\python.exe"
}
else {
    throw "No se encontró Python dentro de D:\envs_shared\py312-torch-cu128"
}

& $PY --version
& $PY -c "import sys; print(sys.executable)"
```

## Instalar dependencias de desarrollo

Primero puede revisarse el impacto:

```powershell
& $PY -m pip install --dry-run -r requirements-dev.txt
```

Instalación:

```powershell
& $PY -m pip install -r requirements-dev.txt --upgrade-strategy only-if-needed
& $PY -m pip check
```

## Configurar la sesión de demo

```powershell
$env:DEMO_MODE = "true"
$env:SECRET_KEY = & $PY -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Inicializar datos

```powershell
& $PY -m db.semilla
```

La semilla debe generar:

- `db/clinica.db`
- llaves RSA del servidor;
- llaves privadas cifradas del personal;
- QR TOTP;
- cuatro pacientes;
- seis notas clínicas firmadas;
- seis entradas iniciales de auditoría.

## Ejecutar la suite

```powershell
& $PY -m pytest -q
```

## Cobertura funcional de la suite

| Prueba | Control observado |
|---|---|
| Semilla e integridad | Firma de notas + cadena inicial |
| MFA | Contraseña + TOTP + JWT |
| Matriz de autorización | RBAC crítico |
| Logout | Validación CSRF |
| Rate limiter | 5 fallos / 5 min -> 15 min de bloqueo |
| Auditoría concurrente | Encadenamiento consistente con múltiples escritores |
| Manipulación | Detección de `hash_anterior` modificado |
| Restauración | Invalidación de sesión obsoleta |

## Levantar servidor después de las pruebas

```powershell
& $PY -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abrir:

```text
http://127.0.0.1:8000
```

Para la exposición no se recomienda usar `--host 0.0.0.0` mientras `DEMO_MODE=true`, porque `/demo/codigos` está diseñado para revelar los TOTP de la demo.

## CI en GitHub

`.github/workflows/tests.yml` ejecuta la suite con Python 3.12 en cada `push` y `pull_request`. El flujo instala `requirements-dev.txt` y ejecuta:

```bash
python -m pytest -q
```
