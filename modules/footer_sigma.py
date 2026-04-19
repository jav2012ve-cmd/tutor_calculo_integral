"""
Pie de página (footer) del tutor Σigma — diseño tipo SaaS académico.

Llamar ``render_footer_sigma()`` al final del panel central o en cualquier vista
donde se desee el cintillo de marca, métricas y enlaces.
"""

from __future__ import annotations

import os
from typing import Optional

import streamlit as st

from modules import uso_stats

# URLs públicas (sobrescribibles por entorno para despliegues reales).
_ENV_BASE = (os.environ.get("SIGMA_PUBLIC_URL") or "").strip().rstrip("/")


def _url(path: str, fallback: str) -> str:
    if _ENV_BASE:
        return f"{_ENV_BASE}{path}" if path.startswith("/") else f"{_ENV_BASE}/{path}"
    return fallback


GUIAS_URL = _url("/guias", "https://docs.streamlit.io")
SOPORTE_URL = _url("/soporte", "https://github.com/jav2012ve-cmd/tutor_calculo_integral/issues")
PRIVACIDAD_URL = _url("/privacidad", "https://example.com/politica-privacidad-sigma")


def _total_interacciones() -> int:
    stats = uso_stats.obtener_estadisticas()
    return sum(int(stats.get(m, 0) or 0) for m in uso_stats.MODULOS)


def render_footer_sigma(
    *,
    mostrar_advertencia_uso: bool = True,
    enlaces_guias: Optional[str] = None,
    enlaces_soporte: Optional[str] = None,
    enlaces_privacidad: Optional[str] = None,
) -> None:
    """
    Cintillo final: autoridad de marca, métrica de impacto, enlaces y copyright.

    ``enlaces_*``: si se pasan, sustituyen las URLs por defecto (p. ej. sitio propio en producción).
    """
    st.divider()

    if mostrar_advertencia_uso:
        warn = st.session_state.get("_uso_stats_supabase_warn")
        if warn:
            st.caption(warn)

    total = _total_interacciones()
    u_guias = enlaces_guias or GUIAS_URL
    u_soporte = enlaces_soporte or SOPORTE_URL
    u_priv = enlaces_privacidad or PRIVACIDAD_URL

    try:
        c1, c2, c3 = st.columns([2, 1, 1], gap="large")
    except TypeError:
        c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        st.markdown(
            """
<div style="color:#0f172a;font-size:0.95rem;line-height:1.55;">
  <div style="font-size:1.12rem;font-weight:700;margin-bottom:0.4rem;color:#0c4a6e;letter-spacing:-0.02em;">
    🎓 &nbsp;Σigma: Ecosistema de Aprendizaje Adaptativo
  </div>
  <div style="color:#475569;">
    Proyecto de soporte académico especializado en <strong>Cálculo Integral</strong> y
    <strong>Ecuaciones Diferenciales</strong> para Facultades de Ingeniería y Ciencias Económicas en Venezuela.
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            '<p style="margin:0 0 0.35rem 0;font-size:0.95rem;font-weight:600;color:#0f172a;">Impacto Σigma</p>',
            unsafe_allow_html=True,
        )
        st.metric(label="Dudas Resueltas", value=f"{total:,}".replace(",", " "))
        st.caption("Interacciones procesadas en tiempo real.")

    with c3:
        st.markdown(
            '<p style="margin:0 0 0.35rem 0;font-size:0.95rem;font-weight:600;color:#0f172a;">Recursos</p>',
            unsafe_allow_html=True,
        )
        if hasattr(st, "link_button"):
            st.link_button("Guías de Estudio", u_guias, use_container_width=True)
            st.link_button("Soporte Técnico", u_soporte, use_container_width=True)
            st.link_button("Política de Privacidad", u_priv, use_container_width=True)
        else:
            st.markdown(
                f'<p style="font-size:0.9rem;line-height:1.7;">'
                f'<a href="{u_guias}" target="_blank" rel="noopener noreferrer" '
                f'style="color:#0369a1;text-decoration:none;">Guías de Estudio</a><br/>'
                f'<a href="{u_soporte}" target="_blank" rel="noopener noreferrer" '
                f'style="color:#0369a1;text-decoration:none;">Soporte Técnico</a><br/>'
                f'<a href="{u_priv}" target="_blank" rel="noopener noreferrer" '
                f'style="color:#0369a1;text-decoration:none;">Política de Privacidad</a>'
                f"</p>",
                unsafe_allow_html=True,
            )

    _, c_copy, _ = st.columns([1, 4, 1])
    with c_copy:
        st.caption(
            "© 2026 Σigma Tutor Inteligente. Desarrollado con tecnología de IA de última generación "
            "para el éxito académico nacional."
        )
