"""
Registro e inicio de sesión de participantes contra Supabase (tabla app_estudiante).
Campos: nombre, cédula, correo, institución, carrera, semestre, fecha de nacimiento y contraseña (hash bcrypt).
Requiere SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY en secrets o entorno.
"""

from __future__ import annotations

import base64
import html
import re
import urllib.parse
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

import bcrypt
import requests
import streamlit as st

from modules import contexto_universitario, interfaz, planes_estudio_oficiales, uso_stats

_TABLE = "app_estudiante"
_TIMEOUT = 15
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_CEDULA_TOKEN_RE = re.compile(r"^[\w.-]+$", re.UNICODE)
_ROOT_DIR = Path(__file__).resolve().parents[1]


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
    s = (email or "").strip().lower()
    # Evita fallos de login por caracteres invisibles pegados al copiar/pegar.
    return re.sub(r"[\u200b\u200c\u200d\ufeff]", "", s)


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
    url = f"{_base_url()}/rest/v1/{_TABLE}?email=eq.{q}&select=*"
    try:
        r = requests.get(url, headers=_headers(), timeout=_TIMEOUT)
        if r.status_code != 200:
            # No exponer detalle al usuario; ayuda a depurar en logs de Streamlit Cloud.
            print(f"[auth] GET estudiante {r.status_code}: {(r.text or '')[:300]}")
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
    carrera: str,
    semestre: str,
) -> tuple[bool, str]:
    """
    Crea fila en app_estudiante. Devuelve (éxito, mensaje).
    """
    if not _supabase_ok():
        return False, "Supabase no está configurado (SUPABASE_URL y clave service_role)."

    em = normalizar_email(email)
    if not validar_email(em):
        return False, "Correo no válido."
    if len((password or "").strip()) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."

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

    car = (carrera or "").strip()
    if len(car) < 2:
        return False, "Indica la carrera o programa que estudias."
    if len(car) > 120:
        return False, "El nombre de la carrera es demasiado largo."

    sem = (semestre or "").strip()
    if len(sem) < 1:
        return False, "Indica el semestre que cursas (ej. 4, 2025-1)."
    if len(sem) > 40:
        return False, "El semestre indicado es demasiado largo."

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
        "password_hash": _hash_password((password or "").strip()),
        "nombre": nom,
        "cedula": ced_norm,
        "institucion": inst,
        "fecha_nacimiento": fecha_nacimiento.isoformat(),
        "carrera": car,
        "semestre": sem,
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
        err = (r.text or "")[:400]
        print(f"[auth] POST estudiante {r.status_code}: {err}")
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
    pwd = (password or "").strip()
    row = buscar_por_email(em)
    if not row:
        return False, "Correo o contraseña incorrectos."

    ph = row.get("password_hash") or ""
    if not _verificar_password(pwd, ph):
        return False, "Correo o contraseña incorrectos."

    st.session_state.auth_estudiante_id = str(row["id"])
    st.session_state.auth_estudiante_email = row.get("email") or em
    st.session_state.auth_estudiante_nombre = (
        (row.get("nombre") or row.get("display_name") or "") or ""
    ).strip()
    st.session_state.auth_estudiante_cedula = (row.get("cedula") or "").strip() or None
    st.session_state.auth_estudiante_institucion = (row.get("institucion") or "").strip() or None
    st.session_state.auth_estudiante_carrera = (row.get("carrera") or "").strip() or None
    st.session_state.auth_estudiante_semestre = (row.get("semestre") or "").strip() or None
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

    try:
        uso_stats.registrar_session_heartbeat("login_sesion")
    except Exception:
        pass

    return True, "Sesión iniciada."


