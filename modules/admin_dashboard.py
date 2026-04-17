"""Panel de analítica (Supabase service_role): ``render_admin_panel()`` desde ``app``.

Requiere ``uso_stats`` y ``plotly.express`` (``px``). Opcional: ``ADMIN_PANEL_PASSWORD`` en Secrets.
"""

import json
from typing import Any

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

SESSION_KEY_MODO_ADMIN = "modo_administrador_manual"


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

    n_registrados = int(df_est["id"].nunique()) if not df_est.empty and "id" in df_est.columns else 0
    total_consultas_ia = len(df_logs)
    n_con_log_ia = 0
    if not df_logs.empty and "estudiante_id" in df_logs.columns:
        sid = df_logs["estudiante_id"].dropna().astype(str).str.strip()
        n_con_log_ia = int(sid[sid != ""].nunique())

    prom_consultas_por_alumno_ia = (
        round(total_consultas_ia / float(n_con_log_ia), 2) if n_con_log_ia else 0.0
    )

    ev_con_usuario = pd.DataFrame()
    if not df_eventos.empty and "estudiante_id" in df_eventos.columns:
        ev_con_usuario = df_eventos.dropna(subset=["estudiante_id"]).copy()
    n_unicos_con_eventos = 0
    if not ev_con_usuario.empty:
        n_unicos_con_eventos = ev_con_usuario["estudiante_id"].astype(str).str.strip().nunique()
    prom_eventos_por_usuario_activo = (
        round(len(ev_con_usuario) / float(n_unicos_con_eventos), 2) if n_unicos_con_eventos else 0.0
    )

    prom_consultas_por_registrado = (
        round(total_consultas_ia / float(n_registrados), 3) if n_registrados else 0.0
    )

    st.markdown("### Métricas gruesas")
    st.caption("Totales en la **muestra** descargada (límites REST en `uso_stats`).")
    col1, col2, col3 = st.columns(3)
    col1.metric("Estudiantes totales", n_registrados)
    col2.metric("Consultas totales (IA)", total_consultas_ia)
    col3.metric(
        "Promedio de uso por usuario",
        prom_consultas_por_registrado,
        help="Consultas IA en muestra / estudiantes registrados en muestra (incluye inactivos con 0).",
    )
    st.caption(
        f"Detalle: **{prom_consultas_por_alumno_ia}** consultas IA de media por alumno con log identificado "
        f"({n_con_log_ia} usuarios); **{prom_eventos_por_usuario_activo}** eventos de app por usuario con actividad "
        f"en la muestra ({n_unicos_con_eventos} usuarios distintos en `app_usage_event`)."
    )

    st.divider()
    st.markdown("### Distribución de estudiantes por universidad")
    st.caption(
        "Inscritos en `app_estudiante` por campo **institucion** (UCV, USB, UNIMET, etc.). "
        "«Sin dato» agrupa vacíos u omisión."
    )
    if df_est.empty or "institucion" not in df_est.columns or "id" not in df_est.columns:
        st.caption("Sin datos de estudiantes para la torta.")
    else:
        pie_src = df_est.copy()
        pie_src["_inst"] = (
            pie_src["institucion"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("", "(sin dato)")
        )
        pie_df = pie_src.groupby("_inst", as_index=False)["id"].nunique()
        pie_df = pie_df.rename(columns={"_inst": "institucion", "id": "estudiantes"})
        pie_df = pie_df[pie_df["estudiantes"] > 0].sort_values("estudiantes", ascending=False)
        if pie_df.empty:
            st.caption("Sin filas válidas para agrupar.")
        else:
            fig_uni = px.pie(
                pie_df,
                names="institucion",
                values="estudiantes",
                hole=0.38,
                title="Estudiantes registrados por institución",
            )
            fig_uni.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_uni, use_container_width=True)

    st.divider()
    st.markdown("### Análisis de fallas")
    st.caption("Los **5 temas** con más eventos ``quiz_respuesta_incorrecta`` en la muestra de uso.")
    df_fallas = _extraer_fallas_quiz(df_eventos)
    if df_fallas.empty:
        st.caption("No hay fallos de simulacro con tema válido en la muestra.")
    else:
        top5 = df_fallas.head(5).copy()
        fig_fallas = px.bar(
            top5,
            x="tema",
            y="fallas",
            title="Top 5 temas — respuestas incorrectas en Quiz",
            color="fallas",
            color_continuous_scale="Reds",
        )
        fig_fallas.update_layout(
            xaxis_tickangle=-36,
            height=400,
            showlegend=False,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_fallas, use_container_width=True)

    st.divider()
    st.markdown("### Permanencia")
    st.caption(
        "Histogramas desde **app_usage_event** (UTC): volumen por **hora** y por **día del calendario** "
        "para ventanas de notificaciones o promos."
    )
    if df_eventos.empty or "created_at" not in df_eventos.columns:
        st.caption("Sin eventos con marca de tiempo en la muestra.")
    else:
        ts_ev = pd.to_datetime(df_eventos["created_at"], utc=True, errors="coerce")
        ev2 = df_eventos.assign(_hora=ts_ev.dt.hour, _fecha=ts_ev.dt.date)
        ev2 = ev2.dropna(subset=["_hora"])

        h1, h2 = st.columns(2)
        with h1:
            hora_serie = ev2["_hora"].astype(int).value_counts().reindex(range(24), fill_value=0)
            hora_df = hora_serie.reset_index()
            hora_df.columns = ["hora", "eventos"]
            fig_hora = px.bar(
                hora_df,
                x="hora",
                y="eventos",
                title="Actividad por hora del día (UTC)",
                labels={"hora": "Hora (0–23)", "eventos": "Eventos"},
            )
            fig_hora.update_layout(bargap=0.12, height=360, xaxis=dict(dtick=1, range=[-0.5, 23.5]))
            st.plotly_chart(fig_hora, use_container_width=True)

        with h2:
            ev_dia = df_eventos.assign(_fecha=ts_ev.dt.date).dropna(subset=["_fecha"])
            if ev_dia.empty:
                st.caption("No hay fechas válidas para histograma diario.")
            else:
                fig_dia = px.histogram(
                    ev_dia,
                    x="_fecha",
                    title="Actividad por día (UTC)",
                    labels={"_fecha": "Fecha", "count": "Eventos"},
                )
                fig_dia.update_layout(bargap=0.04, height=360)
                st.plotly_chart(fig_dia, use_container_width=True)

    st.divider()
    with st.expander("Vista previa de datos (muestra corta)", expanded=False):
        st.caption("ia_logs")
        st.dataframe(df_logs.head(12), use_container_width=True, hide_index=True)
        st.caption("app_usage_event")
        st.dataframe(df_eventos.head(12), use_container_width=True, hide_index=True)

    st.divider()
    if st.button("Volver a la aplicación", type="primary", key="admin_volver_sigma_app"):
        st.session_state[SESSION_KEY_MODO_ADMIN] = False
        st.rerun()
