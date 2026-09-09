"""
Panel de demostración — simula ataques para mostrar los mecanismos de defensa.

Rutas:
  GET  /demo                 → panel con estado actual
  POST /demo/atacar          → corrompe una nota en historial_clinico (UPDATE directo)
  POST /demo/borrar_bitacora → intenta DELETE en audit_log (trigger lo rechaza)
  POST /demo/restaurar       → re-ejecuta db/semilla.py para volver al estado limpio
  GET  /demo/codigos         → muestra códigos TOTP actuales de cada usuario de prueba

Solo disponible cuando DEMO_MODE=True (config.py).
"""
import subprocess
import sys

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import (
    DB_PATH, DEMO_MODE, COOKIE_TOKEN_NOMBRE, COOKIE_PREFACTOR_NOMBRE,
)
from app.datos.repo_auditoria import RepoAuditoria
from app.datos.repo_personal import RepoPersonal
from app.fabrica import Fabrica
from app.presentacion.dependencias import (
    dep_conexion, usuario_actual,
    generar_csrf, validar_csrf, set_csrf_cookie, COOKIE_CSRF,
)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "desconocido"


def _auditar_ataque(repo: RepoAuditoria, accion: str, detalle: str, ip: str) -> None:
    repo.insertar_encadenado(
        personal_id=None,
        entidad_afectada="demo",
        entidad_id=None,
        accion=accion,
        detalle=detalle,
        ip_origen=ip,
    )


def crear_router(plantillas: Jinja2Templates) -> APIRouter:
    router = APIRouter(prefix="/demo", tags=["demo"])

    # ------------------------------------------------------------------ #
    # GET /demo — panel de demostración                                    #
    # ------------------------------------------------------------------ #
    @router.get("", response_class=HTMLResponse)
    async def panel_demo(
        request: Request,
        con=Depends(dep_conexion),
        usuario: dict = Depends(usuario_actual),
    ):
        fab    = Fabrica(con)
        estado = fab.ejecutar_verificacion()

        from app.autenticacion import mfa
        personal = fab.repo_personal().listar_todos()
        codigos  = [
            {
                "nombre": p["nombre"],
                "email":  p["email"],
                "codigo": mfa.codigo_actual(p["mfa_secret"]),
            }
            for p in personal
        ]

        csrf = generar_csrf()
        resp = plantillas.TemplateResponse(
            request, "demo.html",
            {
                "usuario":   usuario,
                "estado":    estado,
                "codigos":   codigos,
                "csrf_token": csrf,
                "demo_mode": DEMO_MODE,
            },
        )
        set_csrf_cookie(resp, csrf)
        return resp

    # ------------------------------------------------------------------ #
    # POST /demo/atacar — corrompe la primera nota en historial_clinico    #
    # ------------------------------------------------------------------ #
    @router.post("/atacar", response_class=HTMLResponse)
    async def atacar(
        request: Request,
        con=Depends(dep_conexion),
        usuario: dict = Depends(usuario_actual),
    ):
        form      = await request.form()
        csrf_form = str(form.get("csrf_token", ""))
        if not validar_csrf(request, csrf_form):
            return RedirectResponse(url="/demo", status_code=303)

        import sqlite3

        # ATAQUE SIMULADO INTENCIONAL — UPDATE directo sin pasar por el servicio.
        # Corrompe hash y firma; el verificador lo detectará.
        cx = sqlite3.connect(str(DB_PATH))
        try:
            fila = cx.execute(
                "SELECT id FROM historial_clinico ORDER BY fecha LIMIT 1"
            ).fetchone()
            if fila:
                nota_id = fila[0]
                cx.execute(
                    "UPDATE historial_clinico "
                    "SET diagnostico = 'DATO MANIPULADO POR ATACANTE' "
                    "WHERE id = ?",
                    (nota_id,),
                )
                cx.commit()
                detalle = f"nota_id={nota_id}"
            else:
                detalle = "no_habia_notas"
        finally:
            cx.close()

        _auditar_ataque(RepoAuditoria(con), "ATAQUE_SIMULADO", detalle, _ip(request))
        return RedirectResponse(url="/demo?ataque=ok", status_code=303)

    # ------------------------------------------------------------------ #
    # POST /demo/borrar_bitacora — intenta DELETE en audit_log             #
    # ------------------------------------------------------------------ #
    @router.post("/borrar_bitacora", response_class=HTMLResponse)
    async def borrar_bitacora(
        request: Request,
        con=Depends(dep_conexion),
        usuario: dict = Depends(usuario_actual),
    ):
        form      = await request.form()
        csrf_form = str(form.get("csrf_token", ""))
        if not validar_csrf(request, csrf_form):
            return RedirectResponse(url="/demo", status_code=303)

        import sqlite3

        mensaje_trigger = None
        cx = sqlite3.connect(str(DB_PATH))
        try:
            cx.execute("DELETE FROM audit_log")
            cx.commit()
            mensaje_trigger = "DELETE ejecutado (inesperado)"
        except (sqlite3.IntegrityError, sqlite3.OperationalError) as e:
            mensaje_trigger = str(e)
        finally:
            cx.close()

        _auditar_ataque(
            RepoAuditoria(con),
            "ATAQUE_SIMULADO",
            f"intento_borrar_bitacora: {mensaje_trigger}",
            _ip(request),
        )
        return RedirectResponse(
            url=f"/demo?trigger={mensaje_trigger[:80]}", status_code=303
        )

    # ------------------------------------------------------------------ #
    # POST /demo/restaurar — re-ejecuta semilla para resetear estado       #
    # ------------------------------------------------------------------ #
    @router.post("/restaurar", response_class=HTMLResponse)
    async def restaurar(
        request: Request,
        usuario: dict = Depends(usuario_actual),
    ):
        form      = await request.form()
        csrf_form = str(form.get("csrf_token", ""))
        if not validar_csrf(request, csrf_form):
            return RedirectResponse(url="/demo", status_code=303)

        resultado = subprocess.run(
            [sys.executable, "-m", "db.semilla"],
            capture_output=True,
            text=True,
            cwd=str(DB_PATH.parent.parent),
        )
        ok = resultado.returncode == 0

        # La semilla regenera UUIDs, llaves y secretos TOTP. El JWT actual
        # queda vinculado a un usuario que ya no existe; forzamos un login limpio.
        resp = RedirectResponse(url="/login?restaurado=ok", status_code=303)
        resp.delete_cookie(COOKIE_TOKEN_NOMBRE)
        resp.delete_cookie(COOKIE_PREFACTOR_NOMBRE)
        resp.delete_cookie(COOKIE_CSRF)
        return resp

    # ------------------------------------------------------------------ #
    # GET /demo/codigos — códigos TOTP actuales (sin autenticación)       #
    # Accesible antes del login para cuando falla un teléfono en demo.    #
    # ------------------------------------------------------------------ #
    @router.get("/codigos", response_class=HTMLResponse)
    async def ver_codigos(request: Request, con=Depends(dep_conexion)):
        from app.autenticacion import mfa
        fab      = Fabrica(con)
        personal = fab.repo_personal().listar_todos()
        codigos  = [
            {
                "nombre": p["nombre"],
                "email":  p["email"],
                "codigo": mfa.codigo_actual(p["mfa_secret"]),
            }
            for p in personal
        ]
        resp = plantillas.TemplateResponse(
            request, "demo_codigos.html",
            {
                "usuario":   None,
                "codigos":   codigos,
                "csrf_token": "",
                "demo_mode": DEMO_MODE,
            },
        )
        return resp

    return router