def cerrar_sesion() -> None:
    for k in (
        "auth_estudiante_id",
        "auth_estudiante_email",
        "auth_estudiante_nombre",
        "auth_estudiante_codigo",
        "auth_estudiante_cedula",
        "auth_estudiante_institucion",
        "auth_estudiante_carrera",
        "auth_estudiante_semestre",
        "auth_estudiante_fecha_nacimiento",
        "_seguimos_uso_registrado_sesion",
        "_estilo_univ_sig_inyectado",
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
    redirigir_a_login: bool = False,
) -> None:
    with st.form(f"form_registro_{key_prefix}"):
        st.caption("Datos del participante (estudiante universitario).")
        c1, c2 = st.columns(2)
        with c1:
            nom = st.text_input(
                "Nombre completo",
                key=f"{key_prefix}_reg_nombre",
                max_chars=200,
                placeholder="Ej. Ana María Pérez",
            )
            ced = st.text_input(
                "Cédula o documento de identidad",
                key=f"{key_prefix}_reg_cedula",
                max_chars=40,
                placeholder="Ej. V-12345678",
            )
            e2 = st.text_input(
                "Correo electrónico",
                key=f"{key_prefix}_reg_email",
                placeholder="ejemplo@universidad.edu",
            )
        with c2:
            inst = st.text_input(
                "Institución donde estudias",
                key=f"{key_prefix}_reg_institucion",
                max_chars=200,
                placeholder="Ej. UCV · USB · UNIMET · ULA · Monteávila",
            )
            st.caption(
                "Guía: siglas o nombre habitual — **UCV, USB, UNIMET, ULA, LUZ, UC, UNEXPO, UCLA, Monteávila**. "
                "También vale el nombre por extenso (p. ej. *Universidad de Carabobo*)."
            )
            clave_univ = contexto_universitario.clave_malla_desde_institucion(inst)
            if clave_univ in interfaz.MAPA_ESTILOS_INSTITUCIONALES:
                color_univ = interfaz.MAPA_ESTILOS_INSTITUCIONALES[clave_univ]["color_primario"]
                nombre_univ = {
                    "UCV": "UCV",
                    "USB": "USB",
                    "UNIMET": "UNIMET",
                    "ULA": "ULA",
                    "LUZ": "LUZ",
                    "UC": "UC",
                }.get(clave_univ, clave_univ)
                st.markdown(
                    (
                        f"<div style='margin:0.2rem 0 0.5rem 0; padding:0.5rem 0.65rem; "
                        f"border-left:4px solid {color_univ}; background:rgba(148,163,184,0.1); "
                        "border-radius:6px;'>"
                        f"<span style='color:{color_univ}; font-weight:600;'>"
                        f"✨ ¡Excelente! Hemos cargado la malla oficial de la {nombre_univ} para ti"
                        "</span></div>"
                    ),
                    unsafe_allow_html=True,
                )
            carrera = st.text_input(
                "Carrera que estudias",
                key=f"{key_prefix}_reg_carrera",
                max_chars=120,
                placeholder="Ej. Ingeniería Civil",
            )
            semestre = st.text_input(
                "Semestre que cursas",
                key=f"{key_prefix}_reg_semestre",
                max_chars=40,
                placeholder="Ej. 4 · 2025-1",
            )
            hoy = date.today()
            fn = st.date_input(
                "Fecha de nacimiento",
                value=hoy - timedelta(days=365 * 18),
                min_value=hoy - timedelta(days=365 * 100),
                max_value=hoy - timedelta(days=365 * 14),
                key=f"{key_prefix}_reg_fn",
            )
            p2 = st.text_input(
                "Contraseña (mín. 4 caracteres)",
                type="password",
                key=f"{key_prefix}_reg_pass",
            )
            p2b = st.text_input(
                "Repite la contraseña",
                type="password",
                key=f"{key_prefix}_reg_pass2",
            )
        if st.form_submit_button("Registrarme", type="primary"):
            if p2 != p2b:
                st.error("Las contraseñas no coinciden.")
            else:
                ok, msg = registrar_estudiante(e2, p2, nom, ced, inst, fn, carrera, semestre)
                if ok:
                    if redirigir_a_login:
                        st.session_state["seguimos_portal_tab"] = "login"
                        st.session_state["_auth_portal_msg"] = (
                            "Cuenta creada con éxito. Ahora inicia sesión con tu correo y contraseña."
                        )
                        st.rerun()
                    ok_in, msg_in = autenticar(e2, p2)
                    if ok_in:
                        if on_session_ok:
                            on_session_ok()
                        st.rerun()
                    st.success(msg)
                    st.error(
                        "La cuenta se creó, pero no se pudo iniciar sesión automáticamente. "
                        f"Detalle: {msg_in} Prueba **Iniciar sesión** con el mismo correo y contraseña."
                    )
                else:
                    st.error(msg)


