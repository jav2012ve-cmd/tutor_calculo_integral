import streamlit as st
from modules.temario import LISTA_TEMAS

def configurar_pagina():
    st.set_page_config(
        page_title="Matemáticas III - Economía UCAB",
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
             "d) Tutor: Preguntas Abiertas"],
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
            """)

        return st.session_state.get("modo_actual"), tema_seleccionado

def mostrar_bienvenida():
    st.title("Matemáticas III - Economía UCAB")
    
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 25px; border-radius: 10px; border-left: 5px solid #00aeef; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #0e1117;">🏛️ Bienvenidos al Tutor Inteligente de la Cátedra</h4>
        <p style="color: #31333f;">Este ecosistema está diseñado para fortalecer el dominio de <strong>Cálculo Integral</strong> y <strong>Ecuaciones Diferenciales</strong> en tu formación como economista. Dos pilares:</p>
        <ul style="margin-bottom: 10px; color: #31333f;">
            <li><strong>Cálculo Integral:</strong> Métodos de integración, aplicaciones (excedentes, áreas, volúmenes, probabilidad).</li>
            <li><strong>Ecuaciones Diferenciales:</strong> Primer orden, orden superior; modelos de crecimiento, enfriamiento de Newton, estabilidad y ciclos económicos.</li>
        </ul>
    </div>
    
    ### 🛠️ Mejoras recientes
    Hemos actualizado el tutor para que aproveches mejor el contenido y la evaluación:
    
    * **Temario y banco alineados** por tema; numeración unificada para filtrar bien por parcial.
    * **Informe en PDF** al terminar la autoevaluación: descarga tu calificación y las explicaciones de cada pregunta.
    * **Tutor de preguntas abiertas** con historial limitado para respuestas más estables; aviso cuando la conversación es larga.
    * **Mejor visualización de fórmulas** en preguntas y explicaciones (LaTeX corregido).
    * **Ayuda en el menú:** en el lateral puedes abrir **📖 Ayuda / Modos** para ver qué hace cada modo. Al cambiar de modo se reinicia el estado para evitar datos residuales.
    
    <hr style="margin-top: 20px; margin-bottom: 20px;">
    """, unsafe_allow_html=True)
    
    st.info("💡 **Consejo:** Para el segundo parcial, usa **Autoevaluación** → **Personalizado** y practica tema por tema.")
