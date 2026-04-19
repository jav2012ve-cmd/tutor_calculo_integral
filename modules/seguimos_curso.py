"""
Seguimiento del temario canónico Σigma (bloque dentro de «Tu Ruta Maestra Σigma»): trazado por ``temario.LISTA_TEMAS``.

Independiente de consultas puntuales en otros modos: aquí solo cuentan eventos
``seguimos_practica_ok`` (A practicar) y ``quiz_respuesta_correcta`` (Simulacro),
con ``tema`` normalizado al texto oficial del curso.

Criterio de **tema superado**: al menos **5** ejercicios de práctica completados
y **5** respuestas correctas en autoevaluación **en ese mismo tema**.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import streamlit as st

from modules import temario

META_PRACTICA = 5
META_QUIZ = 5
EVENTO_PRACTICA_OK = "seguimos_practica_ok"
EVENTO_QUIZ_OK = "quiz_respuesta_correcta"

# Planificación orientativa (horas por bloque del temario)
HORAS_OBJETIVO_POR_TEMA = 4.0
PESO_PRACTICA_EN_CRONO = 0.62
PESO_QUIZ_EN_CRONO = 0.38


def _parse_payload(pl: Any) -> dict[str, Any]:
    if isinstance(pl, dict):
        return pl
    if isinstance(pl, str) and pl.strip():
        try:
            o = json.loads(pl)
            return o if isinstance(o, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def conteos_minicurso_por_tema(eventos: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Acumula conteos por tema oficial a partir de filas ``app_usage_event``."""
    out: dict[str, dict[str, int]] = {
        t: {"practica_ok": 0, "quiz_ok": 0} for t in temario.LISTA_TEMAS
    }
    for row in eventos:
        modo = (row.get("modo") or "").strip()
        pl = _parse_payload(row.get("payload"))
        tema = temario.normalizar_tema_curso(pl.get("tema"))
        if not tema or tema not in out:
            continue
        if modo == "Entrenamiento" and pl.get("tipo_evento") == EVENTO_PRACTICA_OK:
            out[tema]["practica_ok"] += 1
        elif modo == "Quiz" and pl.get("tipo_evento") == EVENTO_QUIZ_OK:
            out[tema]["quiz_ok"] += 1
    return out


def tema_superado(slots: dict[str, int]) -> bool:
    return int(slots.get("practica_ok", 0)) >= META_PRACTICA and int(slots.get("quiz_ok", 0)) >= META_QUIZ


def etiqueta_tema_corta(tema_completo: str) -> str:
    partes = tema_completo.split(" ", 1)
    cod = partes[0].strip()
    if len(partes) < 2:
        return cod
    rest = partes[1].strip()
    if len(rest) > 56:
        rest = rest[:53].rstrip() + "…"
    return f"{cod} — {rest}"


def orden_temario() -> list[str]:
    return list(temario.LISTA_TEMAS)


def primera_tema_pendiente(conteos: dict[str, dict[str, int]]) -> Optional[str]:
    for t in orden_temario():
        if not tema_superado(conteos.get(t, {"practica_ok": 0, "quiz_ok": 0})):
            return t
    return None


def lista_temas_superados(conteos: dict[str, dict[str, int]]) -> list[str]:
    return [t for t in orden_temario() if tema_superado(conteos.get(t, {"practica_ok": 0, "quiz_ok": 0}))]


def fraccion_actividad_hacia_meta(slots: dict[str, int]) -> float:
    p = min(META_PRACTICA, max(0, int(slots.get("practica_ok", 0)))) / float(META_PRACTICA)
    q = min(META_QUIZ, max(0, int(slots.get("quiz_ok", 0)))) / float(META_QUIZ)
    return min(1.0, p * PESO_PRACTICA_EN_CRONO + q * PESO_QUIZ_EN_CRONO)


def horas_equivalentes_avance(slots: dict[str, int]) -> float:
    return round(HORAS_OBJETIVO_POR_TEMA * fraccion_actividad_hacia_meta(slots), 2)