def _portal_tarjeta():
    """Contenedor con borde tipo tarjeta (Streamlit >=1.29); si no existe el arg, usa container simple."""
    try:
        return st.container(border=True)
    except TypeError:
        return st.container()


def _tarjeta_beneficios_registro() -> None:
    st.markdown("##### 🚀 Activa tu Ventaja Estratégica")
    st.markdown(
        """
        - 🎯 **Precisión Institucional:** IA entrenada con los parciales y la bibliografía de tu universidad (UCV, USB, UNIMET, ULA, LUZ, UC, UNEXPO, UCLA y Monteávila).
        - 🔥 **Mapa de Calor Personalizado:** Identifica exactamente en qué temas vas a fallar antes del examen real.
        - 🔄 **Sincronización Total:** Tu progreso, dudas y simulacros disponibles en cualquier dispositivo.
        """
    )
    st.caption("Únete a la élite que estudia con inteligencia de datos.")


def _tarjeta_pasos_registro() -> None:
    st.markdown("##### Pasos")
    st.markdown(
        """
        1. Completa el formulario.
        2. Pulsa **Registrarme**.
        3. Entrarás automáticamente al panel.
        """
    )


_PLANES_MATRIZ_FALLBACK: dict[str, dict[str, Any]] = {
    "UNEXPO": {
        "enfoque": "Formación tecnológica aplicada a ingeniería y ciencias exactas.",
        "bibliografia": ["Leithold", "Stewart"],
    },
    "UCLA": {
        "enfoque": "Enfoque integral en ingeniería, agronomía y ciencias en el occidente.",
        "bibliografia": ["Thomas", "Purcell"],
    },
    "Monteavila": {
        "enfoque": "Rigor académico con orientación a gestión, economía y proyectos.",
        "bibliografia": ["Spivak (lecturas selectas)", "Sears & Zemansky"],
    },
}

_CARRERAS_VINCULADAS: dict[str, tuple[str, ...]] = {
    "UCV": ("Ingeniería", "Mecánica", "Eléctrica", "Civil", "Computación", "Física"),
    "USB": ("Ingeniería", "Mecánica", "Eléctrica", "Civil", "Computación", "Física"),
    "UNEXPO": ("Ingeniería", "Mecánica", "Eléctrica", "Civil", "Computación", "Física"),
    "UNIMET": ("Ingeniería", "Economía", "Ciencias Administrativas"),
    "Monteavila": ("Ingeniería", "Economía", "Ciencias Administrativas"),
    "ULA": ("Ingeniería", "Agronomía", "Ciencias"),
    "LUZ": ("Ingeniería", "Agronomía", "Ciencias"),
    "UCLA": ("Ingeniería", "Agronomía", "Ciencias"),
    "UC": ("Ingeniería", "Agronomía", "Ciencias"),
}

_IMAGENES_UNIVERSIDAD_CANDIDATAS: dict[str, tuple[str, ...]] = {
    "UCV": ("UCV.jpg", "UCV.png"),
    "USB": ("USB.jpg", "USB.png"),
    "UNIMET": ("UNIMET.jpg", "UNIMET.png"),
    "ULA": ("ULA.jpg", "ULA.png"),
    "LUZ": ("LUZ.jpg", "LUZ.png"),
    "UC": ("UC.jpg", "UC.png"),
    "UNEXPO": ("UNEXPO.jpg", "UNEXPO.png"),
    "UCLA": ("UCLA.jpg", "UCLA.png"),
    "Monteavila": (
        "Monteavila.jpg",
        "MONTEAVILA.jpg",
        "Monteavila.png",
        "UMA.jpg",
        "ImagenesUniversidades2.png",
    ),
}

_PORTAL_INST_PRESELECCIONADA_KEY = "_auth_portal_institucion_preseleccionada"


