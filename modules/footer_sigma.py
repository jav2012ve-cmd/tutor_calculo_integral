"""
Pie de página (footer) del tutor Σigma — diseño tipo SaaS académico premium.

Llamar ``render_footer_sigma()`` al final del panel central o en cualquier vista.
El bloque principal va dentro de ``st.container()`` con estilos inyectados (HTML/CSS).
"""

from __future__ import annotations

import html as html_lib
import os
from typing import Optional

import streamlit as st

from modules import uso_stats

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


def _build_footer_html(
    total: int,
    u_guias: str,
    u_soporte: str,
    u_priv: str,
) -> str:
    total_s = f"{total:,}".replace(",", " ")
    ag = html_lib.escape(u_guias, quote=True)
    aso = html_lib.escape(u_soporte, quote=True)
    ap = html_lib.escape(u_priv, quote=True)

    return f"""
<style>
.sigma-footer-premium {{
  background: linear-gradient(90deg, #0e1117 0%, #1c2b4b 100%);
  border-top: 2px solid #00ccff;
  padding: 2rem;
  border-radius: 15px 15px 0 0;
  color: #e0e0e0;
  box-sizing: border-box;
  margin-top: 0.25rem;
}}
.sigma-footer-premium * {{
  box-sizing: border-box;
}}
.sigma-footer-grid {{
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1.75rem 1.5rem;
  align-items: start;
}}
@media (max-width: 900px) {{
  .sigma-footer-grid {{ grid-template-columns: 1fr; }}
}}
.sigma-footer-brand-title {{
  font-size: 1.12rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.02em;
  margin: 0 0 0.45rem 0;
  line-height: 1.3;
}}
.sigma-footer-brand-body {{
  font-size: 0.95rem;
  line-height: 1.55;
  color: #e0e0e0;
  margin: 0;
}}
.sigma-footer-brand-body strong {{
  color: #f1f5f9;
  font-weight: 600;
}}
.sigma-footer-section-title {{
  font-size: 0.98rem;
  font-weight: 700;
  color: #f5e6c8;
  margin: 0 0 0.65rem 0;
  letter-spacing: 0.02em;
}}
.sigma-footer-metric-value {{
  font-size: 2.1rem;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.1;
  margin: 0 0 0.2rem 0;
}}
.sigma-footer-metric-label {{
  font-size: 0.82rem;
  font-weight: 500;
  color: #cbd5e1;
  margin: 0 0 0.5rem 0;
}}
.sigma-footer-metric-hint {{
  font-size: 0.78rem;
  color: #94a3b8;
  margin: 0;
  line-height: 1.4;
}}
.sigma-footer-links {{
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}}
.sigma-footer-outline-link {{
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.85rem;
  border: 1px solid rgba(0, 204, 255, 0.5);
  border-radius: 8px;
  color: #e0f7ff !important;
  text-decoration: none !important;
  font-size: 0.88rem;
  font-weight: 500;
  background: transparent;
  transition: border-color 0.15s ease, background 0.15s ease;
  width: fit-content;
  max-width: 100%;
}}
.sigma-footer-outline-link:hover {{
  border-color: #00ccff;
  background: rgba(0, 204, 255, 0.08);
  color: #ffffff !important;
}}
</style>
<div class="sigma-footer-premium" role="contentinfo">
  <div class="sigma-footer-grid">
    <div>
      <p class="sigma-footer-brand-title">🎓 &nbsp;Σigma: Ecosistema de Aprendizaje Adaptativo</p>
      <p class="sigma-footer-brand-body">
        Proyecto de soporte académico especializado en <strong>Cálculo Integral</strong> y
        <strong>Ecuaciones Diferenciales</strong> para Facultades de Ingeniería y Ciencias Económicas en Venezuela.
      </p>
    </div>
    <div>
      <p class="sigma-footer-section-title">Impacto Σigma</p>
      <p class="sigma-footer-metric-value">{html_lib.escape(total_s)}</p>
      <p class="sigma-footer-metric-label">Dudas Resueltas</p>
      <p class="sigma-footer-metric-hint">Interacciones procesadas en tiempo real.</p>
    </div>
    <div>
      <p class="sigma-footer-section-title">Recursos</p>
      <div class="sigma-footer-links">
        <a class="sigma-footer-outline-link" href="{ag}" target="_blank" rel="noopener noreferrer">📘&nbsp;Guías de Estudio</a>
        <a class="sigma-footer-outline-link" href="{aso}" target="_blank" rel="noopener noreferrer">⚙️&nbsp;Soporte Técnico</a>
        <a class="sigma-footer-outline-link" href="{ap}" target="_blank" rel="noopener noreferrer">🔒&nbsp;Política de Privacidad</a>
      </div>
    </div>
  </div>
</div>
"""


def render_footer_sigma(
    *,
    mostrar_advertencia_uso: bool = True,
    enlaces_guias: Optional[str] = None,
    enlaces_soporte: Optional[str] = None,
    enlaces_privacidad: Optional[str] = None,
) -> None:
    """
    Cintillo final premium: ``st.container`` + gradiente, grid 2-1-1, métrica, enlaces tipo outline e iconos.

    El copyright final usa ``st.caption`` (gris legible sobre el fondo claro de Streamlit), debajo del panel oscuro.
    ``enlaces_*``: si se pasan, sustituyen las URLs por defecto.
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

    bloque = _build_footer_html(total, u_guias, u_soporte, u_priv)

    with st.container():
        st.markdown(bloque, unsafe_allow_html=True)
    st.caption(
        "© 2026 Σigma Tutor Inteligente. Desarrollado con tecnología de IA de última generación "
        "para el éxito académico nacional."
    )
