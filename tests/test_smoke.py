"""Pruebas de integración/destructivas para la demo local.

Ejecutar desde la raíz del proyecto:
    python -m pytest -q

Cada prueba que toca datos vuelve a ejecutar db.semilla, por lo que NO debe
usarse contra una base con información que se quiera conservar.
"""
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pyotp
from fastapi.testclient import TestClient

from app.config import DB_PATH
from app.datos.conexion import obtener_conexion
from app.datos.repo_auditoria import RepoAuditoria
from app.fabrica import Fabrica
from app.main import app
from app.seguridad import rate_limiter as rl
from db.semilla import main as reseed


def _row(sql: str, args=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        fila = con.execute(sql, args).fetchone()
        return dict(fila) if fila else None
    finally:
        con.close()


def _login(email: str) -> TestClient:
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/login").status_code == 200
    csrf = client.cookies["csrf_token"]
    r = client.post(
        "/login",
        data={"email": email, "contrasena": "Demo2026!", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert (r.status_code, r.headers.get("location")) == (303, "/login/mfa")

    assert client.get("/login/mfa").status_code == 200
    csrf = client.cookies["csrf_token"]
    secret = _row("SELECT mfa_secret FROM personal WHERE email = ?", (email,))["mfa_secret"]
    codigo = pyotp.TOTP(secret).now()
    r = client.post(
        "/login/mfa",
        data={"codigo": codigo, "csrf_token": csrf},
        follow_redirects=False,
    )
    assert (r.status_code, r.headers.get("location")) == (303, "/panel")
    assert client.cookies.get("token")
    return client


def test_semilla_e_integridad_inicial():
    reseed()
    con = obtener_conexion()
    try:
        resultado = Fabrica(con).ejecutar_verificacion()
        assert resultado["todo_ok"] is True
        assert resultado["cadena"]["total"] == 6
        assert resultado["firmas_invalidas"] == []
    finally:
        con.close()


def test_matriz_de_autorizacion_clave():
    reseed()

    enfermera = _login("ana.torres@clinica.mx")
    assert enfermera.get("/pacientes", follow_redirects=False).status_code == 200
    for ruta in ("/auditoria", "/sesiones", "/auditoria/exportar.csv"):
        r = enfermera.get(ruta, follow_redirects=False)
        assert r.status_code == 303
        assert r.headers["location"].startswith("/panel?error=acceso_denegado")

    admin = _login("admin@clinica.mx")
    r = admin.get("/pacientes", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/panel?error=acceso_denegado")
    assert admin.get("/auditoria", follow_redirects=False).status_code == 200


def test_logout_requiere_csrf():
    reseed()
    client = _login("laura.mendez@clinica.mx")
    assert client.cookies.get("token")

    r = client.post("/logout", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/panel?error=csrf"
    assert client.cookies.get("token")

    assert client.get("/panel").status_code == 200
    csrf = client.cookies["csrf_token"]
    r = client.post("/logout", data={"csrf_token": csrf}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"
    assert not client.cookies.get("token")


def test_rate_limit_bloquea_quince_minutos():
    rl._intentos.clear()
    rl._bloqueado_hasta.clear()
    for _ in range(rl.MAX_INTENTOS):
        rl.registrar_fallo("prueba")
    assert rl.esta_bloqueado("prueba")
    assert 895 <= rl.segundos_restantes("prueba") <= rl.BLOQUEO_SEG


def test_escrituras_auditoria_concurrentes_mantienen_cadena():
    reseed()

    def escribir(i: int):
        con = obtener_conexion()
        try:
            RepoAuditoria(con).insertar_encadenado(
                personal_id=None,
                entidad_afectada="test",
                entidad_id=str(i),
                accion="CONCURRENCIA",
                detalle=f"writer={i}",
                ip_origen="127.0.0.1",
            )
        finally:
            con.close()

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(escribir, range(20)))

    con = obtener_conexion()
    try:
        cadena = Fabrica(con).ejecutar_verificacion()["cadena"]
        assert cadena["integra"] is True
        assert cadena["total"] == 26
    finally:
        con.close()


def test_verificador_detecta_hash_anterior_manipulado():
    reseed()
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("DROP TRIGGER audit_log_no_update")
        entrada_id = con.execute(
            "SELECT id FROM audit_log ORDER BY rowid LIMIT 1"
        ).fetchone()[0]
        con.execute(
            "UPDATE audit_log SET hash_anterior = ? WHERE id = ?",
            ("f" * 64, entrada_id),
        )
        con.commit()
    finally:
        con.close()

    con = obtener_conexion()
    try:
        cadena = Fabrica(con).ejecutar_verificacion()["cadena"]
        assert cadena["integra"] is False
        assert cadena["primera_fila_rota"] == entrada_id
    finally:
        con.close()


def test_restaurar_invalida_sesion_anterior():
    reseed()
    client = _login("laura.mendez@clinica.mx")
    assert client.get("/demo").status_code == 200
    csrf = client.cookies["csrf_token"]

    r = client.post(
        "/demo/restaurar",
        data={"csrf_token": csrf},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/login?restaurado=ok"
    assert not client.cookies.get("token")