@st.cache_data(show_spinner=False)
def _imagen_universidad_data_uri(clave: str) -> Optional[str]:
    mime_por_ext = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    for nombre in _IMAGENES_UNIVERSIDAD_CANDIDATAS.get(clave, ()):
        ruta = _ROOT_DIR / nombre
        if not ruta.exists():
            continue
        ext = ruta.suffix.lower()
        mime = mime_por_ext.get(ext)
        if not mime:
            continue
        try:
            binario = ruta.read_bytes()
        except OSError:
            continue
        encoded = base64.b64encode(binario).decode("ascii")
        return f"data:{mime};base64,{encoded}"
    return None


def render_matriz_universidades(*, key_prefix_registro: str = "portal_reg") -> None:
    """Grilla de universidades de referencia (glass + carreras + hover + selección).

    El título principal «Tu éxito…» lo pinta quien llame (p. ej. el portal), para poder
    colocar antes el copy de registro sin columnas laterales.
    """
    st.markdown("##### Universidades de referencia")
    st.caption(
        "Contenido académico por universidad para orientar enfoque y bibliografía sugerida en el tutor."
    )

    st.markdown(
        """
<style>
.auth-uni-card {
  border-radius: 12px;
  padding: 0.72rem 0.78rem;
  margin-bottom: 0.62rem;
  border-right: 1px solid #cbd5e166;
  border-bottom: 1px solid #cbd5e166;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
  min-height: 268px;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(5px);
  border-top: 6px solid var(--p);
  border-left: 1px solid color-mix(in srgb, var(--p) 28%, transparent);
  transition: box-shadow 0.22s ease, border-color 0.22s ease, transform 0.18s ease;
}
.auth-uni-card:hover {
  border-top-color: var(--s) !important;
  border-left-color: color-mix(in srgb, var(--s) 45%, transparent) !important;
  box-shadow: 0 0 0 2px var(--s), 0 12px 28px rgba(15, 23, 42, 0.12);
  transform: translateY(-2px);
}
</style>
""",
        unsafe_allow_html=True,
    )

    paleta_expandida: dict[str, dict[str, str]] = {
        "UCV": {"emoji": "🏛️"},
        "USB": {"emoji": "🌲"},
        "UNIMET": {"emoji": "⚙️"},
        "ULA": {"emoji": "🏔️", "color_primario": "#1E3A8A", "color_secundario": "#FFFFFF"},
        "LUZ": {"emoji": "☀️", "color_primario": "#B8860B", "color_secundario": "#166534"},
        "UC": {"emoji": "🌄", "color_primario": "#EA580C", "color_secundario": "#166534"},
        "UNEXPO": {
            "emoji": "🔧",
            "color_primario": "#0F766E",
            "color_secundario": "#F97316",
        },
        "UCLA": {
            "emoji": "🌿",
            "color_primario": "#065F46",
            "color_secundario": "#D97706",
        },
        "Monteavila": {
            "emoji": "🏙️",
            "color_primario": "#7C3AED",
            "color_secundario": "#F59E0B",
        },
    }

    def _badge_enfoque(enfoque: str) -> str:
        s = (enfoque or "").lower()
        if any(k in s for k in ("rigor", "analítico", "formal", "demostr")):
            return "Rigor Teórico"
        if any(k in s for k in ("pragmático", "práctic", "aplic", "técnico", "ingenier")):
            return "Aplicación Práctica"
        if any(k in s for k in ("acelerado", "trimestral", "velocidad")):
            return "Ritmo Intensivo"
        return "Método Balanceado"

    def _html_carreras_badges(labels: tuple[str, ...], color_p: str) -> str:
        pills = []
        for lab in labels:
            esc = html.escape(lab)
            pills.append(
                f'<span style="display:inline-block;font-size:0.68rem;font-weight:600;'
                f"color:#fff;background:{html.escape(color_p, quote=True)};"
                f"padding:0.12rem 0.42rem;margin:0.08rem 0.12rem 0.08rem 0;"
                f'border-radius:999px;line-height:1.2;">{esc}</span>'
            )
        inner = "".join(pills)
        return (
            '<div style="margin:0.32rem 0 0.42rem 0;">'
            '<div style="font-size:0.72rem;font-weight:700;color:#334155;margin-bottom:0.22rem;">'
            "Carreras vinculadas</div>"
            f'<div style="line-height:1.45;">{inner}</div></div>'
        )

    claves = (
        "UCV",
        "USB",
        "UNIMET",
        "ULA",
        "LUZ",
        "UC",
        "UNEXPO",
        "UCLA",
        "Monteavila",
    )
    for i in range(0, len(claves), 3):
        cols = st.columns(3)
        fila = claves[i : i + 3]
        for j, clave in enumerate(fila):
            estilo = interfaz.MAPA_ESTILOS_INSTITUCIONALES.get(clave, {})
            plan = planes_estudio_oficiales.PLANES_DETALLADOS.get(
                clave, _PLANES_MATRIZ_FALLBACK.get(clave, {})
            )
            estilo_extra = paleta_expandida.get(clave, {})
            color = str(
                estilo_extra.get("color_primario")
                or estilo.get("color_primario")
                or "#64748b"
            ).strip()
            color_sec = str(
                estilo_extra.get("color_secundario")
                or estilo.get("color_secundario")
                or "#e2e8f0"
            ).strip()
            emoji = str(estilo_extra.get("emoji") or "🎓")
            enfoque_raw = str(plan.get("enfoque") or "Sin enfoque cargado.")
            enfoque = html.escape(enfoque_raw)
            badge = html.escape(_badge_enfoque(enfoque_raw))
            bib = plan.get("bibliografia") or []
            bib_txt_raw = ", ".join(str(x) for x in bib) if bib else "Sin bibliografía sugerida."
            bib_txt = html.escape(bib_txt_raw)
            carreras = _CARRERAS_VINCULADAS.get(clave, ())
            carreras_html = _html_carreras_badges(carreras, color)
            nombre_tarjeta = "Monteávila" if clave == "Monteavila" else clave
            img_data_uri = _imagen_universidad_data_uri(clave)
            if img_data_uri:
                miniatura_html = (
                    '<div style="margin:0.1rem 0 0.5rem 0;">'
                    f'<img src="{img_data_uri}" alt="Campus {html.escape(nombre_tarjeta)}" '
                    'style="width:100%;height:72px;object-fit:cover;border-radius:9px;'
                    f'border:1px solid {color}66;" />'
                    "</div>"
                )
            else:
                miniatura_html = (
                    '<div style="margin:0.1rem 0 0.5rem 0;height:72px;border-radius:9px;'
                    f'background:{color}22;border:1px dashed {color}66;display:flex;'
                    'align-items:center;justify-content:center;font-size:0.8rem;color:#475569;">'
                    "Miniatura próximamente</div>"
                )
            btn_key = f"{key_prefix_registro}_pick_{clave.lower()}"
            with cols[j]:
                st.markdown(
                    f"""
<div class="auth-uni-card" style="--p: {color}; --s: {color_sec}; background: linear-gradient(140deg, {color_sec}22 0%, #ffffff 100%);">
  <div style="font-weight: 700; margin-bottom: 0.35rem;">{emoji} ∑igma para {html.escape(nombre_tarjeta)}</div>
  {miniatura_html}
  <div style="display:inline-block; width: fit-content; font-size: 0.78rem; font-weight: 700; color: #0f172a; background: {color}33; border: 1px solid {color}66; border-radius: 999px; padding: 0.16rem 0.54rem; margin-bottom: 0.28rem;">{badge}</div>
  {carreras_html}
  <div style="font-size: 0.92rem; margin-bottom: 0.35rem; line-height: 1.35;"><strong>Enfoque:</strong> {enfoque}</div>
  <div style="font-size: 0.9rem; line-height: 1.35; margin-top: auto;"><strong>Bibliografía:</strong> {bib_txt}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Elegir {nombre_tarjeta}",
                    key=btn_key,
                    use_container_width=True,
                ):
                    st.session_state[_PORTAL_INST_PRESELECCIONADA_KEY] = nombre_tarjeta
                    st.session_state[f"{key_prefix_registro}_reg_institucion"] = nombre_tarjeta
                    st.rerun()


def render_portal_participante(
    *,
    tab_inicial: str = "registro",
    on_session_ok: Optional[Callable[[], None]] = None,
) -> None:
    """
    Portal dedicado.

    - ``tab_inicial="login"`` (desde «Ya tengo cuenta»): solo correo y contraseña, sin textos de registro.
    - ``tab_inicial="registro"`` (desde «Regístrate»): formulario completo de alta y luego redirección a login.
    """
    if not _supabase_ok():
        st.caption(
            "💡 **Registro en base de datos:** en **Secrets** (TOML), `SUPABASE_URL` y "
            "`SUPABASE_SERVICE_ROLE_KEY`; guarda, reinicia la app y ejecuta `supabase_estudiantes.sql`."
        )
        return

    if tab_inicial == "login":
        portal_msg = st.session_state.pop("_auth_portal_msg", None)
        with _portal_tarjeta():
            st.markdown("### Iniciar sesión")
            if portal_msg:
                st.success(str(portal_msg))
            st.caption("Ingresa el **correo** y la **contraseña** con los que te registraste.")
            render_formulario_login(key_prefix="portal_log", on_session_ok=on_session_ok)
        return

    with _portal_tarjeta():
        st.markdown("### Registro de nuevos estudiantes")
        st.caption(
            "Completa tus datos para crear tu cuenta y enlazar el progreso de estudio con tu perfil."
        )
        try:
            col_ventaja, col_pasos = st.columns(2, gap="large")
        except TypeError:
            col_ventaja, col_pasos = st.columns(2)
        with col_ventaja:
            _tarjeta_beneficios_registro()
        with col_pasos:
            _tarjeta_pasos_registro()

        st.markdown("### 🚀 Tu éxito en Cálculo empieza aquí")
        render_matriz_universidades(key_prefix_registro="portal_reg")
        inst_pre = st.session_state.get(_PORTAL_INST_PRESELECCIONADA_KEY)
        if inst_pre:
            st.caption(f"Institución seleccionada desde la matriz: **{inst_pre}**")
            st.session_state["portal_reg_reg_institucion"] = inst_pre
        st.markdown("#### Crear cuenta")
        render_formulario_registro(
            key_prefix="portal_reg",
            on_session_ok=on_session_ok,
            redirigir_a_login=True,
        )


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
            "💡 **Cuenta de participante:** en **Secrets** (TOML), define `SUPABASE_URL` y "
            "`SUPABASE_SERVICE_ROLE_KEY` (API de Supabase), guarda y **reinicia la app**. "
            "Ejecuta `supabase_estudiantes.sql` en el SQL Editor si aún no creaste la tabla."
        )
        return
    if sesion_activa():
        c1, c2 = st.columns([5, 1])
        with c1:
            nom = st.session_state.get("auth_estudiante_nombre", "Estudiante")
            em = st.session_state.get("auth_estudiante_email", "")
            car = (st.session_state.get("auth_estudiante_carrera") or "").strip()
            sem = (st.session_state.get("auth_estudiante_semestre") or "").strip()
            extra = ""
            if car or sem:
                extra = f" · {car}" + (f" · sem. {sem}" if sem else "")
            st.success(f"Sesión: **{nom}** · `{em}`{extra}")
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
            "💡 **Registro en base de datos:** en **Secrets** (TOML), `SUPABASE_URL` y "
            "`SUPABASE_SERVICE_ROLE_KEY`; guarda, reinicia la app y ejecuta `supabase_estudiantes.sql`."
        )
        return

    if sesion_activa():
        c1, c2 = st.columns([4, 1])
        with c1:
            nom = st.session_state.get("auth_estudiante_nombre", "Estudiante")
            em = st.session_state.get("auth_estudiante_email", "")
            inst = st.session_state.get("auth_estudiante_institucion")
            car = (st.session_state.get("auth_estudiante_carrera") or "").strip()
            sem = (st.session_state.get("auth_estudiante_semestre") or "").strip()
            suf = f" · {inst}" if inst else ""
            if car:
                suf += f" · {car}"
            if sem:
                suf += f" · sem. {sem}"
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
