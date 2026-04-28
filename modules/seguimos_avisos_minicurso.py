"""
Tres avisos semanales «interdiarios» (lun / mié / vie) ligados al minicurso 5+5.

Se muestran al abrir **Tu Ruta Maestra Σigma** con sesión y Supabase: proponen
práctica guiada, refuerzo y simulacro alineados al temario en foco del minicurso.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any, Optional

import streamlit as st

from modules import seguimos_curso

# (weekday Python: lunes=0, …), índice de aviso 0..2
_DIA_SLOT: tuple[tuple[int, int], ...] = ((0, 0), (2, 1), (4, 2))
_ETIQUETA_DIA: dict[int, str] = {0: "lunes", 2: "miércoles", 4: "viernes"}

_SESSION_DESCARTE = "minicurso_aviso_descartado_iso_slot"


def _slot_hoy() -> Optional[tuple[int, str]]:
    """Devuelve (slot 0..2, etiqueta_día) si hoy corresponde aviso; si no, None."""
    wd = date.today().weekday()
    for d, slot in _DIA_SLOT:
        if wd == d:
            return (slot, _ETIQUETA_DIA.get(d, "hoy"))
    return None


def _semana_desde_inicio_curso(fecha_iso: str | None) -> Optional[int]:
    if not (fecha_iso or "").strip():
        return None
    try:
        d0 = datetime.strptime(fecha_iso.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    today = date.today()
    if today < d0:
        return 1
    return (today - d0).days // 7 + 1


def _tema_refuerzo_menor_suma(conteos: dict[str, dict[str, int]], orden: list[str]) -> Optional[str]:
    pend = [t for t in orden if not seguimos_curso.tema_superado(conteos.get(t, {"practica_ok": 0, "quiz_ok": 0}))]
    if not pend:
        return None

    def suma(t: str) -> int:
        s = conteos.get(t) or {}
        return int(s.get("practica_ok", 0)) + int(s.get("quiz_ok", 0))

    return min(pend, key=lambda t: (suma(t), orden.index(t) if t in orden else 999))


def _tema_prioridad_simulacro(conteos: dict[str, dict[str, int]], orden: list[str]) -> Optional[str]:
    pend = [t for t in orden if not seguimos_curso.tema_superado(conteos.get(t, {"practica_ok": 0, "quiz_ok": 0}))]
    if not pend:
        return None

    def quiz_ok(t: str) -> int:
        return int((conteos.get(t) or {}).get("quiz_ok", 0))

    return min(pend, key=lambda t: (quiz_ok(t), orden.index(t) if t in orden else 999))


def _payload_aviso(
    slot: int,
    conteos: dict[str, dict[str, int]],
    orden: list[str],
) -> Optional[dict[str, Any]]:
    foco = seguimos_curso.primera_tema_pendiente(conteos)
    refuerzo = _tema_refuerzo_menor_suma(conteos, orden)
    sim_tema = _tema_prioridad_simulacro(conteos, orden)

    if slot == 0:
        if not foco:
            return None
        return {
            "titulo": "Aviso 1/3 — Ritmo del minicurso (práctica guiada)",
            "cuerpo": (
                f"**{seguimos_curso.etiqueta_tema_corta(foco)}** es tu bloque en foco. "
                f"Completa hasta **{seguimos_curso.META_PRACTICA}** ejercicios en **A practicar** "
                "cerrando cada ítem hasta el resultado final para que cuenten en el minicurso."
            ),
            "tema_practica": foco,
            "temas_simulacro": [foco],
            "mostrar_reto": True,
        }
    if slot == 1:
        t = refuerzo or foco
        if not t:
            return None
        return {
            "titulo": "Aviso 2/3 — Refuerzo intermedio de la semana",
            "cuerpo": (
                f"**{seguimos_curso.etiqueta_tema_corta(t)}** es un buen candidato para repasar: "
                "priorizamos el tema pendiente con **menor volumen 5+5** acumulado. "
                "Una sesión corta hoy mantiene la materia al día."
            ),
            "tema_practica": t,
            "temas_simulacro": [t],
            "mostrar_reto": True,
        }
    # slot == 2
    t_sim = sim_tema or foco
    if not t_sim:
        return None
    n_q = int((conteos.get(t_sim) or {}).get("quiz_ok", 0))
    return {
        "titulo": "Aviso 3/3 — Cierra la semana con simulacro",
        "cuerpo": (
            f"En **{seguimos_curso.etiqueta_tema_corta(t_sim)}** llevas **{n_q} / {seguimos_curso.META_QUIZ}** "
            "aciertos de simulacro reconocidos para el minicurso. "
            "Haz un **Simulacro personalizado** con ese tema para sumar al cierre 5+5."
        ),
        "tema_practica": t_sim,
        "temas_simulacro": [t_sim],
        "mostrar_reto": False,
    }


def render_avisos_minicurso_semanales(
    *,
    eventos: list[dict[str, Any]],
    sesion_supabase: bool,
    on_practicar_tema: Callable[[str], None],
    on_simulacro_temas: Callable[[list[str]], None],
    on_reto_tema: Callable[[str], None],
) -> None:
    if not sesion_supabase:
        return
    hit = _slot_hoy()
    if not hit:
        return
    slot, dia_txt = hit
    hoy = date.today().isoformat()
    if st.session_state.get(_SESSION_DESCARTE) == f"{hoy}-{slot}":
        return

    orden = seguimos_curso.orden_temario()
    conteos = seguimos_curso.conteos_minicurso_por_tema(eventos)
    payload = _payload_aviso(slot, conteos, orden)
    if not payload:
        st.success(
            "Minicurso al día: no hay bloques pendientes con la meta 5+5. "
            "Sigue usando **A practicar** y **Simulacro** cuando quieras repasar."
        )
        return

    sem = _semana_desde_inicio_curso(st.session_state.get("auth_estudiante_fecha_inicio_curso"))
    subt = ""
    if sem is not None:
        subt = f" _(semana orientativa {sem} desde tu fecha de inicio de curso)_"

    st.markdown(f"##### Recordatorio semanal — {dia_txt.capitalize()}{subt}")
    with st.container(border=True):
        st.markdown(f"**{payload['titulo']}**")
        st.markdown(payload["cuerpo"])

        tp = str(payload["tema_practica"])
        ts = list(payload["temas_simulacro"])

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("A practicar (tema sugerido)", key=f"minicurso_aviso_pr_{slot}", use_container_width=True):
                on_practicar_tema(tp)
        with c2:
            if st.button("Simulacro (mismos temas)", key=f"minicurso_aviso_qz_{slot}", use_container_width=True):
                on_simulacro_temas(ts)
        with c3:
            if payload.get("mostrar_reto") and st.button(
                "Serie del banco (reto)",
                key=f"minicurso_aviso_rt_{slot}",
                use_container_width=True,
                help="Abre A practicar con una serie corta del banco para el tema sugerido.",
            ):
                on_reto_tema(tp)

        if st.button("Ocultar este aviso hoy", key=f"minicurso_aviso_hide_{slot}"):
            st.session_state[_SESSION_DESCARTE] = f"{hoy}-{slot}"
            st.rerun()

        st.caption(
            "Tres avisos por semana (lunes, miércoles, viernes), al abrir esta pantalla. "
            "Cada uno enlaza al minicurso: práctica guiada y simulacro cuentan cuando el tema del ítem coincide."
        )
