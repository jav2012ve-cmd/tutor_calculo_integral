"""
Panel de analítica para operadores (lectura vía Supabase service_role).

Uso: desde ``app.py`` o una app Streamlit aparte, llamar ``render_admin_panel()``.

Seguridad: si defines en Secrets ``ADMIN_PANEL_PASSWORD`` (TOML), el panel exige esa clave
una vez por sesión antes de consultar datos. Sin secret, solo se exige Supabase configurado
(adecuado solo en entornos controlados).
"""

from __future__ import annotations

import json
from typing import Any, Optional

import streamlit as st

from modules import temario, uso_stats

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore

try:
    import plotly.express as px
except ImportError:  # pragma: no cover
    px = None  # type: ignore


def _payload_a_dict(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            o = json.loads(raw)
            return o if isinstance(o, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _admin_desbloqueado() -> bool:
    try:
        pwd = str(st.secrets.get("ADMIN_PANEL_PASSWORD", "") or "").strip()
    except Exception:
        pwd = ""
    if not pwd:
        return True
    return bool(st.session_state.get("_admin_panel_unlocked"))


def _render_barrera_acceso_admin() -> bool:
    """Devuelve True si se puede mostrar el panel."""
    try:
        pwd_required = str(st.secrets.get("ADMIN_PANEL_PASSWORD", "") or "").strip()
    except Exception:
        pwd_required = ""

    if not pwd_required:
        st.warning(
            "⚠️ **ADMIN_PANEL_PASSWORD** no está definido en Secrets: cualquiera con acceso a la URL "
            "podría ver métricas agregadas. Define la clave en producción."
        )
        return True

    if st.session_state.get("_admin_panel_unlocked"):
        return True

    st.markdown("### Acceso al panel de administración")
    clave = st.text_input("Contraseña del panel", type="password", key="admin_pwd_gate")
    if st.button("Desbloquear", type="primary", key="admin_pwd_btn"):
        if clave.strip() == pwd_required:
            st.session_state["_admin_panel_unlocked"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    return False


def _enriquecer_logs_con_institucion(df_logs: "pd.DataFrame", df_est: "pd.DataFrame") -> "pd.DataFrame":
    if df_logs.empty or df_est.empty or "estudiante_id" not in df_logs.columns:
        if not df_logs.empty and "institucion" not in df_logs.columns:
            df_logs = df_logs.copy()
            df_logs["institucion"] = "(sin perfil)"
        return df_logs
    est = df_est.rename(columns={"id": "estudiante_id"})[["estudiante_id", "institucion"]].drop_duplicates(
        subset=["estudiante_id"]
    )
    out = df_logs.merge(est, on="estudiante_id", how="left")
    out["institucion"] = out["institucion"].fillna("(sin institución en perfil)")
    return out


def _extraer_fallas_quiz(df_ev: "pd.DataFrame") -> "pd.DataFrame":
    if df_ev.empty or "payload" not in df_ev.columns:
        return pd.DataFrame(columns=["tema"]) if pd is not None else df_ev

    temas: list[str] = []
    for _, row in df_ev.iterrows():
        pl = _payload_a_dict(row.get("payload"))
        if pl.get("tipo_evento") != "quiz_respuesta_incorrecta":
            continue
        t = temario.normalizar_tema_curso(pl.get("tema"))
        if t:
            temas.append(t)
    if not temas:
        return pd.DataFrame(columns=["tema"])
    vc = pd.Series(temas).value_counts().reset_index()
    vc.columns = ["tema", "fallas"]
    return vc


def render_admin_panel() -> None:
    st.title("Panel de analítica estratégica")

    if pd is None or px is None:
        st.error("Instala **pandas** y **plotly** (`pip install -r requirements.txt`).")
        return

    if not uso_stats.supabase_url_y_clave()[0]:
        st.error("Falta **SUPABASE_URL** (y clave) en Secrets o entorno.")
        return

    if not _admin_desbloqueado():
        if not _render_barrera_acceso_admin():
            return

    rows_logs = uso_stats.obtener_todos_los_logs_ia(limit=8000)
    rows_ev = uso_stats.obtener_todos_los_eventos_uso(limit=15000)
    rows_est = uso_stats.obtener_estudiantes_resumen_admin(limit=8000)

    df_logs = pd.DataFrame(rows_logs) if rows_logs else pd.DataFrame(
        columns=["id", "created_at", "estudiante_id", "pregunta", "respuesta", "modelo"]
    )
    df_eventos = pd.DataFrame(rows_ev) if rows_ev else pd.DataFrame(
        columns=["id", "created_at", "modo", "payload", "estudiante_id"]
    )
    df_est = pd.DataFrame(rows_est) if rows_est else pd.DataFrame(
        columns=["id", "institucion", "nombre", "email", "created_at"]
    )

    if df_logs.empty and df_eventos.empty and df_est.empty:
        st.info("No hay filas en las tablas consultadas o la lectura REST falló (revisa permisos **service_role**).")
        return

    df_logs_enr = _enriquecer_logs_con_institucion(df_logs, df_est)

    n_registrados = int(df_est["id"].nunique()) if not df_est.empty and "id" in df_est.columns else 0
    ids_logs = (
        df_logs["estudiante_id"].dropna().astype(str).str.strip().unique()
        if not df_logs.empty and "estudiante_id" in df_logs.columns
        else []
    )
    n_con_log_ia = len([x for x in ids_logs if x])

    modo_top = "—"
    if not df_eventos.empty and "modo" in df_eventos.columns:
        m = df_eventos["modo"].mode(dropna=True)
        if len(m) > 0:
            modo_top = str(m.iloc[0])

    col1, col2, col3 = st.columns(3)
    col1.metric("Estudiantes registrados", n_registrados)
    col2.metric("Filas en ia_logs (muestra)", len(df_logs))
    col3.metric("Modo más frecuente (eventos)", modo_top)

    col4, col5, col6 = st.columns(3)
    col4.metric("Estudiantes con ≥1 log IA", n_con_log_ia)
    col5.metric("Filas en app_usage_event (muestra)", len(df_eventos))
    col6.metric("Instituciones distintas (perfil)", int(df_est["institucion"].nunique()) if not df_est.empty and "institucion" in df_est.columns else 0)

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Distribución por institución (logs IA con perfil)")
        if df_logs_enr.empty or "institucion" not in df_logs_enr.columns:
            st.caption("Sin datos para el gráfico.")
        else:
            pie_df = df_logs_enr[df_logs_enr["institucion"].notna()].copy()
            if pie_df.empty:
                st.caption("Sin institución enlazada en los logs.")
            else:
                fig_uni = px.pie(
                    pie_df,
                    names="institucion",
                    hole=0.4,
                    title="Proporción de interacciones IA por institución del estudiante",
                )
                st.plotly_chart(fig_uni, use_container_width=True)

    with c2:
        st.subheader("Temas con más fallas en Simulacro (muestra)")
        df_fallas = _extraer_fallas_quiz(df_eventos)
        if df_fallas.empty:
            st.caption("No hay eventos `quiz_respuesta_incorrecta` con tema válido en la muestra.")
        else:
            fig_fallas = px.bar(
                df_fallas.head(25),
                x="tema",
                y="fallas",
                title="Errores de quiz por tema (conteo en muestra)",
            )
            fig_fallas.update_layout(xaxis_tickangle=-42, height=420)
            st.plotly_chart(fig_fallas, use_container_width=True)

    st.subheader("Actividad temporal (logs IA)")
    if df_logs.empty or "created_at" not in df_logs.columns:
        st.caption("Sin fechas en ia_logs.")
    else:
        ts = pd.to_datetime(df_logs["created_at"], utc=True, errors="coerce")
        df_logs = df_logs.copy()
        df_logs["_fecha"] = ts.dt.date
        serie = df_logs.dropna(subset=["_fecha"]).groupby("_fecha").size().reset_index(name="consultas")
        serie = serie.rename(columns={"_fecha": "fecha"})
        if serie.empty:
            st.caption("No se pudo agrupar por fecha.")
        else:
            fig_linea = px.line(serie, x="fecha", y="consultas", markers=True, title="Consultas IA por día (UTC)")
            st.plotly_chart(fig_linea, use_container_width=True)

    with st.expander("Vista previa de datos (muestra corta)", expanded=False):
        st.caption("ia_logs")
        st.dataframe(df_logs.head(12), use_container_width=True, hide_index=True)
        st.caption("app_usage_event")
        st.dataframe(df_eventos.head(12), use_container_width=True, hide_index=True)
