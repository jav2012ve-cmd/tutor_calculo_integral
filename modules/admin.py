"""
Panel de administración (Plotly): estudiantes por universidad, peso por funcionalidad
y tabla de fugas del Quiz (heurística tras fallo).

Requiere Supabase (service_role) y columnas ``institucion`` / ``carrera`` en ``ia_logs``
(ver ``supabase_ia_logs_institucion_carrera.sql``).

Seguridad: si defines ``ADMIN_PANEL_PASSWORD`` en Secrets, debe desbloquearse en sesión
(misma clave que en ``admin_dashboard``).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

import streamlit as st

from modules import temario, uso_stats

try:
    import pandas as pd
    import plotly.express as px
except ImportError:  # pragma: no cover
    pd = None  # type: ignore
    px = None  # type: ignore


def _admin_desbloqueado() -> bool:
    try:
        pwd = str(st.secrets.get("ADMIN_PANEL_PASSWORD", "") or "").strip()
    except Exception:
        pwd = ""
    if not pwd:
        return True
    return bool(st.session_state.get("_admin_panel_unlocked"))


def _render_barrera_admin() -> bool:
    if not uso_stats.supabase_url_y_clave()[0]:
        st.error("Falta configuración de Supabase.")
        return False
    try:
        pwd_required = str(st.secrets.get("ADMIN_PANEL_PASSWORD", "") or "").strip()
    except Exception:
        pwd_required = ""
    if not pwd_required:
        st.warning(
            "Define **ADMIN_PANEL_PASSWORD** en Secrets para proteger este panel en producción."
        )
        return True
    if st.session_state.get("_admin_panel_unlocked"):
        return True
    st.markdown("### Acceso al panel admin")
    clave = st.text_input("Contraseña", type="password", key="admin_py_gate_pwd")
    if st.button("Desbloquear", key="admin_py_gate_btn"):
        if clave.strip() == pwd_required:
            st.session_state["_admin_panel_unlocked"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    return False


def _payload_dict(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            o = json.loads(raw)
            return o if isinstance(o, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _parse_ts(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    try:
        if isinstance(val, str):
            s = val.replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        if hasattr(val, "isoformat"):
            return val if isinstance(val, datetime) else None
    except (ValueError, TypeError):
        return None
    return None


def calcular_fugas_quiz_por_tema(
    rows_ev: list[dict[str, Any]],
    gap_abandono_segundos: float = 7200.0,
) -> "pd.DataFrame":
    """
    Heurística de «fuga»: tras un ``quiz_respuesta_incorrecta``, el siguiente evento del
    mismo estudiante no es Quiz, o el salto temporal supera ``gap_abandono_segundos``.
    """
    if pd is None or not rows_ev:
        return pd.DataFrame(columns=["tema", "fugas_estimadas"])

    filas: list[dict[str, Any]] = []
    for r in rows_ev:
        sid = r.get("estudiante_id")
        if sid is None or str(sid).strip() == "":
            continue
        pl = _payload_dict(r.get("payload"))
        modo = (r.get("modo") or "").strip()
        ts = _parse_ts(r.get("created_at"))
        filas.append(
            {
                "estudiante_id": str(sid).strip(),
                "created_at": r.get("created_at"),
                "_ts": ts,
                "modo": modo,
                "payload": pl,
            }
        )
    if not filas:
        return pd.DataFrame(columns=["tema", "fugas_estimadas"])

    df = pd.DataFrame(filas)
    df = df.sort_values(["estudiante_id", "_ts"], na_position="last")

    from collections import Counter

    fugas: Counter[str] = Counter()

    for sid, grp in df.groupby("estudiante_id"):
        seq = grp.reset_index(drop=True)
        n = len(seq)
        for i in range(n):
            row = seq.iloc[i]
            if row["modo"] != "Quiz":
                continue
            pl = _payload_dict(row.get("payload"))
            if pl.get("tipo_evento") != "quiz_respuesta_incorrecta":
                continue
            tema = temario.normalizar_tema_curso(pl.get("tema"))
            if not tema:
                continue
            t0 = row["_ts"]
            if i + 1 >= n:
                fugas[tema] += 1
                continue
            nxt = seq.iloc[i + 1]
            t1 = nxt["_ts"]
            salto = (
                (t1 - t0).total_seconds()
                if t0 is not None and t1 is not None and hasattr(t1 - t0, "total_seconds")
                else gap_abandono_segundos + 1.0
            )
            if (nxt["modo"] or "").strip() != "Quiz" or salto > gap_abandono_segundos:
                fugas[tema] += 1

    if not fugas:
        return pd.DataFrame(columns=["tema", "fugas_estimadas"])
    out = (
        pd.DataFrame([{"tema": t, "fugas_estimadas": c} for t, c in fugas.items()])
        .sort_values("fugas_estimadas", ascending=False)
        .reset_index(drop=True)
    )
    return out


def render_panel() -> None:
    """Vista principal del dashboard admin (Plotly)."""
    st.title("Panel de analítica (admin)")

    if pd is None or px is None:
        st.error("Instala **pandas** y **plotly**.")
        return

    if not _admin_desbloqueado():
        if not _render_barrera_admin():
            return

    rows_est = uso_stats.obtener_estudiantes_resumen_admin(limit=8000)
    rows_logs = uso_stats.obtener_todos_los_logs_ia(limit=8000)
    rows_ev = uso_stats.obtener_todos_los_eventos_uso(limit=15000)

    df_est = pd.DataFrame(rows_est) if rows_est else pd.DataFrame()
    df_logs = pd.DataFrame(rows_logs) if rows_logs else pd.DataFrame()
    df_ev = pd.DataFrame(rows_ev) if rows_ev else pd.DataFrame()

    if df_est.empty and df_logs.empty and df_ev.empty:
        st.info("Sin datos o sin acceso REST a las tablas.")
        return

    st.subheader("Estudiantes por universidad (perfil de registro)")
    if df_est.empty or "institucion" not in df_est.columns:
        st.caption("No hay filas en ``app_estudiante``.")
    else:
        uni = (
            df_est.groupby(df_est["institucion"].fillna("(sin dato)").astype(str))
            .size()
            .reset_index(name="n")
            .sort_values("n", ascending=False)
        )
        fig_bar = px.bar(
            uni.head(40),
            x="institucion",
            y="n",
            title="Inscritos por institución (texto en perfil)",
        )
        fig_bar.update_layout(xaxis_tickangle=-38, height=440)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Peso por funcionalidad (eventos de uso)")
    if df_ev.empty or "modo" not in df_ev.columns:
        st.caption("No hay eventos en ``app_usage_event``.")
    else:
        excl = {"session_heartbeat"}
        df_m = df_ev[~df_ev["modo"].isin(excl)].copy()
        if df_m.empty:
            st.caption("Solo hay heartbeats en la muestra.")
        else:
            agg = df_m.groupby("modo").size().reset_index(name="eventos")
            fig_tree = px.treemap(
                agg,
                path=["modo"],
                values="eventos",
                title="Volumen de eventos por modo (excluye session_heartbeat)",
            )
            st.plotly_chart(fig_tree, use_container_width=True)

    st.subheader("Fugas del Quiz tras fallo (estimación)")
    st.caption(
        "Por cada estudiante, orden cronológico: si tras un error de simulacro el siguiente evento "
        "no es Quiz o transcurre más de 2 h, cuenta como fuga para ese tema."
    )
    df_fugas = calcular_fugas_quiz_por_tema(rows_ev)
    if df_fugas.empty:
        st.caption("No se detectaron patrones de fuga con la muestra actual.")
    else:
        st.dataframe(df_fugas.head(60), use_container_width=True, hide_index=True)

    st.subheader("IA logs: institución / carrera (columnas en tabla)")
    if df_logs.empty:
        st.caption("Sin ``ia_logs`` en la muestra.")
    elif "institucion" in df_logs.columns:
        st.metric("Filas con institución distinta de Anónimo", int((df_logs["institucion"] != "Anónimo").sum()))
        st.dataframe(
            df_logs[["created_at", "institucion", "carrera", "modelo"]].head(25)
            if "carrera" in df_logs.columns
            else df_logs.head(25),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning(
            "Las columnas ``institucion`` / ``carrera`` no están en la respuesta: ejecuta "
            "``supabase_ia_logs_institucion_carrera.sql`` en Supabase."
        )
