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

# Listados: por encima de esto se sugiere usar la pestaña «Por universidad».
_MAX_FILAS_LISTA_ESTUDIANTE = 120

_ADMIN_PLOT_LAYOUT = dict(
    font=dict(size=13, color="#0f172a"),
    title_font=dict(size=15, color="#0f172a"),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f8fafc",
)


def _admin_inject_readability_styles() -> None:
    """Mejora contraste y tamaño de captions, tablas y celdas del panel (Streamlit usa grises muy claros por defecto)."""
    st.markdown(
        """
        <style>
        section.main [data-testid="stCaption"] {
            color: #1e293b !important;
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
        }
        section.main [data-testid="stMarkdownContainer"] p {
            color: #1e293b;
        }
        section.main div[data-testid="stDataFrame"] div {
            font-size: 0.88rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _fig_apply_admin_theme(fig: Any) -> Any:
    if fig is None:
        return None
    fig.update_layout(**_ADMIN_PLOT_LAYOUT)
    return fig


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


def _build_actividad_estudiantes(
    df_est: "pd.DataFrame",
    df_eventos: "pd.DataFrame",
    df_logs: "pd.DataFrame",
) -> tuple["pd.DataFrame", "pd.DataFrame"]:
    """
    Devuelve (detalle_por_estudiante, resumen_por_universidad).
    Incluye universidad, primera/última actividad en la muestra REST, eventos por modo y consultas IA.
    """
    if df_est.empty or "id" not in df_est.columns:
        vac = pd.DataFrame()
        return vac, vac

    base = df_est.copy()
    base["sid"] = base["id"].astype(str).str.strip()

    primera_e = ultima_e = n_ev = None
    modo_wide = pd.DataFrame()
    if not df_eventos.empty and "estudiante_id" in df_eventos.columns and "created_at" in df_eventos.columns:
        ev = df_eventos.dropna(subset=["estudiante_id"]).copy()
        ev["sid"] = ev["estudiante_id"].astype(str).str.strip()
        gb = ev.groupby("sid")["created_at"]
        primera_e = gb.min().rename("primera_ev")
        ultima_e = gb.max().rename("ultima_ev")
        n_ev = gb.count().rename("n_eventos_app")
        if "modo" in ev.columns:
            modo_wide = pd.crosstab(ev["sid"], ev["modo"])

    primera_l = ultima_l = n_ia = None
    if not df_logs.empty and "estudiante_id" in df_logs.columns and "created_at" in df_logs.columns:
        lg = df_logs.dropna(subset=["estudiante_id"]).copy()
        lg["sid"] = lg["estudiante_id"].astype(str).str.strip()
        gb2 = lg.groupby("sid")["created_at"]
        primera_l = gb2.min().rename("primera_ia")
        ultima_l = gb2.max().rename("ultima_ia")
        n_ia = gb2.count().rename("n_consultas_ia")

    df = base.set_index("sid", drop=True)
    for part in (primera_e, ultima_e, n_ev):
        if part is not None:
            df = df.join(part, how="left")
    for part in (primera_l, ultima_l, n_ia):
        if part is not None:
            df = df.join(part, how="left")
    if not modo_wide.empty:
        df = df.join(modo_wide, how="left")

    cols_min = [c for c in ("primera_ev", "primera_ia") if c in df.columns]
    cols_max = [c for c in ("ultima_ev", "ultima_ia") if c in df.columns]
    if cols_min:
        df["primera_actividad_utc"] = pd.to_datetime(df[cols_min].min(axis=1), utc=True, errors="coerce")
    else:
        df["primera_actividad_utc"] = pd.NaT
    if cols_max:
        df["ultima_actividad_utc"] = pd.to_datetime(df[cols_max].max(axis=1), utc=True, errors="coerce")
    else:
        df["ultima_actividad_utc"] = pd.NaT

    df["n_eventos_app"] = df["n_eventos_app"].fillna(0).astype(int) if "n_eventos_app" in df.columns else 0
    df["n_consultas_ia"] = df["n_consultas_ia"].fillna(0).astype(int) if "n_consultas_ia" in df.columns else 0

    reservados = {
        "sid",
        "id",
        "institucion",
        "nombre",
        "email",
        "created_at",
        "primera_ev",
        "ultima_ev",
        "primera_ia",
        "ultima_ia",
        "n_eventos_app",
        "n_consultas_ia",
        "primera_actividad_utc",
        "ultima_actividad_utc",
    }
    modo_cols = [c for c in df.columns if c not in reservados]

    def _resumen_modos(row: "pd.Series") -> str:
        partes: list[tuple[str, int]] = []
        for c in modo_cols:
            try:
                v = int(float(row.get(c, 0) or 0))
            except (TypeError, ValueError):
                v = 0
            if v > 0:
                partes.append((c, v))
        partes.sort(key=lambda t: -t[1])
        return " · ".join(f"{a}: {b}" for a, b in partes[:12]) if partes else "—"

    df["eventos_por_modo"] = df.apply(_resumen_modos, axis=1)

    df["Universidad"] = (
        df["institucion"].fillna("").astype(str).str.strip().replace("", "(sin dato)")
        if "institucion" in df.columns
        else "(sin dato)"
    )

    _span = (df["ultima_actividad_utc"] - df["primera_actividad_utc"]).dt.total_seconds() / 3600.0
    df["ventana_muestra_horas"] = pd.to_numeric(_span, errors="coerce").round(2)

    vista = pd.DataFrame(
        {
            "sid": df.index.astype(str),
            "Nombre": df["nombre"] if "nombre" in df.columns else "",
            "Correo": df["email"] if "email" in df.columns else "",
            "Universidad": df["Universidad"],
            "Primera actividad (UTC)": df["primera_actividad_utc"],
            "Última actividad (UTC)": df["ultima_actividad_utc"],
            "Horas entre 1ª y última (muestra)": df["ventana_muestra_horas"],
            "Eventos app": df["n_eventos_app"],
            "Consultas IA": df["n_consultas_ia"],
            "Uso por modo (conteo)": df["eventos_por_modo"],
        }
    )
    vista = vista.sort_values("Última actividad (UTC)", ascending=False, na_position="last")
    vista = vista.reset_index(drop=True)

    agg_num = (
        vista.drop(columns=["sid"], errors="ignore")
        .groupby("Universidad", as_index=False)
        .agg(
            estudiantes=("Nombre", "count"),
            media_eventos_app=("Eventos app", "mean"),
            media_consultas_ia=("Consultas IA", "mean"),
            media_horas_ventana=("Horas entre 1ª y última (muestra)", "mean"),
            mediana_eventos_app=("Eventos app", "median"),
            mediana_consultas_ia=("Consultas IA", "median"),
        )
    )
    for col in (
        "media_eventos_app",
        "media_consultas_ia",
        "media_horas_ventana",
        "mediana_eventos_app",
        "mediana_consultas_ia",
    ):
        if col in agg_num.columns:
            agg_num[col] = agg_num[col].round(2)

    return vista, agg_num


def _render_listado_estudiantes_admin(vista: "pd.DataFrame", agg_num: "pd.DataFrame") -> None:
    st.divider()
    st.markdown("### Participantes y uso por funcionalidad")
    st.markdown(
        "<p style='color:#334155;font-size:1.02rem;line-height:1.55;margin:0.35rem 0 0.75rem 0;'>"
        "Universidad de procedencia (<code>app_estudiante.institucion</code>), "
        "<strong>primera y última actividad</strong> en la muestra actual (unión de "
        "<code>app_usage_event</code> e <code>ia_logs</code>, UTC), "
        "<strong>eventos de app por modo</strong> y <strong>consultas IA</strong> registradas.</p>",
        unsafe_allow_html=True,
    )
    if vista.empty:
        st.info(
            "No hay filas en **app_estudiante** en esta muestra. Cuando existan inscritos, aquí verás el listado."
        )
        return

    n = len(vista)
    if n > _MAX_FILAS_LISTA_ESTUDIANTE:
        st.info(
            f"Hay **{n}** participantes en la muestra. La tabla **Por estudiante** muestra como máximo "
            f"**{_MAX_FILAS_LISTA_ESTUDIANTE}** filas (prioridad: última actividad reciente). "
            "Usa **Por universidad** para promedios de todo el conjunto o exporta desde Supabase para el detalle completo."
        )

    tab_est, tab_uni = st.tabs(["Por estudiante", "Por universidad (promedios)"])

    with tab_est:
        disp = vista.head(_MAX_FILAS_LISTA_ESTUDIANTE).drop(columns=["sid"], errors="ignore")
        col_cfg: dict[str, Any] = {
            "Uso por modo (conteo)": st.column_config.TextColumn(
                "Uso por modo (conteo)",
                width="large",
            ),
        }
        try:
            col_cfg["Primera actividad (UTC)"] = st.column_config.DatetimeColumn(
                "Primera actividad (UTC)",
                format="YYYY-MM-DD HH:mm",
            )
            col_cfg["Última actividad (UTC)"] = st.column_config.DatetimeColumn(
                "Última actividad (UTC)",
                format="YYYY-MM-DD HH:mm",
            )
        except Exception:
            pass
        st.dataframe(
            disp,
            use_container_width=True,
            hide_index=True,
            column_config=col_cfg,
        )

    with tab_uni:
        if agg_num.empty:
            st.info("No hay datos para agrupar por universidad.")
        else:
            st.markdown(
                "<p style='color:#334155;font-size:1rem;'>Promedios y medianas por texto de "
                "<strong>institución</strong> (incluye «sin dato»).</p>",
                unsafe_allow_html=True,
            )
            st.dataframe(
                agg_num.sort_values("estudiantes", ascending=False),
                use_container_width=True,
                hide_index=True,
            )


def render_admin_panel() -> None:
    st.title("Panel de analítica estratégica")
    _admin_inject_readability_styles()

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

    vista_est, agg_uni = _build_actividad_estudiantes(df_est, df_eventos, df_logs)
    _render_listado_estudiantes_admin(vista_est, agg_uni)

    st.divider()
    st.markdown("### Distribución de estudiantes por universidad")
    st.caption(
        "Inscritos en `app_estudiante` por campo **institucion** (UCV, USB, UNIMET, etc.). "
        "«Sin dato» agrupa vacíos u omisión."
    )
    if df_est.empty or "institucion" not in df_est.columns or "id" not in df_est.columns:
        st.info("Sin datos de estudiantes para la torta.", icon="ℹ️")
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
            st.info("Sin filas válidas para agrupar.", icon="ℹ️")
        else:
            fig_uni = px.pie(
                pie_df,
                names="institucion",
                values="estudiantes",
                hole=0.38,
                title="Estudiantes registrados por institución",
            )
            fig_uni.update_traces(textposition="inside", textinfo="percent+label")
            _fig_apply_admin_theme(fig_uni)
            st.plotly_chart(fig_uni, use_container_width=True)

    st.divider()
    st.markdown("### Análisis de fallas")
    st.caption("Los **5 temas** con más eventos ``quiz_respuesta_incorrecta`` en la muestra de uso.")
    df_fallas = _extraer_fallas_quiz(df_eventos)
    if df_fallas.empty:
        st.info(
            "No hay fallos de simulacro con tema válido en la muestra "
            "(no aparecen eventos `quiz_respuesta_incorrecta` con tema reconocible).",
            icon="ℹ️",
        )
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
        _fig_apply_admin_theme(fig_fallas)
        st.plotly_chart(fig_fallas, use_container_width=True)

    st.divider()
    st.markdown("### Permanencia")
    st.caption(
        "Histogramas desde **app_usage_event** (UTC): volumen por **hora** y por **día del calendario** "
        "para ventanas de notificaciones o promos."
    )
    if df_eventos.empty or "created_at" not in df_eventos.columns:
        st.info(
            "Sin eventos con marca de tiempo en la muestra (**app_usage_event** vacía o sin columna "
            "`created_at` legible).",
            icon="ℹ️",
        )
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
            _fig_apply_admin_theme(fig_hora)
            st.plotly_chart(fig_hora, use_container_width=True)

        with h2:
            ev_dia = df_eventos.assign(_fecha=ts_ev.dt.date).dropna(subset=["_fecha"])
            if ev_dia.empty:
                st.info("No hay fechas válidas para el histograma diario.", icon="ℹ️")
            else:
                fig_dia = px.histogram(
                    ev_dia,
                    x="_fecha",
                    title="Actividad por día (UTC)",
                    labels={"_fecha": "Fecha", "count": "Eventos"},
                )
                fig_dia.update_layout(bargap=0.04, height=360)
                _fig_apply_admin_theme(fig_dia)
                st.plotly_chart(fig_dia, use_container_width=True)

    st.divider()
    with st.expander("Vista previa de datos (muestra corta)", expanded=False):
        st.markdown(
            "<p style='color:#334155;font-size:1rem;line-height:1.5;'>Primeras filas descargadas por REST "
            "(texto oscuro para mejor lectura).</p>",
            unsafe_allow_html=True,
        )
        st.markdown("**ia_logs**")
        st.dataframe(df_logs.head(12), use_container_width=True, hide_index=True, height=320)
        st.markdown("**app_usage_event**")
        st.dataframe(df_eventos.head(12), use_container_width=True, hide_index=True, height=320)

    st.divider()
    if st.button("Volver a la aplicación", type="primary", key="admin_volver_sigma_app"):
        st.session_state[SESSION_KEY_MODO_ADMIN] = False
        st.rerun()
