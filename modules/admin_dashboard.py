"""
Panel de analítica para operadores (lectura vía Supabase service_role).

Uso: desde ``app.py`` o una app Streamlit aparte, llamar ``render_admin_panel()``.

``SESSION_KEY_MODO_ADMIN`` debe coincidir con la clave en ``app.py`` para el modo manual.

Seguridad: si defines en Secrets ``ADMIN_PANEL_PASSWORD`` (TOML), el panel exige esa clave
una vez por sesión antes de consultar datos. Sin secret, solo se exige Supabase configurado
(adecuado solo en entornos controlados).
"""

SESSION_KEY_MODO_ADMIN = "modo_administrador_manual"

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
        columns=[
            "id",
            "created_at",
            "estudiante_id",
            "pregunta",
            "respuesta",
            "modelo",
            "institucion",
            "carrera",
        ]
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
    total_consultas_ia = len(df_logs)
    prom_consultas_por_alumno = (
        round(total_consultas_ia / float(n_con_log_ia), 2) if n_con_log_ia else 0.0
    )

    st.markdown("##### Métricas clave")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total alumnos (registrados)", n_registrados)
    col2.metric("Consultas totales (IA, muestra)", total_consultas_ia)
    col3.metric("Promedio consultas IA / alumno con log", prom_consultas_por_alumno)

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Alumnos activos por universidad")
        st.caption(
            "Estudiantes distintos con al menos un log en la muestra, agrupados por **institución** "
            "(columna en `ia_logs` o cruce con perfil)."
        )
        df_pie_src = df_logs.copy()
        if "institucion" not in df_pie_src.columns or df_pie_src["institucion"].isna().all():
            df_pie_src = df_logs_enr.copy()
        if (
            df_pie_src.empty
            or "institucion" not in df_pie_src.columns
            or "estudiante_id" not in df_pie_src.columns
        ):
            st.caption("Sin datos para el gráfico de torta.")
        else:
            tmp = df_pie_src.dropna(subset=["estudiante_id"]).copy()
            tmp["_inst"] = tmp["institucion"].fillna("(sin dato)").astype(str)
            pie_df = tmp.groupby("_inst", as_index=False)["estudiante_id"].nunique()
            pie_df = pie_df.rename(columns={"_inst": "institucion", "estudiante_id": "alumnos_activos"})
            pie_df = pie_df[pie_df["alumnos_activos"] > 0]
            if pie_df.empty:
                st.caption("Sin alumnos con `estudiante_id` e institución en la muestra.")
            else:
                fig_uni = px.pie(
                    pie_df,
                    names="institucion",
                    values="alumnos_activos",
                    hole=0.4,
                    title="Alumnos activos por universidad (cuenta única por institución)",
                )
                st.plotly_chart(fig_uni, use_container_width=True)

    with c2:
        st.subheader("Top 10 de temas fallidos (marketing)")
        st.caption("Basado en eventos **quiz_respuesta_incorrecta** en la muestra de uso.")
        df_fallas = _extraer_fallas_quiz(df_eventos)
        if df_fallas.empty:
            st.caption("No hay fallos de simulacro con tema válido en la muestra.")
        else:
            top10 = df_fallas.head(10).copy()
            top10["rank"] = range(1, len(top10) + 1)
            st.dataframe(
                top10[["rank", "tema", "fallas"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "rank": st.column_config.NumberColumn("#", format="%d"),
                    "tema": st.column_config.TextColumn("Tema del temario"),
                    "fallas": st.column_config.NumberColumn("Errores registrados", format="%d"),
                },
            )
            fig_fallas = px.bar(
                top10,
                x="tema",
                y="fallas",
                title="Top 10 — volumen de errores en Simulacro",
            )
            fig_fallas.update_layout(xaxis_tickangle=-42, height=380)
            st.plotly_chart(fig_fallas, use_container_width=True)

    st.divider()
    st.markdown("##### Detalle complementario")
    modo_top = "—"
    if not df_eventos.empty and "modo" in df_eventos.columns:
        m = df_eventos["modo"].mode(dropna=True)
        if len(m) > 0:
            modo_top = str(m.iloc[0])
    c4, c5, c6 = st.columns(3)
    c4.metric("Estudiantes con ≥1 log IA", n_con_log_ia)
    c5.metric("Filas en app_usage_event (muestra)", len(df_eventos))
    c6.metric("Modo más frecuente (eventos)", modo_top)

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

    st.divider()
    if st.button("Volver a la aplicación", type="primary", key="admin_volver_sigma_app"):
        st.session_state[SESSION_KEY_MODO_ADMIN] = False
        st.rerun()
