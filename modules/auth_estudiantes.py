"""
Registro e inicio de sesión de participantes contra Supabase (tabla app_estudiante).
Campos: nombre, cédula, correo, institución, fecha de nacimiento y contraseña (hash bcrypt).
Requiere SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY en secrets o entorno.
"""

from __future__ import annotations

import re
import urllib.parse
from datetime import date, timedelta
from typing import Any, Callable, Optional

import bcrypt
import requests
import streamlit as st

from modules import uso_stats

_TABLE = "app_estudiante"
_TIMEOUT = 15
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_CEDULA_TOKEN_RE = re.compile(r"^[\w.-]+$", re.UNICODE)


def _supabase_ok() -> bool:
    u, k = uso_stats.supabase_url_y_clave()
    return bool(u and k)


def _base_url() -> str:
    u, _ = uso_stats.supabase_url_y_clave()
    return (u or "").rstrip("/")


def _headers() -> dict[str, str]:
    _, k = uso_stats.supabase_url_y_clave()
    return uso_stats.headers_supabase_rest(k or "")


def normalizar_email(email: str) -> str:
    return (email or "").strip().lower()


def normalizar_cedula(cedula: str) -> str:
    return re.sub(r"\s+", "", (cedula or "").strip().lower())


def validar_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(normalizar_email(email)))


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def _verificar_password(plain: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            password_hash.encode("ascii"),
        )
    except (ValueError, TypeError):
        return False


def buscar_por_email(email: str) -> Optional[dict[str, Any]]:
    em = normalizar_email(email)
    if not em or not _supabase_ok():
        return None
    q = urllib.parse.quote(em, safe="")
    url = (
        f"{_base_url()}/rest/v1/{_TABLE}?email=eq.{q}"
        "&select=id,email,password_hash,nombre,cedula,institucion,fecha_nacimiento,"
        "display_name,codigo_opcional"
    )
    try:
        r = requests.get(url, headers=_headers(), timeout=_TIMEOUT)
        if r.status_code != 200:
            return None
        rows = r.json()
        if not rows:
            return None
        return rows[0]
    except requests.RequestException:
        return None


def buscar_por_cedula_normalizada(ced_norm: str) -> Optional[dict[str, Any]]:
    if not ced_norm or not _supabase_ok():
        return None
    q = urllib.parse.quote(ced_norm, safe="")
    url = f"{_base_url()}/rest/v1/{_TABLE}?cedula=eq.{q}&select=id,email"
    try:
        r = requests.get(url, headers=_headers(), timeout=_TIMEOUT)
        if r.status_code != 200:
            return None
        rows = r.json()
        if not rows:
            return None
        return rows[0]
    except requests.RequestException:
        return None


def validar_fecha_nacimiento(d: date) -> tuple[bool, str]:
    if d >= date.today():
        return False, "La fecha de nacimiento debe ser anterior a hoy."
    edad_min = date.today() - timedelta(days=365 * 100)
    edad_max = date.today() - timedelta(days=365 * 14)
    if d < edad_min:
        return False, "Revisa la fecha de nacimiento (no puede ser tan antigua)."
    if d > edad_max:
        return False, "Debes tener al menos 14 años para registrarte."
    return True, ""


def registrar_estudiante(
    email: str,
    password: str,
    nombre: str,
    cedula: str,
    institucion: str,
    fecha_nacimiento: date,
) -> tuple[bool, str]:
    """
    Crea fila en app_estudiante. Devuelve (éxito, mensaje).
    """
    if not _supabase_ok():
        return False, "Supabase no está configurado (SUPABASE_URL y clave service_role)."

    em = normalizar_email(email)
    if not validar_email(em):
        return False, "Correo no válido."
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."

    nom = (nombre or "").strip()
    if len(nom) < 2:
        return False, "Indica tu nombre completo (al menos 2 caracteres)."
    if len(nom) > 200:
        return False, "El nombre es demasiado largo."

    inst = (institucion or "").strip()
    if len(inst) < 2:
        return False, "Indica la institución donde estudias."
    if len(inst) > 200:
        return False, "El nombre de la institución es demasiado largo."

    ced_norm = normalizar_cedula(cedula)
    if len(ced_norm) < 5 or len(ced_norm) > 32:
        return False, "La cédula o documento debe tener entre 5 y 32 caracteres (sin contar espacios)."
    if not _CEDULA_TOKEN_RE.match(ced_norm):
        return False, "La cédula solo puede incluir letras, números, punto o guion."

    ok_f, msg_f = validar_fecha_nacimiento(fecha_nacimiento)
    if not ok_f:
        return False, msg_f

    if buscar_por_email(em):
        return False, "Ya existe una cuenta con ese correo."
    if buscar_por_cedula_normalizada(ced_norm):
        return False, "Ya hay una cuenta registrada con esa cédula o documento."

    payload = {
        "email": em,
        "password_hash": _hash_password(password),
        "nombre": nom,
        "cedula": ced_norm,
        "institucion": inst,
        "fecha_nacimiento": fecha_nacimiento.isoformat(),
    }
    insert_url = f"{_base_url()}/rest/v1/{_TABLE}"
    try:
        r = requests.post(
            insert_url,
            headers={**_headers(), "Prefer": "return=minimal"},
            json=payload,
            timeout=_TIMEOUT,
        )
        if r.status_code in (200, 201):
            return True, "Cuenta creada. Ya puedes iniciar sesión."
        if r.status_code == 409 or "23505" in (r.text or ""):
            if "cedula" in (r.text or "").lower() or "email" in (r.text or "").lower():
                return False, "Ese correo o cédula ya está registrado."
            return False, "Ya existe una cuenta con esos datos."
        return False, f"No se pudo registrar ({r.status_code}). {r.text[:200]}"
    except requests.RequestException as e:
        return False, f"Error de red: {e}"


