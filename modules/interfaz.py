import streamlit as st
from modules.temario import LISTA_TEMAS
from modules import uso_stats

def inyectar_estilo_matematico():
    """
    CSS para mejorar renderizado KaTeX y evitar que el texto matemático se rompa.
    Se ejecuta una sola vez por sesión.
    """
    if st.session_state.get("estilo_matematico_inyectado"):
        return
    st.session_state["estilo_matematico_inyectado"] = True

    st.markdown(
        """
        <style>
        /* Ajustes generales para textos con LaTeX en Markdown */
        .stMarkdown p {
            line-height: 1.6;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        /* KaTeX */
        .katex {
            font-size: 1.1em;
            max-width: 100%;
            overflow-x: auto;
            white-space: normal;
        }

        /* Contenedor que Streamlit usa para st.latex */
        .stLatex, .stLatex > div {
            max-width: 100%;
            overflow-x: auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def configurar_pagina():
    st.set_page_config(
        page_title="Matemáticas III - Economías UCAB V3.0",
        page_icon="📈",
        layout="wide"
    )

def mostrar_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/f/f0/Logo_UCAB_H.png", width=200)
        st.markdown("### 🏛️ Escuela de Economía")
        
        seleccion_visual = st.radio(
            "1. Selecciona tu Modo de Estudio:",
            ["a) Entrenamiento (Temario)", 
             "b) Respuesta Guiada (Consultas)", 
             "c) Autoevaluación (Quiz)",
             "d) Tutor: Preguntas Abiertas",
             "e) Corrección de Manuscritos"],
            index=None,
            key="radio_seleccion"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Iniciar"):
                if seleccion_visual:
                    # Al cambiar de modo, limpiar estado de los otros modos para evitar datos residuales
                    if seleccion_visual != st.session_state.get("modo_actual"):
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
                    st.session_state.modo_actual = seleccion_visual
                st.rerun()
        with col2:
            if st.button("🔄 Reiniciar"):
                st.session_state.modo_actual = None
                st.session_state.messages = []
                st.rerun()
        
        st.divider()
        
        tema_seleccionado = None
        if st.session_state.get("modo_actual") == "a) Entrenamiento (Temario)":
            st.write("### 📘 Temario Detallado")
            if "tema_seleccionado" not in st.session_state:
                st.session_state.tema_seleccionado = LISTA_TEMAS[0]
            
            tema_seleccionado = st.selectbox("Selecciona el punto:", LISTA_TEMAS)
            st.session_state.tema_seleccionado = tema_seleccionado

        st.divider()
        with st.expander("📖 Ayuda / Modos"):
            st.markdown("""
            **a) Entrenamiento:** Serie de ejercicios paso a paso (estrategia → hito → resultado).  
            **b) Respuesta Guiada:** Subes foto o texto de un ejercicio y el tutor te guía.  
            **c) Autoevaluación:** Simulacro de parcial (Primer, Segundo o temas personalizados).  
            **d) Tutor abierto:** Chat sobre teoría y ejercicios de la cátedra.  
            **e) Corrección de Manuscritos:** Sube tu resolución escrita; la app identifica el enunciado, valora tu solución y sugiere ajustes.
            """)

        with st.expander("📊 Uso de la app"):
            stats = uso_stats.obtener_estadisticas()
            if any(stats.get(m, 0) > 0 for m in uso_stats.MODULOS):
                for mod in uso_stats.MODULOS:
                    n = stats.get(mod, 0)
                    st.caption(f"**{mod}:** {n} consultas")
                st.caption("_Anónimo, sin identificar usuarios._")
            else:
                st.caption("_Aún no hay registros de uso._")

        return st.session_state.get("modo_actual"), tema_seleccionado

def mostrar_bienvenida():
    """Muestra la presentación inicial solo cuando aún no se ha seleccionado un modo."""
    st.title("Matemáticas III - Economías UCAB V3.0")
    
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 25px; border-radius: 10px; border-left: 5px solid #00aeef; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #0066cc;">🏛️ Bienvenidos al Tutor Inteligente de la Cátedra</h4>
        <p style="color: #0066cc;">Este ecosistema está diseñado para fortalecer el dominio de <strong>Cálculo Integral</strong> y <strong>Ecuaciones Diferenciales</strong> en tu formación como economista.</p>
        <p style="color: #0066cc;"><strong>Modos de estudio:</strong></p>
        <ul style="margin-bottom: 10px; color: #0066cc;">
            <li><strong>a) Entrenamiento:</strong> Serie de ejercicios paso a paso (estrategia → hito → resultado).</li>
            <li><strong>b) Respuesta Guiada:</strong> Sube foto o texto de un ejercicio y el tutor te guía.</li>
            <li><strong>c) Autoevaluación:</strong> Simulacro de parcial (Primer, Segundo o temas personalizados).</li>
            <li><strong>d) Tutor Preguntas Abiertas:</strong> Chat sobre teoría y ejercicios de la cátedra.</li>
            <li><strong>e) Corrección de Manuscritos:</strong> Sube tu resolución escrita; la app identifica el enunciado, valora tu solución (correcto / parcial / incorrecto) y sugiere ajustes.</li>
        </ul>
        <p style="color: #0066cc;">Dos pilares del curso: <strong>Cálculo Integral</strong> (métodos de integración, excedentes, áreas, volúmenes) y <strong>Ecuaciones Diferenciales</strong> (primer orden, orden superior, modelos económicos).</p>
    </div>
    
    <p style="color: #0066cc;"><strong>🛠️ Recursos</strong></p>
    <ul style="color: #0066cc;">
        <li>Temario y banco alineados por tema; informe en PDF al terminar la autoevaluación.</li>
        <li>Fórmulas (LaTeX) en preguntas, opciones y explicaciones. Ayuda en 📖 Ayuda / Modos (lateral).</li>
    </ul>
    <hr style="margin-top: 20px; margin-bottom: 20px;">
    """, unsafe_allow_html=True)
    
    st.info("👆 **Elige un modo en el menú de la izquierda y pulsa *Iniciar* para comenzar.**")
