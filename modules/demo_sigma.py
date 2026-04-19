"""
Modo demo (sin cuenta): permite abrir los modos de estudio con un tope de consultas IA por función.
Con sesión iniciada no aplica límite ni consumo.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

DEMO_MAX_CONSULTAS_POR_FUNCION = 3

ACTIVO_KEY = "sigma_demo_activo"
USOS_KEY = "sigma_demo_usos"

# Claves consumidas en ``generar_contenido_seguro`` (una por «funcionalidad» de la portada).
CLAVE_ENTRENAMIENTO = "entrenamiento"
CLAVE_GUIADA = "guiada"
CLAVE_QUIZ = "quiz"
CLAVE_TUTOR = "tutor"
CLAVE_MANUSCRITO = "manuscrito"

_ETIQUETAS_USO: dict[str, str] = {
    CLAVE_ENTRENAMIENTO: "A practicar",
    CLAVE_GUIADA: "Paso a paso",
    CLAVE_QUIZ: "Simulacro",
    CLAVE_TUTOR: "Preguntas abiertas",
    CLAVE_MANUSCRITO: "Manuscritos",
}


def _sesion_participante_activa() -> bool:
    return bool(st.session_state.get("auth_estudiante_id"))


def demo_activo() -> bool:
    return bool(st.session_state.get(ACTIVO_KEY))


def acceso_modos_sin_login() -> bool:
    """True si puede ver la cuadrícula de modos (sesión o demo)."""
    return _sesion_participante_activa() or demo_activo()


def activar_demo() -> None:
    st.session_state[ACTIVO_KEY] = True
    if USOS_KEY not in st.session_state or not isinstance(st.session_state.get(USOS_KEY), dict):
        st.session_state[USOS_KEY] = {}


def desactivar_demo_al_volver_portada() -> None:
    st.session_state.pop(ACTIVO_KEY, None)
    st.session_state.pop(USOS_KEY, None)


def usos_demo(clave: str) -> int:
    d = st.session_state.get(USOS_KEY)
    if not isinstance(d, dict):
        return 0
    return int(d.get(clave, 0) or 0)


def usos_restantes_demo(clave: str) -> int:
    return max(0, DEMO_MAX_CONSULTAS_POR_FUNCION - usos_demo(clave))


def puede_usar_demo_ia(clave: str | None) -> bool:
    if not clave:
        return True
    if _sesion_participante_activa():
        return True
    if not demo_activo():
        return True
    return usos_demo(clave) < DEMO_MAX_CONSULTAS_POR_FUNCION


def consumir_demo_ia(clave: str | None) -> None:
    if not clave or _sesion_participante_activa() or not demo_activo():
        return
    raw = st.session_state.get(USOS_KEY)
    d: dict[str, int] = dict(raw) if isinstance(raw, dict) else {}
    d[clave] = int(d.get(clave, 0) or 0) + 1
    st.session_state[USOS_KEY] = d


def mostrar_banner_usos_demo() -> None:
    if not demo_activo() or _sesion_participante_activa():
        return
    partes = []
    for clave in (
        CLAVE_ENTRENAMIENTO,
        CLAVE_GUIADA,
        CLAVE_QUIZ,
        CLAVE_TUTOR,
        CLAVE_MANUSCRITO,
    ):
        et = _ETIQUETAS_USO.get(clave, clave)
        partes.append(f"{et}: {usos_restantes_demo(clave)}/{DEMO_MAX_CONSULTAS_POR_FUNCION}")
    st.info(
        "**Modo demo** — Consultas de IA restantes por función: "
        + " · ".join(partes)
        + ". Con una cuenta puedes usar todo sin este límite."
    )


def ruta_imagen_portada_bienvenida() -> str | None:
    """Ruta absoluta a la imagen de bienvenida (mockup), si existe."""
    here = Path(__file__).resolve().parents[1]
    env = (os.environ.get("SIGMA_PORTADA_IMAGEN") or "").strip()
    if env and os.path.isfile(env):
        return env
    candidatos = [
        here / "assets" / "portada_sigma_hud.png",
        here / "assets" / "portada_sigma_hud.jpg",
        here / "portada_sigma_hud.png",
        here / "portada_sigma_hud.jpg",
    ]
    for p in candidatos:
        if p.is_file():
            return str(p)
    return None