def autenticar(email: str, password: str) -> tuple[bool, str]:
    """
    Verifica credenciales. Si son correctas, guarda sesión en st.session_state.
    Devuelve (éxito, mensaje).
    """
    if not _supabase_ok():
        return False, "Supabase no está configurado."

    em = normalizar_email(email)
    row = buscar_por_email(em)
    if not row:
        return False, "Correo o contraseña incorrectos."

    ph = row.get("password_hash") or ""
    if not _verificar_password(password, ph):
        return False, "Correo o contraseña incorrectos."

    st.session_state.auth_estudiante_id = str(row["id"])
    st.session_state.auth_estudiante_email = row.get("email") or em
    st.session_state.auth_estudiante_nombre = (
        (row.get("nombre") or row.get("display_name") or "") or ""
    ).strip()
    st.session_state.auth_estudiante_cedula = (row.get("cedula") or "").strip() or None
    st.session_state.auth_estudiante_institucion = (row.get("institucion") or "").strip() or None
    fn = row.get("fecha_nacimiento")
    if isinstance(fn, str):
        st.session_state.auth_estudiante_fecha_nacimiento = fn[:10]
    elif hasattr(fn, "isoformat"):
        st.session_state.auth_estudiante_fecha_nacimiento = fn.isoformat()[:10]
    else:
        st.session_state.auth_estudiante_fecha_nacimiento = None

    leg = row.get("codigo_opcional")
    if leg:
        st.session_state.auth_estudiante_codigo = leg
    else:
        st.session_state.pop("auth_estudiante_codigo", None)

    return True, "Sesión iniciada."


def cerrar_sesion() -> None:
    for k in (
        "auth_estudiante_id",
        "auth_estudiante_email",
        "auth_estudiante_nombre",
        "auth_estudiante_codigo",
        "auth_estudiante_cedula",
        "auth_estudiante_institucion",
        "auth_estudiante_fecha_nacimiento",
        "_seguimos_uso_registrado_sesion",
    ):
        st.session_state.pop(k, None)
    st.session_state.pop("estudiante_nombre_seguimos", None)
    st.session_state.pop("estudiante_codigo_seguimos", None)


def sesion_activa() -> bool:
    return bool(st.session_state.get("auth_estudiante_id"))


def render_formulario_login(
    *,
    key_prefix: str,
    on_session_ok: Optional[Callable[[], None]] = None,
) -> None:
    with st.form(f"form_login_{key_prefix}"):
        e = st.text_input("Correo", key=f"{key_prefix}_login_email")
        p = st.text_input("Contraseña", type="password", key=f"{key_prefix}_login_pass")
        if st.form_submit_button("Entrar", type="primary"):
            ok, msg = autenticar(e, p)
            if ok:
                if on_session_ok:
                    on_session_ok()
                st.rerun()
            else:
                st.error(msg)


