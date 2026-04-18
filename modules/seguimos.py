"""
Panel «Seguimos»: continuidad para estudiantes identificados.

Flujo con Supabase: entrada → portal de registro / login → panel.
Sin Supabase: se puede ir al panel con identificación solo de sesión.
"""

from __future__ import annotations

import base64
import html
import io
from urllib.parse import quote

import streamlit as st
from PIL import Image

from modules import auth_estudiantes, temario, uso_stats

MODO_ID = "0) Seguimos (continuidad)"

SEGUIMOS_PASO_ENTRADA = "entrada"
SEGUIMOS_PASO_PORTAL = "portal"
SEGUIMOS_PASO_PANEL = "panel"

# Mismo id que en ``interfaz.MODO_PLANES_ESTUDIO_OFICIALES`` (evitar import circular).
MODO_PLANES_OFICIALES_ID = "f) Planes de Estudio Oficiales"

_ACCESO_RAPIDO_MODOS: tuple[tuple[str, str], ...] = (
    ("a) Entrenamiento (Temario)", "A practicar"),
    ("b) Respuesta Guiada (Consultas)", "Vamos paso a paso"),
    ("c) Autoevaluación (Quiz)", "Simulacro"),
    ("d) Tutor: Preguntas Abiertas", "Dime y te digo"),
    ("e) Corrección de Manuscritos", "Te lo reviso"),
    (MODO_PLANES_OFICIALES_ID, "Planes de estudio oficiales"),
)


def modo_id_valido_acceso_rapido(mid: str) -> bool:
    """``mid`` coincide con un modo de la cuadrícula de acceso rápido."""
    return any(m == mid for m, _ in _ACCESO_RAPIDO_MODOS)


def aplicar_apertura_modo_desde_query_param() -> None:
    """Si la URL trae ``?abrir_modo=…``, abre ese modo y limpia el parámetro (enlace desde teselas)."""
    try:
        qp = st.query_params
        raw = qp.get("abrir_modo")
        if raw is None:
            return
        mid = raw[0] if isinstance(raw, list) else str(raw)
        from urllib.parse import unquote_plus

        mid = unquote_plus(mid)
        if not modo_id_valido_acceso_rapido(mid):
            if "abrir_modo" in qp:
                del qp["abrir_modo"]
            return
        st.session_state.modo_actual = mid
        st.session_state.pop("seguimos_paso", None)
        _limpiar_estado_al_salir_de_seguimos()
        if "abrir_modo" in qp:
            del qp["abrir_modo"]
        st.rerun()
    except Exception:
        pass


def _tile_acceso_rapido_data_uri(mid: str) -> str | None:
    from modules import interfaz as _ix

    pil = _ix.preview_imagen_modo_recorte_superior(mid, fraccion_altura=0.15)
    if pil is None:
        pth = _ix.ruta_imagen_modo(mid)
        if not pth:
            return None
        with Image.open(pth) as im:
            pil = im.copy()
        w, h = pil.size
        if h > 2:
            pil = pil.crop((0, 0, w, max(1, int(h * 0.15))))
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _limpiar_estado_al_salir_de_seguimos() -> None:
    """Alineado a ``interfaz._aplicar_iniciar_modo`` al abrir otro modo desde el panel."""
    st.session_state.quiz_activo = False
    st.session_state.preguntas_quiz = []
    st.session_state.indice_pregunta = 0
    st.session_state.respuestas_usuario = []
    if "trigger_quiz" in st.session_state:
        st.session_state.trigger_quiz = False
    st.session_state.entrenamiento_activo = False
    st.session_state.consulta_step = 0
    st.session_state.consulta_data = None
    st.session_state.consulta_validada = False
    st.session_state.historial_tutor_abierto = []
    st.session_state.manuscrito_correccion = None


def _navegar_a_modo_desde_seguimos(modo_id: str) -> None:
    st.session_state.modo_actual = modo_id
    st.session_state.pop("seguimos_paso", None)
    _limpiar_estado_al_salir_de_seguimos()
    st.rerun()


