"""
Pie de página Σigma: HUD cyber / universitario, métrica de uso y sesión.

Llamar ``render_footer_sigma()`` al final del flujo principal de la app para que sea
visible en todas las vistas.
"""

from __future__ import annotations

import html as html_lib
import os
from typing import Optional

import streamlit as st

from modules import auth_estudiantes, uso_stats

_ENV_BASE = (os.environ.get("SIGMA_PUBLIC_URL") or "").strip().rstrip("/")

# Módulos que cuentan como actividad de tutoría / práctica (excluye heartbeats y panel Seguimos).
_MODULOS_DUDAS_RESUELTAS: tuple[str, ...] = (
    "Entrenamiento",
    "Respuesta Guiada",
    "Quiz",
    "Tutor Preguntas Abiertas",
    "Corrección de Manuscritos",
    "Planes de Estudio Oficiales",
)


def _url_soporte() -> str:
    base = _ENV_BASE
    path = "/soporte"
    if base:
        return f"{base}{path}" if path.startswith("/") else f"{base}/{path}"
    return "https://github.com/jav2012ve-cmd/tutor_calculo_integral/issues"


def _contador_dudas_resueltas() -> int:
    stats = uso_stats.obtener_estadisticas()
    return sum(int(stats.get(m, 0) or 0) for m in _MODULOS_DUDAS_RESUELTAS)


def _bloque_sesion_estudiante() -> str:
    if not auth_estudiantes.sesion_activa():
        return (
            '<span class="sigma-footer-hud-muted">Inicia sesión en <strong>Tu Ruta Maestra Σigma</strong> '
            "para vincular tu progreso.</span>"
        )
    nombre = (st.session_state.get("auth_estudiante_nombre") or "").strip() or "Estudiante"
    email = (st.session_state.get("auth_estudiante_email") or "").strip()
    nom_e = html_lib.escape(nombre)
    if email:
        em_e = html_lib.escape(email)
        return (
            f'<span class="sigma-footer-hud-label">Participante</span>'
            f'<span class="sigma-footer-hud-name">{nom_e}</span>'
            f'<span class="sigma-footer-hud-email">{em_e}</span>'
        )
    return (
        f'<span class="sigma-footer-hud-label">Participante</span>'
        f'<span class="sigma-footer-hud-name">{nom_e}</span>'
    )


def _build_footer_hud_html(total_dudas: int, url_soporte: str) -> str:
    total_s = f"{total_dudas:,}".replace(",", "\u202f")
    total_e = html_lib.escape(total_s)
    soporte_e = html_lib.escape(url_soporte, quote=True)
    sesion_html = _bloque_sesion_estudiante()

    return f"""
<style>
.sigma-footer-hud {{
  margin-top: 1.25rem;
  padding: 1.1rem 1.25rem 1.15rem;
  border-radius: 2px 14px 2px 14px;
  background: linear-gradient(
    125deg,
    rgba(14, 17, 23, 0.97) 0%,
    rgba(28, 43, 75, 0.92) 42%,
    rgba(15, 23, 42, 0.96) 100%
  );
  border: 1px solid rgba(0, 204, 255, 0.55);
  box-shadow:
    0 0 0 1px rgba(0, 204, 255, 0.12),
    0 8px 28px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}}
.sigma-footer-hud-inner {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem 1.5rem;
}}
.sigma-footer-hud-brand {{
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 8rem;
}}
.sigma-footer-hud-brand span:first-child {{
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #38bdf8;
  font-weight: 600;
}}
.sigma-footer-hud-brand span:last-child {{
  font-size: 0.95rem;
  font-weight: 700;
  color: #f8fafc;
}}
.sigma-footer-hud-metric {{
  text-align: center;
  min-width: 10rem;
  padding: 0.35rem 0.85rem;
  border-left: 1px solid rgba(148, 163, 184, 0.35);
  border-right: 1px solid rgba(148, 163, 184, 0.35);
}}
.sigma-footer-hud-metric-val {{
  font-size: 1.85rem;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.1;
  text-shadow: 0 0 18px rgba(0, 204, 255, 0.35);
}}
.sigma-footer-hud-metric-lbl {{
  font-size: 0.78rem;
  color: #94a3b8;
  margin-top: 0.15rem;
}}
.sigma-footer-hud-user {{
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  max-width: 22rem;
}}
.sigma-footer-hud-label {{
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #7dd3fc;
}}
.sigma-footer-hud-name {{
  font-size: 1rem;
  font-weight: 700;
  color: #f1f5f9;
}}
.sigma-footer-hud-email {{
  font-size: 0.8rem;
  color: #cbd5e1;
  word-break: break-all;
}}
.sigma-footer-hud-muted {{
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.45;
}}
.sigma-footer-hud-soporte a {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 1rem;
  border: 1px solid rgba(0, 204, 255, 0.65);
  border-radius: 6px;
  color: #e0f7ff !important;
  text-decoration: none !important;
  font-weight: 600;
  font-size: 0.88rem;
  background: rgba(0, 204, 255, 0.08);
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}}
.sigma-footer-hud-soporte a:hover {{
  background: rgba(0, 204, 255, 0.18);
  border-color: #22d3ee;
  box-shadow: 0 0 14px rgba(34, 211, 238, 0.35);
}}
@media (max-width: 720px) {{
  .sigma-footer-hud-metric {{
    border-left: none;
    border-right: none;
    border-top: 1px solid rgba(148, 163, 184, 0.25);
    border-bottom: 1px solid rgba(148, 163, 184, 0.25);
    padding-top: 0.65rem;
    padding-bottom: 0.65rem;
    width: 100%;
  }}
}}
</style>
<div class="sigma-footer-hud" role="contentinfo">
  <div class="sigma-footer-hud-inner">
    <div class="sigma-footer-hud-brand">
      <span>Tutor integral</span>
      <span>Σigma</span>
    </div>
    <div class="sigma-footer-hud-metric">
      <div class="sigma-footer-hud-metric-val">{total_e}</div>
      <div class="sigma-footer-hud-metric-lbl">Dudas resueltas · uso acumulado</div>
    </div>
    <div class="sigma-footer-hud-user">{sesion_html}</div>
    <div class="sigma-footer-hud-soporte">
      <a href="{soporte_e}" target="_blank" rel="noopener noreferrer">💬 Soporte</a>
    </div>
  </div>
</div>
"""


def render_footer_sigma(
    *,
    mostrar_advertencia_uso: bool = True,
    url_soporte: Optional[str] = None,
) -> None:
    """
    Pie global: contador de dudas resueltas (``uso_stats``), bloque de participante si hay sesión,
    enlace de soporte, estética HUD.
    """
    st.divider()

    if mostrar_advertencia_uso:
        warn = st.session_state.get("_uso_stats_supabase_warn")
        if warn:
            st.caption(warn)

    total = _contador_dudas_resueltas()
    soporte = (url_soporte or "").strip() or _url_soporte()
    html_bloque = _build_footer_hud_html(total, soporte)

    with st.container():
        st.markdown(html_bloque, unsafe_allow_html=True)

    st.caption(
        "© 2026 Σigma Tutor de Cálculo Integral · "
        "Métrica agregada por módulos de práctica y tutoría (sin contar heartbeats ni el panel Seguimos)."
    )
