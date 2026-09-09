"""
Rutas clínicas: lista de pacientes, historial, nueva nota firmada.

Control de acceso por rol:
  - doctor    → puede consultar y crear notas
  - enfermero → puede consultar, NO puede crear notas (ACCESO_DENEGADO auditado)
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.autenticacion.servicio_auth import ServicioAuth
from app.clinico.modelos import NotaClinica
from app.clinico.servicio_clinico import PacienteNoEncontrado
from app.config import DEMO_MODE, LLAVES_DIR
from app.datos.repo_auditoria import RepoAuditoria
from app.datos.repo_personal import RepoPersonal
from app.fabrica import Fabrica
from app.presentacion.dependencias import (
    dep_conexion, usuario_actual,
    generar_csrf, validar_csrf, set_csrf_cookie,
)
from app.seguridad.firma import canonicalizar_nota, hash_de_contenido, firmar_nota
from app.seguridad.llaves import cargar_privada


def _ip(request: Request) -> str:
    return request.client.host if request.client else "desconocido"


def _iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def crear_router(plantillas: Jinja2Templates) -> APIRouter:
    router = APIRouter(tags=["clínico"])

    # ------------------------------------------------------------------ #
    # GET /pacientes                                                        #
    # ------------------------------------------------------------------ #
    @router.get("/pacientes", response_class=HTMLResponse)
    async def listar_pacientes(
        request: Request,
        con=Depends(dep_conexion),
        usuario: dict = Depends(usuario_actual),
    ):
        fab = Fabrica(con)
        pacientes = fab.servicio_clinico().listar_pacientes()
        csrf = generar_csrf()
        resp = plantillas.TemplateResponse(
            request, "pacientes.html",
            {
                "usuario":   usuario,
                "pacientes": pacientes,
                "csrf_token": csrf,
                "demo_mode": DEMO_MODE,
            },
        )
        set_csrf_cookie(resp, csrf)
        return resp

    # ------------------------------------------------------------------ #
    # GET /pacientes/{paciente_id} — historial (audita CONSULTAR_HISTORIAL) #
    # ------------------------------------------------------------------ #
    @router.get("/pacientes/{paciente_id}", response_class=HTMLResponse)
    async def ver_historial(
        request: Request,
        paciente_id: str,
        con=Depends(dep_conexion),
        usuario: dict = Depends(usuario_actual),
    ):
        fab = Fabrica(con)
        try:
            paciente, notas = fab.servicio_clinico().obtener_historial(
                paciente_id,
                personal_id=usuario["sub"],
                ip=_ip(request),
            )
        except PacienteNoEncontrado:
            return RedirectResponse(url="/pacientes", status_code=303)

        csrf = generar_csrf()
        puede_crear = usuario.get("rol") == "doctor"
        resp = plantillas.TemplateResponse(
            request, "historial.html",
            {
                "usuario":         usuario,
                "paciente":        paciente,
                "notas":           notas,
                "puede_crear_nota": puede_crear,
                "csrf_token":      csrf,
                "demo_mode":       DEMO_MODE,
            },
        )
        set_csrf_cookie(resp, csrf)
        return resp

    # ------------------------------------------------------------------ #
    # GET /pacientes/{paciente_id}/nota — formulario de nueva nota          #
    # ------------------------------------------------------------------ #
    @router.get("/pacientes/{paciente_id}/nota", response_class=HTMLResponse)
    async def formulario_nota(
        request: Request,
        paciente_id: str,
        con=Depends(dep_conexion),
        usuario: dict = Depends(usuario_actual),
    ):
        # Control de acceso: solo doctores pueden crear notas
        if usuario.get("rol") != "doctor":
            fab = Fabrica(con)
            fab.servicio_auth().registrar_acceso_denegado(
                usuario["sub"], f"/pacientes/{paciente_id}/nota", _ip(request)
            )
            return RedirectResponse(
                url=f"/pacientes/{paciente_id}?error=acceso_denegado", status_code=303
            )

        fab = Fabrica(con)
        fila_pac = fab.repo_personal()  # solo para obtener paciente
        # Obtener datos del paciente para mostrar en el formulario
        from app.datos.repo_pacientes import RepoPacientes
        pac_dict = RepoPacientes(con).obtener_por_id(paciente_id)
        if pac_dict is None:
            return RedirectResponse(url="/pacientes", status_code=303)

        from app.clinico.modelos import Paciente
        paciente = Paciente(**{k: pac_dict[k] for k in ("id", "nombre", "fecha_nacimiento", "contacto")})

        csrf = generar_csrf()
        resp = plantillas.TemplateResponse(
            request, "nota_nueva.html",
            {
                "usuario":   usuario,
                "paciente":  paciente,
                "csrf_token": csrf,
                "demo_mode": DEMO_MODE,
            },
        )
        set_csrf_cookie(resp, csrf)
        return resp

    # ------------------------------------------------------------------ #
    # POST /pacientes/{paciente_id}/nota — crear nota firmada               #
    # ------------------------------------------------------------------ #
    @router.post("/pacientes/{paciente_id}/nota", response_class=HTMLResponse)
    async def crear_nota(
        request: Request,
        paciente_id: str,
        con=Depends(dep_conexion),
        usuario: dict = Depends(usuario_actual),
    ):
        if usuario.get("rol") != "doctor":
            fab = Fabrica(con)
            fab.servicio_auth().registrar_acceso_denegado(
                usuario["sub"], f"/pacientes/{paciente_id}/nota", _ip(request)
            )
            return RedirectResponse(url=f"/pacientes/{paciente_id}", status_code=303)

        form = await request.form()
        diagnostico      = str(form.get("diagnostico", "")).strip()
        tratamiento      = str(form.get("tratamiento", "")).strip()
        contrasena_firma = str(form.get("contrasena_firma", ""))
        csrf_form        = str(form.get("csrf_token", ""))

        from app.datos.repo_pacientes import RepoPacientes
        from app.clinico.modelos import Paciente

        pac_dict = RepoPacientes(con).obtener_por_id(paciente_id)
        if pac_dict is None:
            return RedirectResponse(url="/pacientes", status_code=303)
        paciente = Paciente(**{k: pac_dict[k] for k in ("id", "nombre", "fecha_nacimiento", "contacto")})

        def _error(msg: str):
            csrf = generar_csrf()
            resp = plantillas.TemplateResponse(
                request, "nota_nueva.html",
                {
                    "usuario":   usuario,
                    "paciente":  paciente,
                    "error":     msg,
                    "csrf_token": csrf,
                    "demo_mode": DEMO_MODE,
                },
            )
            set_csrf_cookie(resp, csrf)
            return resp

        if not validar_csrf(request, csrf_form):
            return _error("Token de seguridad inválido. Recarga la página.")

        if not diagnostico or not tratamiento:
            return _error("Completa el diagnóstico y el tratamiento.")

        if not contrasena_firma:
            return _error("La contraseña es necesaria para firmar la nota.")

        # Descifrar llave privada con la contraseña — si falla, contraseña incorrecta
        ruta_llave = LLAVES_DIR / f"personal_{usuario['sub']}.pem"
        try:
            llave_privada = cargar_privada(ruta_llave, contrasena_firma)
        except Exception:
            return _error("Contraseña incorrecta. La nota no fue firmada.")

        # Firmar ANTES de llamar al servicio (la capa clínica no sabe de firmas)
        fecha = _iso_utc()
        contenido = canonicalizar_nota(
            paciente_id, usuario["sub"], diagnostico, tratamiento, fecha
        )
        h_bytes       = hash_de_contenido(contenido)
        hash_registro = h_bytes.hex()
        firma_b64     = firmar_nota(llave_privada, h_bytes)
        del llave_privada  # descartada inmediatamente tras firmar

        nota = NotaClinica(
            id=str(uuid.uuid4()),
            paciente_id=paciente_id,
            personal_id=usuario["sub"],
            diagnostico=diagnostico,
            tratamiento=tratamiento,
            fecha=fecha,
            hash_registro=hash_registro,
            firma_digital=firma_b64,
        )

        fab = Fabrica(con)
        fab.servicio_clinico().crear_nota(nota, personal_id=usuario["sub"], ip=_ip(request))

        return RedirectResponse(url=f"/pacientes/{paciente_id}", status_code=303)

    # ------------------------------------------------------------------ #
    # GET /pacientes/{paciente_id}/pdf — historial para imprimir/PDF       #
    # ------------------------------------------------------------------ #
    @router.get("/pacientes/{paciente_id}/pdf", response_class=HTMLResponse)
    async def historial_pdf(
        request: Request,
        paciente_id: str,
        con=Depends(dep_conexion),
        usuario: dict = Depends(usuario_actual),
    ):
        from app.datos.repo_pacientes import RepoPacientes
        from app.clinico.modelos import Paciente

        pac_dict = RepoPacientes(con).obtener_por_id(paciente_id)
        if pac_dict is None:
            return RedirectResponse(url="/pacientes", status_code=303)

        fab = Fabrica(con)
        try:
            paciente, notas = fab.servicio_clinico().obtener_historial(
                paciente_id, usuario["sub"], _ip(request)
            )
        except Exception:
            paciente = Paciente(**{k: pac_dict[k] for k in ("id", "nombre", "fecha_nacimiento", "contacto")})
            notas = []

        return plantillas.TemplateResponse(
            request, "historial_pdf.html",
            {
                "usuario":  usuario,
                "paciente": paciente,
                "notas":    notas,
                "demo_mode": DEMO_MODE,
                "csrf_token": "",
            },
        )

    return router
