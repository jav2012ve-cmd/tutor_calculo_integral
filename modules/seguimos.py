"""
Panel «Seguimos»: continuidad para estudiantes identificados.

Flujo con Supabase: entrada → portal de registro / login → panel.
Sin Supabase: se puede ir al panel con identificación solo de sesión.
"""

from __future__ import annotations

import streamlit as st

from modules import auth_estudiantes, temario, uso_stats

MODO_ID = "0) Seguimos (continuidad)"

SEGUIMOS_PASO_ENTRADA = "entrada"
SEGUIMOS_PASO_PORTAL = "portal"
SEGUIMOS_PASO_PANEL = "panel"


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

    st.markdown("##### Cuenta de participante")
    st.success("**Paso 1:** crea tu cuenta o entra si ya estás registrado.")
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

    st.divider()
    st.info(
        "**Seguimos** resume tu avance según el temario y te orienta para lograr **cobertura amplia** "
        "del curso (práctica, consultas, simulacro, etc.)."
    )


def _render_portal_seguimos() -> None:
    if st.button("← Volver", key="seguimos_portal_volver"):
        st.session_state.seguimos_paso = SEGUIMOS_PASO_ENTRADA
        st.rerun()

    if not _supabase_configurado():
        st.warning("Sin Supabase configurado no se puede usar el portal. Pulsa **← Volver**.")
        return

    tab_ini = st.session_state.get("seguimos_portal_tab", "registro")
    if tab_ini not in ("registro", "login"):
        tab_ini = "registro"
    st.success(
        "Bienvenido al portal de estudiantes. Primero crea tu cuenta; "
        "si ya la tienes, inicia sesión en la sección inferior."
    )
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
        if st.session_state.get("auth_estudiante_email"):
            st.caption(f"Correo: `{st.session_state.auth_estudiante_email}`")
        inst = (st.session_state.get("auth_estudiante_institucion") or "").strip()
        if inst:
            st.caption(f"Institución: **{inst}**")
        fn = (st.session_state.get("auth_estudiante_fecha_nacimiento") or "").strip()
        if fn:
            st.caption(f"Fecha de nacimiento: `{fn}`")
        if codigo:
            st.caption(f"Referencia (opcional, cuenta antigua): `{codigo}`")
    elif codigo:
        st.caption(f"Referencia: `{codigo}`")

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


def render_vista_seguimos() -> None:
    paso = st.session_state.get("seguimos_paso", SEGUIMOS_PASO_ENTRADA)
    if paso == SEGUIMOS_PASO_PORTAL:
        _render_portal_seguimos()
    elif paso == SEGUIMOS_PASO_PANEL:
        _render_panel_seguimos()
    else:
        _render_entrada_seguimos()