def _render_botones_acceso_rapido_modos() -> None:
    if not auth_estudiantes.sesion_activa():
        return
    from modules import interfaz as _ix

    st.markdown("##### Acceso rápido a los modos de estudio")
    for fila_ini in range(0, len(_ACCESO_RAPIDO_MODOS), 3):
        chunk = _ACCESO_RAPIDO_MODOS[fila_ini : fila_ini + 3]
        cols = st.columns(len(chunk))
        for j, (mid, etiqueta) in enumerate(chunk):
            with cols[j]:
                _, ayuda = _ix.meta_modo(mid)
                data_uri = _tile_acceso_rapido_data_uri(mid)
                qmid = quote(mid, safe="")
                title_attr = html.escape(ayuda or etiqueta)
                if data_uri:
                    st.markdown(
                        f'<a href="?abrir_modo={qmid}" title="{title_attr}" '
                        'style="display:block;text-decoration:none;">'
                        f'<img src="{data_uri}" alt="{html.escape(etiqueta)}" '
                        'style="width:100%;border-radius:10px;border:1px solid #e2e8f0;"/></a>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Sin imagen")
                st.caption(etiqueta)


def _render_tab_record_comparativa() -> None:
    st.markdown("##### Mi récord frente a otros inscritos")
    st.caption(
        "Comparativa a partir de **eventos de uso** en la base (cada acción registrada con tu sesión). "
        "El grupo «tu universidad» usa el texto de **institución** de tu perfil, normalizado."
    )
    if not auth_estudiantes.sesion_activa() or not _supabase_configurado():
        st.info("Inicia sesión con Supabase activo para ver la comparativa con otros participantes.")
        return
    sid = st.session_state.get("auth_estudiante_id")
    if not sid:
        return
    inst = (st.session_state.get("auth_estudiante_institucion") or "").strip()
    cmp = uso_stats.obtener_comparativa_practica_estudiante(str(sid), inst or None)
    if cmp is None:
        st.warning(
            "No se pudo cargar la comparativa (tablas `app_estudiante` / `app_usage_event` o permisos REST)."
        )
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Tus eventos registrados", cmp["mi_eventos"])
    with c2:
        st.metric("Promedio en tu institución", cmp["promedio_eventos_misma_institucion"])
    with c3:
        st.metric("Promedio global (todos)", cmp["promedio_eventos_global"])

    st.markdown("**Base del cálculo**")
    st.caption(
        f"Inscritos con la misma institución (texto coincidente): **{cmp['n_inscritos_misma_institucion']}** · "
        f"Inscritos en total en la app: **{cmp['n_inscritos_total']}**."
    )
    if cmp.get("institucion_usada"):
        st.caption(f"Institución usada para agrupar: `{cmp['institucion_usada']}`")

    if cmp.get("pct_supera_companieros_institucion") is not None:
        st.success(
            "Por volumen de actividad registrada, superas aproximadamente a "
            f"**{cmp['pct_supera_companieros_institucion']}%** del resto de inscritos de tu misma institución "
            "(comparación con otros perfiles, no contigo)."
        )
    elif cmp.get("n_inscritos_misma_institucion", 0) <= 1:
        st.caption("No hay otros inscritos con la misma institución para comparar en esta muestra.")

    if cmp.get("pct_supera_companieros_global") is not None:
        st.info(
            "Frente al conjunto **global** de inscritos: superas aproximadamente a "
            f"**{cmp['pct_supera_companieros_global']}%** en actividad registrada."
        )

    if cmp.get("muestra_eventos_truncada"):
        st.caption(
            f"Nota: solo se analizaron hasta **{cmp.get('limite_muestra_eventos', '?')}** filas de eventos; "
            "si hay mucha historia, el conteo puede ser parcial."
        )


def _render_panel_tab_continuidad() -> None:
    por_tema = uso_stats.obtener_estadisticas_temas()
    lista = list(temario.LISTA_TEMAS)
    n_total = len(lista)
    con_practica = sum(1 for t in lista if int(por_tema.get(t, 0) or 0) > 0)
    sin_practica = [t for t in lista if int(por_tema.get(t, 0) or 0) == 0]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Temas con práctica registrada", f"{con_practica} / {n_total}")
    with c2:
        st.metric("Temas sin registros aún", len(sin_practica))
    with c3:
        pct = (con_practica / n_total) if n_total else 0.0
        st.metric("Cobertura aproximada del temario", f"{pct:.0%}")

    st.progress(min(max(pct, 0.0), 1.0))
    st.caption("Barra: cobertura aproximada del temario según datos agregados de práctica.")

    _render_debilidades_y_mapa()

    ordenados = sorted(
        [{"tema": t, "n": int(por_tema.get(t, 0) or 0)} for t in lista],
        key=lambda x: (x["n"], x["tema"]),
    )
    prioridad = [x["tema"] for x in ordenados if x["n"] == 0][:12]
    if not prioridad:
        prioridad = [x["tema"] for x in ordenados[:8]]

    st.markdown("##### Próximas prioridades (menos práctica registrada)")
    for i, t in enumerate(prioridad[:8], 1):
        st.caption(f"{i}. **{t}**")

    st.markdown("##### Cómo avanzar con cobertura total")
    st.markdown(
        """
        1. **A practicar:** elige en el multiselect los temas marcados arriba como prioridad (varios puntos del temario a la vez).

        2. **Vamos paso a paso** o **Dime y te digo:** plantea dudas o ejercicios concretos de esos temas.

        3. **Simulacro:** cuando domines un bloque, comprueba con un examen de prueba (primer o segundo parcial o temas personalizados).

        4. **Te lo reviso:** valida tus resoluciones escritas de ejercicios largos.

        5. Vuelve a **Seguimos** para ver cómo sube la cobertura del temario.
        """
    )

    st.markdown("##### Detalle por tema (registros agregados)")
    st.dataframe(
        ordenados,
        use_container_width=True,
        hide_index=True,
        height=min(420, 28 * n_total + 38),
    )

    st.caption(
        "Los conteos por tema dependen de la configuración (Supabase o archivo local) y son "
        "agregados; no sustituyen el criterio docente. Para cobertura **total**, repasa todos "
        "los puntos del temario al menos una vez combinando los modos de estudio."
    )


def _render_debilidades_y_mapa() -> None:
    """Mapa de calor + lista de temas críticos (Quiz incorrecto + Tutor abierto con sesión)."""
    if not auth_estudiantes.sesion_activa():
        return
    if not _supabase_configurado():
        st.caption(
            "Las debilidades personalizadas requieren Supabase y sesión iniciada; "
            "sin eso solo ves los conteos agregados de práctica."
        )
        return
    sid = st.session_state.get("auth_estudiante_id")
    if not sid:
        return

    eventos = uso_stats.obtener_eventos_aprendizaje_estudiante(str(sid))
    metricas = uso_stats.calcular_metricas_debilidad_por_tema(eventos)

    st.markdown("##### Tu perfil: temas a reforzar")
    st.caption(
        "Integramos **errores en Simulacro** (peso alto) y **consultas en Dime y te digo** "
        "con tema detectado (peso medio). Solo cuenta actividad con tu sesión iniciada."
    )

    if not metricas:
        st.info(
            "Cuando falles preguntas del **Simulacro** o preguntes en **Dime y te digo**, "
            "aquí aparecerán los temas donde conviene reforzar."
        )
        return

    orden_critico = sorted(metricas.keys(), key=lambda t: -metricas[t]["score"])

    st.markdown("##### Temas críticos (prioridad)")
    for i, t in enumerate(orden_critico[:12], 1):
        row = metricas[t]
        st.markdown(
            f"{i}. **{t}** — intensidad **{row['score']:.1f}** "
            f"· errores simulacro: **{row['errores_quiz']}** "
            f"· dudas en tutor: **{row['consultas_tutor']}**"
        )

    try:
        import plotly.graph_objects as go

        top = orden_critico[:24]
        etiquetas = [tx[:46] + ("…" if len(tx) > 46 else "") for tx in top]
        valores = [metricas[t]["score"] for t in top]
        zmax = max(valores) if valores else 1.0
        fig = go.Figure(
            data=go.Heatmap(
                z=[valores],
                x=etiquetas,
                y=["Tu perfil"],
                colorscale="YlOrRd",
                zmin=0,
                zmax=max(zmax, 0.01),
                colorbar=dict(title="Peso"),
            )
        )
        fig.update_layout(
            height=280,
            margin=dict(l=8, r=8, t=36, b=160),
            xaxis_tickangle=-48,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Mapa de calor: misma intensidad que la lista (fila única = tu perfil).")
    except Exception as exc:
        st.caption(f"(Gráfico no disponible: {exc})")

    try:
        import pandas as pd

        filas = []
        for t in temario.LISTA_TEMAS:
            info = metricas.get(t) or {
                "score": 0.0,
                "errores_quiz": 0,
                "consultas_tutor": 0,
            }
            filas.append(
                {
                    "Tema": t,
                    "Intensidad": float(info["score"]),
                    "Errores simulacro": int(info["errores_quiz"]),
                    "Dudas en tutor": int(info["consultas_tutor"]),
                }
            )
        df = pd.DataFrame(filas).sort_values("Intensidad", ascending=False)
        max_int = float(df["Intensidad"].max() or 1.0)
        st.markdown("##### Intensidad por todo el temario")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(520, 26 * len(df) + 40),
            column_config={
                "Intensidad": st.column_config.ProgressColumn(
                    "Mapa de calor (barra)",
                    min_value=0,
                    max_value=max(max_int, 0.01),
                    format="%.1f",
                ),
            },
        )
    except Exception as exc:
        st.caption(f"(Tabla no disponible: {exc})")


def _nombre_estudiante() -> str:
    if auth_estudiantes.sesion_activa():
        return (st.session_state.get("auth_estudiante_nombre") or "").strip()
    return (st.session_state.get("estudiante_nombre_seguimos") or "").strip()


def _codigo_referencia() -> str | None:
    if auth_estudiantes.sesion_activa():
        c = st.session_state.get("auth_estudiante_codigo")
        return c if c else None
    return st.session_state.get("estudiante_codigo_seguimos")


def _registrar_acceso_modo() -> None:
    if st.session_state.get("_seguimos_uso_registrado_sesion"):
        return
    nombre = _nombre_estudiante()
    uso_stats.registrar_uso(
        "Seguimos",
        detalle={
            "panel": "continuidad",
            "identificado": bool(nombre),
            "nombre_resumido": (nombre[:120] if nombre else None),
            "con_cuenta_supabase": auth_estudiantes.sesion_activa(),
        },
    )
    st.session_state["_seguimos_uso_registrado_sesion"] = True


def _supabase_configurado() -> bool:
    u, _ = uso_stats.supabase_url_y_clave()
    return bool(u)


def _ir_panel_seguimos() -> None:
    st.session_state.seguimos_paso = SEGUIMOS_PASO_PANEL


def _render_entrada_seguimos() -> None:
    if not _supabase_configurado():
        st.caption("No hay Supabase configurado: puedes usar solo un nombre para esta sesión en el panel.")
        with st.expander("Diagnóstico de Supabase (no muestra claves)", expanded=False):
            d = uso_stats.diagnostico_supabase()
            st.write(
                {
                    "ok": bool(d.get("ok")),
                    "fuente": d.get("fuente"),
                    "url_presente": bool(d.get("url_presente")),
                    "key_presente": bool(d.get("key_presente")),
                    "nombre_key_detectado": d.get("nombre_key"),
                    "url_host": d.get("url_host"),
                }
            )
            st.caption(
                "En Streamlit Cloud → Settings → Secrets debes definir `SUPABASE_URL` y "
                "`SUPABASE_SERVICE_ROLE_KEY` (service_role), guardar y reiniciar la app."
            )
        if st.button("Continuar al panel (solo esta sesión)", type="primary", use_container_width=True):
            _ir_panel_seguimos()
            st.rerun()
        st.info(
            "Con Supabase y una cuenta, aquí verías tu avance vinculado al temario. Configura las claves en secrets."
        )
        return

    if auth_estudiantes.sesion_activa():
        if st.button("Ir a mi panel", type="primary", use_container_width=True):
            _ir_panel_seguimos()
            st.rerun()
        st.caption("Tienes sesión activa; el resumen de continuidad está en el panel.")
        return

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Regístrate", type="primary", use_container_width=True, key="seguimos_btn_registrate"):
            st.session_state.seguimos_paso = SEGUIMOS_PASO_PORTAL
            st.session_state.seguimos_portal_tab = "registro"
            st.rerun()
    with c2:
        if st.button("Ya tengo cuenta", use_container_width=True, key="seguimos_btn_ya_cuenta"):
            st.session_state.seguimos_paso = SEGUIMOS_PASO_PORTAL
            st.session_state.seguimos_portal_tab = "login"
            st.rerun()


def _render_portal_seguimos() -> None:
    tab_ini = st.session_state.get("seguimos_portal_tab", "registro")
    if tab_ini not in ("registro", "login"):
        tab_ini = "registro"

    try:
        c_nav_1, c_nav_2, c_nav_3 = st.columns(3, gap="small")
    except TypeError:
        c_nav_1, c_nav_2, c_nav_3 = st.columns(3)
    with c_nav_1:
        if st.button(
            "← Paso anterior",
            key="seguimos_portal_volver",
            use_container_width=True,
            help="Vuelve a elegir Regístrate o Ya tengo cuenta",
        ):
            st.session_state.seguimos_paso = SEGUIMOS_PASO_ENTRADA
            st.rerun()
    with c_nav_2:
        if tab_ini == "registro":
            if st.button("Ya tengo cuenta", key="seguimos_portal_ir_login", use_container_width=True):
                st.session_state.seguimos_portal_tab = "login"
                st.rerun()
        else:
            if st.button("Regístrate", key="seguimos_portal_ir_registro", use_container_width=True):
                st.session_state.seguimos_portal_tab = "registro"
                st.rerun()
    with c_nav_3:
        if st.button(
            "Portada",
            key="seguimos_portal_portada",
            use_container_width=True,
            help="Salir de Seguimos y volver a la portada de la app",
        ):
            from modules import interfaz as _interfaz

            _interfaz._limpiar_estado_volver_inicio()
            st.rerun()

    if not _supabase_configurado():
        st.warning(
            "Sin Supabase configurado no se puede usar el portal. "
            "Usa **Portada** para salir o **Paso anterior** para volver."
        )
        return

    auth_estudiantes.render_portal_participante(
        tab_inicial=tab_ini,
        on_session_ok=_ir_panel_seguimos,
    )


def _render_panel_seguimos() -> None:
    if _supabase_configurado() and not auth_estudiantes.sesion_activa():
        st.warning(
            "Para usar el panel con base de datos debes **iniciar sesión** o completar el registro."
        )
        if st.button("Ir al portal de registro / inicio de sesión", key="seguimos_reabrir_portal"):
            st.session_state.seguimos_paso = SEGUIMOS_PASO_PORTAL
            st.session_state.seguimos_portal_tab = "login"
            st.rerun()
        return

    if not _nombre_estudiante():
        with st.form("form_registro_seguimos"):
            st.markdown("##### Identificación (solo esta sesión, sin base de datos)")
            st.caption("Si configuras Supabase y te registras, este paso no será necesario.")
            nombre = st.text_input(
                "Nombre o apodo",
                placeholder="Ej. Ana / Grupo 3",
                max_chars=120,
            )
            codigo = st.text_input(
                "Código o correo (opcional)",
                placeholder="Opcional",
                max_chars=160,
            )
            enviar = st.form_submit_button("Registrar y ver mi panel", type="primary")
            if enviar:
                nom = (nombre or "").strip()
                if not nom:
                    st.error("Indica al menos un nombre o apodo para continuar.")
                else:
                    st.session_state.estudiante_nombre_seguimos = nom
                    st.session_state.estudiante_codigo_seguimos = (codigo or "").strip() or None
                    st.session_state.pop("_seguimos_uso_registrado_sesion", None)
                    st.rerun()
        return

    _registrar_acceso_modo()

    nombre = _nombre_estudiante()
    codigo = _codigo_referencia()

    st.success(f"Hola, **{nombre}**. Aquí tienes tu resumen de continuidad.")

    if auth_estudiantes.sesion_activa():
        em = (st.session_state.get("auth_estudiante_email") or "").strip()
        inst = (st.session_state.get("auth_estudiante_institucion") or "").strip()
        fn = (st.session_state.get("auth_estudiante_fecha_nacimiento") or "").strip()
        c_em, c_inst, c_fn = st.columns(3)
        with c_em:
            st.caption("Correo")
            st.markdown(f"`{em}`" if em else "—")
        with c_inst:
            st.caption("Institución")
            st.markdown(f"**{inst}**" if inst else "—")
        with c_fn:
            st.caption("Fecha de nacimiento")
            st.markdown(f"`{fn}`" if fn else "—")

        car = (st.session_state.get("auth_estudiante_carrera") or "").strip()
        if car:
            st.caption(f"Carrera: **{car}**")
        sem = (st.session_state.get("auth_estudiante_semestre") or "").strip()
        if sem:
            st.caption(f"Semestre: **{sem}**")
        if codigo:
            st.caption(f"Referencia (opcional, cuenta antigua): `{codigo}`")
    elif codigo:
        st.caption(f"Referencia: `{codigo}`")

    _render_botones_acceso_rapido_modos()

    tab_cont, tab_rec = st.tabs(["Continuidad y temario", "Mi récord vs otros"])
    with tab_cont:
        _render_panel_tab_continuidad()
    with tab_rec:
        _render_tab_record_comparativa()


def render_vista_seguimos() -> None:
    paso = st.session_state.get("seguimos_paso", SEGUIMOS_PASO_ENTRADA)
    if paso == SEGUIMOS_PASO_PORTAL:
        _render_portal_seguimos()
    elif paso == SEGUIMOS_PASO_PANEL:
        _render_panel_seguimos()
    else:
        _render_entrada_seguimos()