def render_panel_minicurso(
    *,
    eventos: list[dict[str, Any]],
    sesion_supabase: bool,
) -> None:
    """Bloque de seguimiento 5+5 del temario canónico (pestaña Continuidad)."""
    st.markdown("### Temario canónico Σigma (seguimiento 5+5)")
    st.markdown(
        "<div style='color:#1e293b;font-size:1.02rem;line-height:1.55;margin-bottom:0.75rem;'>"
        "Es un <strong>itinerario guiado</strong> por el temario en bloques cortos. "
        "Las consultas o prácticas que hagas fuera de esta meta <strong>no sustituyen</strong> "
        "los conteos del minicurso: aquí solo suman los ejercicios de "
        "<strong>A practicar</strong> completados y las respuestas correctas del "
        "<strong>Simulacro</strong>, siempre con el <strong>tema del ítem</strong> reconocido por la app."
        "</div>",
        unsafe_allow_html=True,
    )

    if not sesion_supabase:
        st.info(
            "**Inicia sesión** con tu cuenta de participante para que guardemos el minicurso "
            "en la nube (eventos vinculados a tu perfil). Sin sesión, aquí solo verás el temario de referencia."
        )
        return

    conteos = conteos_minicurso_por_tema(eventos)
    hechos = lista_temas_superados(conteos)
    actual = primera_tema_pendiente(conteos)

    n_total = len(orden_temario())
    st.metric("Bloques del temario superados", f"{len(hechos)} / {n_total}")

    if hechos:
        with st.expander("Temas ya superados (5 práctica + 5 simulacro correctos)", expanded=len(hechos) <= 6):
            for t in hechos:
                st.markdown(f"- **{etiqueta_tema_corta(t)}**")

    if actual is None:
        st.success(
            "Has completado el **temario completo** del minicurso según el criterio establecido "
            f"({META_PRACTICA} prácticas + {META_QUIZ} simulacros por bloque). ¡Felicitaciones!"
        )
        return

    slots = conteos.get(actual, {"practica_ok": 0, "quiz_ok": 0})
    n_pr = int(slots.get("practica_ok", 0))
    n_qz = int(slots.get("quiz_ok", 0))
    frac = fraccion_actividad_hacia_meta(slots)
    h_eq = horas_equivalentes_avance(slots)

    st.markdown("#### Tema en foco (siguiente bloque atómico)")
    st.markdown(
        f"<div style='font-size:1.15rem;font-weight:700;color:#0f172a;padding:0.65rem 0.85rem;"
        f"background:linear-gradient(90deg,#e0f2fe 0%,#f8fafc 100%);border-radius:10px;"
        f"border-left:5px solid #0284c7;'>{etiqueta_tema_corta(actual)}</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Meta por este bloque: **{META_PRACTICA}** ejercicios de **A practicar** (paso a paso hasta el resultado) "
        f"y **{META_QUIZ}** respuestas **correctas** en **Simulacro**, con preguntas etiquetadas en ese tema."
    )

    c_pr, c_qz = st.columns(2)
    with c_pr:
        st.markdown("**Práctica (A practicar)**")
        st.progress(min(1.0, n_pr / float(META_PRACTICA)), text=f"{min(n_pr, META_PRACTICA)} / {META_PRACTICA}")
    with c_qz:
        st.markdown("**Autoevaluación (Simulacro)**")
        st.progress(min(1.0, n_qz / float(META_QUIZ)), text=f"{min(n_qz, META_QUIZ)} / {META_QUIZ}")

    st.markdown("#### Ritmo frente al tiempo orientativo")
    st.markdown(
        "<div style='color:#334155;font-size:0.98rem;line-height:1.5;'>"
        f"Para cada bloque asumimos unas <strong>{HORAS_OBJETIVO_POR_TEMA:g} h</strong> de estudio repartidas "
        f"({int(PESO_PRACTICA_EN_CRONO * 100)} % práctica guiada · {int(PESO_QUIZ_EN_CRONO * 100)} % simulacro). "
        "La barra inferior refleja cuánto del **plan** llevas según esas metas numéricas, no un cronómetro real."
        "</div>",
        unsafe_allow_html=True,
    )
    st.progress(frac, text=f"Avance del plan en este tema: {frac:.0%} (~{h_eq} h equivalentes / {HORAS_OBJETIVO_POR_TEMA:g} h sugeridas)")

    st.markdown("##### Cómo avanzar")
    st.markdown(
        f"""
        1. Abre **A practicar**, elige **solo** el tema en foco (o inclúyelo entre pocos temas) y completa ejercicios
           hasta el **resultado final**; cada uno cuenta +1 (máx. {META_PRACTICA} por bloque en el registro).
        2. Abre **Simulacro** con el mismo tema en la selección; cada acierto cuenta +1 (máx. {META_QUIZ} por bloque).
        3. Vuelve a **Tu Ruta Maestra Σigma** para ver el progreso actualizado.
        """
    )