def render_formulario_registro(
    *,
    key_prefix: str,
    on_session_ok: Optional[Callable[[], None]] = None,
) -> None:
    with st.form(f"form_registro_{key_prefix}"):
        st.caption("Datos del participante (estudiante universitario).")
        nom = st.text_input("Nombre completo", key=f"{key_prefix}_reg_nombre", max_chars=200)
        ced = st.text_input("Cédula o documento de identidad", key=f"{key_prefix}_reg_cedula", max_chars=40)
        e2 = st.text_input("Correo electrónico", key=f"{key_prefix}_reg_email")
        inst = st.text_input("Institución donde estudias", key=f"{key_prefix}_reg_institucion", max_chars=200)
        hoy = date.today()
        fn = st.date_input(
            "Fecha de nacimiento",
            value=hoy - timedelta(days=365 * 18),
            min_value=hoy - timedelta(days=365 * 100),
            max_value=hoy - timedelta(days=365 * 14),
            key=f"{key_prefix}_reg_fn",
        )
        p2 = st.text_input("Contraseña (mín. 8 caracteres)", type="password", key=f"{key_prefix}_reg_pass")
        p2b = st.text_input("Repite la contraseña", type="password", key=f"{key_prefix}_reg_pass2")
        if st.form_submit_button("Registrarme", type="primary"):
            if p2 != p2b:
                st.error("Las contraseñas no coinciden.")
            else:
                ok, msg = registrar_estudiante(e2, p2, nom, ced, inst, fn)
                if ok:
                    ok_in, _ = autenticar(e2, p2)
                    if ok_in:
                        if on_session_ok:
                            on_session_ok()
                        st.rerun()
                    st.success(msg)
                    st.info("Cuenta creada. Usa **Iniciar sesión** con el mismo correo y contraseña.")
                else:
                    st.error(msg)


def render_portal_participante(
    *,
    tab_inicial: str = "registro",
    on_session_ok: Optional[Callable[[], None]] = None,
) -> None:
    """
    Portal dedicado: formulario de registro visible arriba; inicio de sesión debajo (sin pestañas).
    `tab_inicial` se usa solo para mostrar un aviso si llegaste desde «Ya tengo cuenta».
    """
    if not _supabase_ok():
        st.caption(
            "💡 **Registro en base de datos:** configura `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` "
            "en secrets y ejecuta `supabase_estudiantes.sql` en el SQL Editor."
        )
        return

    st.markdown("#### Registro de participante")
    st.caption(
        "Completa los datos: nombre completo, cédula, correo, institución, fecha de nacimiento y contraseña."
    )
    if tab_inicial == "login":
        st.info("Si ya tienes cuenta, baja a **Iniciar sesión**.")

    st.markdown("##### Crear cuenta")
    render_formulario_registro(key_prefix="portal_reg", on_session_ok=on_session_ok)

    st.divider()
    st.markdown("##### Iniciar sesión")
    render_formulario_login(key_prefix="portal_log", on_session_ok=on_session_ok)


def _navegar_a_portal_seguimos(portal_tab: str) -> None:
    """Abre el modo Seguimos en el portal (evita import circular al cargar el módulo)."""
    from modules import seguimos as _seg

    st.session_state.modo_actual = _seg.MODO_ID
    st.session_state.seguimos_paso = _seg.SEGUIMOS_PASO_PORTAL
    st.session_state.seguimos_portal_tab = portal_tab


def render_barra_sesion_compacta() -> None:
    """En una vista de modo: sesión o acceso visible a registro / login en Seguimos."""
    if not _supabase_ok():
        st.info(
            "💡 **Cuenta de participante:** configura `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` "
            "en secrets para activar el registro."
        )
        return
    if sesion_activa():
        c1, c2 = st.columns([5, 1])
        with c1:
            nom = st.session_state.get("auth_estudiante_nombre", "Estudiante")
            em = st.session_state.get("auth_estudiante_email", "")
            st.success(f"Sesión: **{nom}** · `{em}`")
        with c2:
            if st.button("Cerrar sesión", key="auth_compact_logout"):
                cerrar_sesion()
                st.rerun()
    else:
        st.warning("No has iniciado sesión: tu progreso no queda vinculado a un perfil en la nube.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Registrarme", type="primary", use_container_width=True, key="auth_compact_reg"):
                _navegar_a_portal_seguimos("registro")
                st.rerun()
        with c2:
            if st.button("Iniciar sesión", use_container_width=True, key="auth_compact_login"):
                _navegar_a_portal_seguimos("login")
                st.rerun()


def render_panel_auth() -> None:
    """Bloque superior en la portada: registro / login o resumen de sesión."""
    if not _supabase_ok():
        st.caption(
            "💡 **Registro en base de datos:** configura `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` "
            "en secrets y ejecuta `supabase_estudiantes.sql` en el SQL Editor."
        )
        return

    if sesion_activa():
        c1, c2 = st.columns([4, 1])
        with c1:
            nom = st.session_state.get("auth_estudiante_nombre", "Estudiante")
            em = st.session_state.get("auth_estudiante_email", "")
            inst = st.session_state.get("auth_estudiante_institucion")
            suf = f" · {inst}" if inst else ""
            st.success(f"Sesión: **{nom}**{suf} (`{em}`)")
        with c2:
            if st.button("Cerrar sesión", use_container_width=True, key="auth_home_logout"):
                cerrar_sesion()
                st.rerun()
        return

    tab_reg, tab_in = st.tabs(["Crear cuenta", "Iniciar sesión"])
    with tab_reg:
        render_formulario_registro(key_prefix="home")
    with tab_in:
        render_formulario_login(key_prefix="home")
